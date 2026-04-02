"""Rate limiting via slowapi, keyed by authenticated user with IP fallback.

Uses Redis tstorage so limits hold across multiple instances; falls back to
in-memory counters if Redis is unavailable.
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import decode_token
from app.config import settings


def user_or_ip(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        user_id = decode_token(auth.removeprefix("Bearer "))
        if user_id:
            return f"user:{user_id}"
    return get_remote_address(request)


limiter = Limiter(
    key_func=user_or_ip,
    storage_uri=settings.REDIS_URL,
    in_memory_fallback_enabled=True,
    enabled=settings.RATE_LIMIT_ENABLED,
)
