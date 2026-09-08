"""Supabase Storage — generate signed download URLs."""
import logging

from app.config import settings

logger = logging.getLogger("bimvora.storage")


async def generate_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """
    Generate a temporary signed URL for a private Supabase Storage file.
    The URL expires in `expires_in` seconds (default 1 hour).
    """
    if not settings.supabase_url or not settings.supabase_service_role_key:
        logger.warning("Supabase credentials not configured — returning placeholder URL")
        return f"https://placeholder.bimvora.com/{storage_path}"

    from supabase import create_client, Client
    client: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    response = client.storage.from_(settings.supabase_storage_bucket).create_signed_url(
        path=storage_path,
        expires_in=expires_in,
    )

    return response["signedURL"]
