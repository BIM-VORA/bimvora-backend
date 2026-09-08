"""Sync order data to Google Sheets via Apps Script webhook."""
import logging

import httpx

from app.config import settings

logger = logging.getLogger("bimvora.sheets")


async def sync_order_to_sheets(order) -> None:
    if not settings.sheets_webhook_url:
        return

    payload = {
        "secret": settings.sheets_secret,
        "order_id": str(order.id),
        "order_number": order.order_number,
        "date": order.created_at.isoformat(),
        "status": order.status,
        "customer_name": f"{order.customer_first_name} {order.customer_last_name or ''}".strip(),
        "email": order.customer_email,
        "company": order.customer_company or "",
        "country": order.country,
        "items": ", ".join(item.name for item in order.items),
        "subtotal_usd": order.subtotal_cents / 100,
        "discount_usd": order.discount_cents / 100,
        "total_usd": order.total_cents / 100,
        "currency": order.currency,
        "stripe_payment_id": order.stripe_payment_intent_id or "",
        "coupon_code": order.coupon_code or "",
        "items_json": str([{"name": i.name, "qty": i.quantity, "price": i.unit_price_cents / 100} for i in order.items]),
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(settings.sheets_webhook_url, json=payload)
            if resp.status_code == 200:
                logger.info(f"Order {order.order_number} synced to Sheets")
            else:
                logger.warning(f"Sheets sync returned {resp.status_code}")
    except Exception as e:
        logger.warning(f"Sheets sync error: {e}")
