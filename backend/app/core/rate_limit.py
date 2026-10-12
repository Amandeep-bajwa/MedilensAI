from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings

def get_client_ip(request: Request) -> str:
    """
    Resolves client IP supporting reverse proxies (X-Forwarded-For, X-Real-IP)
    with fallback to Starlette remote address.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return get_remote_address(request)

# Initialize limiter using client IP resolution
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    enabled=settings.RATE_LIMIT_ENABLED
)

def rate_limit_custom_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Standardized HTTP 429 handler adhering to MediLens error schema (SRS Section 16).
    """
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "code": "RATE_LIMIT_EXCEEDED",
            "message": f"Rate limit exceeded: {exc.detail}. Please wait before making further requests."
        }
    )
