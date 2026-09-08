from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.download import DownloadToken

router = APIRouter()


class DownloadResponse(BaseModel):
    signed_url: str
    file_name: str
    expires_in_seconds: int = 3600


@router.get("/{token}", response_model=DownloadResponse)
async def resolve_download(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DownloadToken)
        .where(DownloadToken.token == token)
        .options(selectinload(DownloadToken.product_file))
    )
    dl_token = result.scalar_one_or_none()

    if not dl_token:
        raise HTTPException(status_code=404, detail="Download link not found")

    if dl_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Download link has expired")

    if dl_token.download_count >= dl_token.max_downloads:
        raise HTTPException(status_code=410, detail="Download limit reached. Contact support.")

    # Generate Supabase Storage signed URL
    from app.services.storage import generate_signed_url
    signed_url = await generate_signed_url(dl_token.product_file.storage_path)

    # Increment download count
    dl_token.download_count += 1
    await db.commit()

    return DownloadResponse(
        signed_url=signed_url,
        file_name=dl_token.product_file.file_name,
    )
