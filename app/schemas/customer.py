import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class CustomerRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str | None = None
    company: str | None = None


class CustomerLogin(BaseModel):
    email: EmailStr
    password: str


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str | None
    company: str | None
    customer_type: str
    country: str | None
    order_count: int
    total_spent_cents: int
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    customer: CustomerRead


class RefreshRequest(BaseModel):
    refresh_token: str
