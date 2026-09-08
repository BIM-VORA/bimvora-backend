import asyncio
import uuid
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.bundle import Bundle
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.order import CreateOrderRequest, CreateOrderResponse, OrderStatus

router = APIRouter()

stripe.api_key = settings.stripe_secret_key


def _generate_order_number() -> str:
    year = datetime.now(timezone.utc).year
    random_part = uuid.uuid4().hex[:6].upper()
    return f"BV-{year}-{random_part}"


@router.post("/", response_model=CreateOrderResponse, status_code=201)
async def create_order(
    body: CreateOrderRequest,
    request: Request,
    x_internal_secret: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    # Validate internal secret (call must come from Next.js route handler)
    if x_internal_secret != settings.internal_secret:
        raise HTTPException(status_code=403, detail="Forbidden")

    if not body.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Resolve items and compute totals
    subtotal_cents = 0
    order_items_data: list[dict] = []

    for item in body.items:
        if item.product_id:
            result = await db.execute(
                select(Product).where(Product.id == item.product_id, Product.status == "active")
            )
            product = result.scalar_one_or_none()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
            unit_price = product.price_cents
            order_items_data.append({
                "product_id": product.id,
                "bundle_id": None,
                "item_type": "product",
                "name": product.name,
                "sku": product.sku,
                "quantity": item.quantity,
                "unit_price_cents": unit_price,
                "total_price_cents": unit_price * item.quantity,
            })
            subtotal_cents += unit_price * item.quantity

        elif item.bundle_id:
            result = await db.execute(
                select(Bundle).where(Bundle.id == item.bundle_id, Bundle.is_active == True)
            )
            bundle = result.scalar_one_or_none()
            if not bundle:
                raise HTTPException(status_code=404, detail=f"Bundle {item.bundle_id} not found")
            unit_price = bundle.price_cents
            order_items_data.append({
                "product_id": None,
                "bundle_id": bundle.id,
                "item_type": "bundle",
                "name": bundle.name,
                "sku": None,
                "quantity": item.quantity,
                "unit_price_cents": unit_price,
                "total_price_cents": unit_price * item.quantity,
            })
            subtotal_cents += unit_price * item.quantity

    # Apply coupon if present
    discount_cents = 0
    if body.coupon_code:
        from app.models.coupon import Coupon
        coupon_result = await db.execute(
            select(Coupon).where(
                Coupon.code == body.coupon_code.upper(),
                Coupon.is_active == True,
            )
        )
        coupon = coupon_result.scalar_one_or_none()
        if coupon:
            if coupon.discount_type == "percent":
                discount_cents = int(subtotal_cents * coupon.discount_value / 100)
            else:
                discount_cents = min(coupon.discount_value, subtotal_cents)
            coupon.used_count += 1

    total_cents = subtotal_cents - discount_cents

    # Get client IP
    ip_address = body.ip_address or (request.client.host if request.client else None)

    # Create Stripe PaymentIntent
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=total_cents,
            currency=body.currency.lower(),
            metadata={
                "order_email": body.customer_email,
                "order_number": "pending",  # will update after DB insert
            },
            automatic_payment_methods={"enabled": True},
        )
    except stripe.StripeError as e:
        raise HTTPException(status_code=402, detail=str(e))

    # Create order in DB
    order_number = _generate_order_number()
    order = Order(
        order_number=order_number,
        customer_email=body.customer_email,
        customer_first_name=body.customer_first_name,
        customer_last_name=body.customer_last_name,
        customer_company=body.customer_company,
        country=body.country,
        status="pending",
        subtotal_cents=subtotal_cents,
        discount_cents=discount_cents,
        total_cents=total_cents,
        currency=body.currency,
        coupon_code=body.coupon_code,
        stripe_payment_intent_id=payment_intent.id,
        event_id=body.event_id,
        fbc=body.fbc,
        fbp=body.fbp,
        ttp=body.ttp,
        ga_client_id=body.ga_client_id,
        ip_address=ip_address,
        user_agent=body.user_agent,
    )
    db.add(order)
    await db.flush()  # Get the order.id without committing

    for item_data in order_items_data:
        db.add(OrderItem(order_id=order.id, **item_data))

    await db.commit()
    await db.refresh(order)

    # Update Stripe PI metadata with real order_number
    stripe.PaymentIntent.modify(
        payment_intent.id,
        metadata={"order_id": str(order.id), "order_number": order_number},
    )

    return CreateOrderResponse(
        order_id=order.id,
        order_number=order.order_number,
        stripe_client_secret=payment_intent.client_secret,
        total_cents=order.total_cents,
        currency=order.currency,
    )


@router.get("/{order_id}/status", response_model=OrderStatus)
async def get_order_status(order_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderStatus.model_validate(order)
