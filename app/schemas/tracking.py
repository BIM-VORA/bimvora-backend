from pydantic import BaseModel


class TrackingEventRequest(BaseModel):
    event_name: str          # ViewContent | AddToCart | InitiateCheckout | Lead
    event_id: str            # Shared with browser pixel for dedup
    event_source_url: str
    user_agent: str | None = None
    user_email: str | None = None
    fbc: str | None = None   # _fbc cookie
    fbp: str | None = None   # _fbp cookie
    ttp: str | None = None   # _ttp cookie (TikTok)
    ttclid: str | None = None
    ga_client_id: str | None = None
    content_ids: list[str] = []
    value: float | None = None
    currency: str = "USD"
    num_items: int = 1
