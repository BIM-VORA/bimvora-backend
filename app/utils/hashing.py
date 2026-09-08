"""PII hashing for server-side tracking (Meta CAPI, TikTok Events API)."""
import hashlib


def hash_pii(value: str | None) -> str | None:
    """Normalise (trim + lowercase) and SHA-256 hash a PII string."""
    if not value:
        return None
    normalised = value.strip().lower()
    return hashlib.sha256(normalised.encode()).hexdigest()


def hash_phone(phone: str | None) -> str | None:
    """Strip non-digits, remove leading zeros, then SHA-256 hash."""
    if not phone:
        return None
    digits = "".join(c for c in phone if c.isdigit()).lstrip("0")
    if not digits:
        return None
    return hashlib.sha256(digits.encode()).hexdigest()
