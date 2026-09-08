"""
Stripe webhook handler.
Fulfills orders after payment_intent.succeeded.
"""
import asyncio
import secrets
from datetime import datetime, timedelta, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db, SessionLocal
from app.models.order import Order, OrderItem
from app.models.product import ProductFile
from app.models.download import DownloadToken

router = APIRouter()

stripe.api_key = settings.stripe_secret_key


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Receives and processes Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "payment_intent.succeeded":
        pi = event["data"]["object"]
        order_id = pi.get("metadata", {}).get("order_id")
        if order_id:
            # Run fulfillment in background to return 200 quickly to Stripe
            asyncio.create_task(_fulfill_order(order_id, pi["id"]))

    elif event["type"] == "payment_intent.payment_failed":
        pi = event["data"]["object"]
        order_id = pi.get("metadata", {}).get("order_id")
        if order_id:
            asyncio.create_task(_cancel_order(order_id))

    return {"status": "received"}


async def _fulfill_order(order_id: str, stripe_pi_id: str) -> None:
    """Run in background — fulfills order after payment confirmed."""
    async with SessionLocal() as db:
        try:
            result = await db.execute(
                select(Order)
                .where(Order.id == order_id)
                .options(selectinload(Order.items))
            )
            order = result.scalar_one_or_none()
            if not order or order.status == "paid":
                return  # Already fulfilled or not found

            order.status = "paid"
            order.stripe_payment_intent_id = stripe_pi_id
            order.paid_at = datetime.now(timezone.utc)
            order.downloads_enabled = True

            # Generate download tokens for each order item
            download_tokens: list[dict] = []
            for item in order.items:
                if item.product_id:
                    files_result = await db.execute(
                        select(ProductFile).where(ProductFile.product_id == item.product_id)
                    )
                    files = files_result.scalars().all()
                    for f in files:
                        token = DownloadToken(
                            order_item_id=item.id,
                            product_file_id=f.id,
                            customer_id=order.customer_id,
                            token=secrets.token_urlsafe(32),
                            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                        )
                        db.add(token)
                        download_tokens.append({
                            "product_name": item.name,
                            "file_name": f.file_name,
                            "file_size_mb": f"{(f.file_size or 0) / 1_048_576:.1f}",
                            "token": token.token,
                        })

            await db.commit()

            # Fire post-fulfillment tasks concurrently
            await asyncio.gather(
                _send_confirmation_email(order, download_tokens),
                _fire_purchase_tracking(order),
                _sync_to_sheets(order),
                return_exceptions=True,
            )

        except Exception as e:
            await db.rollback()
            import logging
            logging.getLogger("bimvora").error(f"Order fulfillment failed: {e}", exc_info=True)


async def _cancel_order(order_id: str) -> None:
    async with SessionLocal() as db:
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if order and order.status == "pending":
            order.status = "cancelled"
            await db.commit()


async def _send_confirmation_email(order: Order, download_tokens: list[dict]) -> None:
    from app.services.email import send_order_confirmation_email
    try:
        await send_order_confirmation_email(order, download_tokens)
    except Exception as e:
        import logging
        logging.getLogger("bimvora").warning(f"Email failed for order {order.id}: {e}")


async def _fire_purchase_tracking(order: Order) -> None:
    from app.services.tracking import fire_purchase_events
    try:
        await fire_purchase_events(order)
    except Exception as e:
        import logging
        logging.getLogger("bimvora").warning(f"Tracking failed for order {order.id}: {e}")


async def _sync_to_sheets(order: Order) -> None:
    from app.services.sheets import sync_order_to_sheets
    try:
        await sync_order_to_sheets(order)
    except Exception as e:
        import logging
        logging.getLogger("bimvora").warning(f"Sheets sync failed for order {order.id}: {e}")
