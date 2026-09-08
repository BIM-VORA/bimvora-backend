from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.newsletter import NewsletterSubscriber

router = APIRouter()


class SubscribeRequest(BaseModel):
    email: EmailStr
    source: str = "footer"


@router.post("/subscribe", status_code=201)
async def subscribe(body: SubscribeRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(NewsletterSubscriber).where(NewsletterSubscriber.email == body.email)
    )
    if existing.scalar_one_or_none():
        return {"status": "already_subscribed"}

    subscriber = NewsletterSubscriber(email=body.email, source=body.source)
    db.add(subscriber)
    await db.commit()
    return {"status": "subscribed"}
