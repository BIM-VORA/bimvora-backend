import asyncio

from fastapi import APIRouter, Request

from app.schemas.tracking import TrackingEventRequest

router = APIRouter()


@router.post("/event", status_code=202)
async def track_event(body: TrackingEventRequest, request: Request):
    """
    Receives browser-side events and fires server-side CAPI calls.
    Always returns 202 immediately — tracking errors never block UX.
    """
    ip_address = request.client.host if request.client else body.user_agent

    asyncio.create_task(_fire_all_capi(body, ip_address))
    return {"status": "accepted"}


async def _fire_all_capi(body: TrackingEventRequest, ip_address: str | None) -> None:
    from app.services.tracking import send_meta_capi_event, send_tiktok_server_event
    from app.config import settings

    custom_data = {
        "content_ids": body.content_ids,
        "value": body.value,
        "currency": body.currency,
        "num_items": body.num_items,
    }

    await asyncio.gather(
        send_meta_capi_event(
            event_name=body.event_name,
            event_id=body.event_id,
            event_source_url=body.event_source_url,
            user_email=body.user_email,
            ip_address=ip_address,
            user_agent=body.user_agent,
            fbc=body.fbc,
            fbp=body.fbp,
            custom_data=custom_data,
            pixel_id=settings.meta_pixel_id,
            access_token=settings.meta_access_token,
        ) if settings.meta_pixel_id else asyncio.sleep(0),

        send_tiktok_server_event(
            event_name=body.event_name,
            event_id=body.event_id,
            event_url=body.event_source_url,
            user_email=body.user_email,
            ip_address=ip_address,
            user_agent=body.user_agent,
            ttp_cookie=body.ttp,
            ttclid=body.ttclid,
            properties=custom_data,
            pixel_id=settings.tiktok_pixel_id,
            access_token=settings.tiktok_access_token,
        ) if settings.tiktok_pixel_id else asyncio.sleep(0),

        return_exceptions=True,
    )
