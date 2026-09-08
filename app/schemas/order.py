import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class OrderItemIn(BaseModel):
    product_id: uuid.UUID | None = None
    bundle_id: uuid.UUID | None = None
    quantity: int = 1


class CreateOrderRequest(BaseModel):
    customer_email: EmailStr
    customer_first_name: str
    customer_last_name: str | None = None
    customer_company: str | None = None
    country: str  # ISO 2-letter

    currency: str = "USD"
    items: list[OrderItemIn]
    coupon_code: str | None = None

    # Tracking cookies (forwarded from browser)
    event_id: str | None = None
    fbc: str | None = None
    fbp: str | None = None
    ttp: str | None = None
    ttclid: str | None = None
    ga_client_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    event_source_url: str | None = None


class CreateOrderResponse(BaseModel):
    order_id: uuid.UUID
    order_number: str
    stripe_client_secret: str
    total_cents: int
    currency: str


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    item_type: str
    name: str
    sku: str | None
    quantity: int
    unit_price_cents: int
    total_price_cents: int


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    order_number: str
    customer_email: str
    customer_first_name: str
    status: str
    subtotal_cents: int
    discount_cents: int
    total_cents: int
    currency: str
    paid_at: datetime | None
    downloads_enabled: bool
    items: list[OrderItemRead]
    created_at: datetime


class OrderStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    order_id: uuid.UUID
    order_number: str
    status: str
    downloads_enabled: bool
