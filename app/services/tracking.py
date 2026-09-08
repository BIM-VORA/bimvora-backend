"""
Server-side tracking — Meta CAPI, TikTok Events API, GA4 Measurement Protocol.
All functions are fire-and-forget; errors are logged but never raised.
"""
import asyncio
import logging
import time
from typing import Any

import httpx

from app.config import settings
from app.utils.hashing import hash_pii, hash_phone

logger = logging.getLogger("bimvora.tracking")

META_CAPI_URL = "https://graph.facebook.com/v21.0/{pixel_id}/events"
TIKTOK_EVENTS_URL = "https://business-api.tiktok.com/open_api/v1.3/event/track/"
GA4_MP_URL = "https://www.google-analytics.com/mp/collect"


async def send_meta_capi_event(
    event_name: str,
    event_id: str,
    event_source_url: str,
    user_email: str | None,
    ip_address: str | None,
    user_agent: str | None,
    fbc: str | None,
    fbp: str | None,
    custom_data: dict,
    pixel_id: str,
    access_token: str,
    user_phone: str | None = None,
    user_first_name: str | None = None,
    user_last_name: str | None = None,
    user_country: str | None = None,
) -> None:
    if not pixel_id or not access_token:
        return

    user_data: dict[str, Any] = {
        "em": hash_pii(user_email),
        "ph": hash_phone(user_phone),
        "fn": hash_pii(user_first_name),
        "ln": hash_pii(user_last_name),
        "country": hash_pii(user_country),
        "client_ip_address": ip_address,
        "client_user_agent": user_agent,
        "fbc": fbc,
        "fbp": fbp,
    }
    # Remove None values
    user_data = {k: v for k, v in user_data.items() if v is not None}

    payload = {
        "data": [{
            "event_name": event_name,
            "event_time": int(time.time()),
            "event_id": event_id,
            "event_source_url": event_source_url,
            "action_source": "website",
            "user_data": user_data,
            "custom_data": {k: v for k, v in custom_data.items() if v is not None},
        }],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                META_CAPI_URL.format(pixel_id=pixel_id),
                json=payload,
                params={"access_token": access_token},
            )
            if resp.status_code != 200:
                logger.warning(f"Meta CAPI {event_name} returned {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.warning(f"Meta CAPI error: {e}")


async def send_tiktok_server_event(
    event_name: str,
    event_id: str,
    event_url: str,
    user_email: str | None,
    ip_address: str | None,
    user_agent: str | None,
    ttp_cookie: str | None,
    ttclid: str | None,
    properties: dict,
    pixel_id: str,
    access_token: str,
) -> None:
    if not pixel_id or not access_token:
        return

    user_data: dict[str, Any] = {
        "email": hash_pii(user_email),
        "ip": ip_address,
        "user_agent": user_agent,
        "ttp": ttp_cookie,
        "ttclid": ttclid,
    }
    user_data = {k: v for k, v in user_data.items() if v is not None}

    payload = {
        "event_source": "web",
        "event_source_id": pixel_id,
        "data": [{
            "event": event_name,
            "event_time": int(time.time()),
            "event_id": event_id,
            "page": {"url": event_url},
            "user": user_data,
            "properties": {
                "content_id": properties.get("content_ids", []),
                "content_type": "product",
                "value": properties.get("value"),
                "currency": properties.get("currency", "USD"),
                "quantity": properties.get("num_items", 1),
            },
        }],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                TIKTOK_EVENTS_URL,
                json=payload,
                headers={"Access-Token": access_token},
            )
            if resp.status_code != 200:
                logger.warning(f"TikTok Events API {event_name} returned {resp.status_code}")
    except Exception as e:
        logger.warning(f"TikTok Events API error: {e}")


async def send_ga4_purchase(
    order_id: str,
    total_usd: float,
    items: list[dict],
    ga_client_id: str | None,
    currency: str = "USD",
) -> None:
    if not settings.ga4_measurement_id or not settings.ga4_api_secret:
        return
    if not ga_client_id:
        ga_client_id = "server.0000000000"  # Fallback for server-side events

    payload = {
        "client_id": ga_client_id,
        "events": [{
            "name": "purchase",
            "params": {
                "transaction_id": order_id,
                "value": total_usd,
                "currency": currency,
                "items": [
                    {
                        "item_id": str(item.get("product_id", "")),
                        "item_name": item.get("name", ""),
                        "price": item.get("unit_price_cents", 0) / 100,
                        "quantity": item.get("quantity", 1),
                    }
                    for item in items
                ],
            },
        }],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                GA4_MP_URL,
                json=payload,
                params={
                    "measurement_id": settings.ga4_measurement_id,
                    "api_secret": settings.ga4_api_secret,
                },
            )
    except Exception as e:
        logger.warning(f"GA4 Measurement Protocol error: {e}")


async def fire_purchase_events(order) -> None:
    """Fire all server-side Purchase events after order fulfilled."""
    total_usd = order.total_cents / 100
    content_ids = [str(item.product_id) for item in order.items if item.product_id]

    await asyncio.gather(
        send_meta_capi_event(
            event_name="Purchase",
            event_id=order.event_id or f"order-{order.id}",
            event_source_url=f"{settings.frontend_url}/checkout/success",
            user_email=order.customer_email,
            user_first_name=order.customer_first_name,
            user_last_name=order.customer_last_name,
            user_country=order.country,
            ip_address=order.ip_address,
            user_agent=order.user_agent,
            fbc=order.fbc,
            fbp=order.fbp,
            custom_data={
                "content_ids": content_ids,
                "content_type": "product",
                "value": total_usd,
                "currency": order.currency,
                "num_items": len(order.items),
                "order_id": str(order.id),
            },
            pixel_id=settings.meta_pixel_id,
            access_token=settings.meta_access_token,
        ) if settings.meta_pixel_id else asyncio.sleep(0),

        send_tiktok_server_event(
            event_name="PlaceAnOrder",
            event_id=order.event_id or f"order-{order.id}",
            event_url=f"{settings.frontend_url}/checkout/success",
            user_email=order.customer_email,
            ip_address=order.ip_address,
            user_agent=order.user_agent,
            ttp_cookie=order.ttp,
            ttclid=None,
            properties={
                "content_ids": content_ids,
                "value": total_usd,
                "currency": order.currency,
                "num_items": len(order.items),
            },
            pixel_id=settings.tiktok_pixel_id,
            access_token=settings.tiktok_access_token,
        ) if settings.tiktok_pixel_id else asyncio.sleep(0),

        send_ga4_purchase(
            order_id=str(order.id),
            total_usd=total_usd,
            items=[{"product_id": i.product_id, "name": i.name, "unit_price_cents": i.unit_price_cents, "quantity": i.quantity} for i in order.items],
            ga_client_id=order.ga_client_id,
            currency=order.currency,
        ),

        return_exceptions=True,
    )
