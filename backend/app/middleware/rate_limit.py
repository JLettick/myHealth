"""
Rate limiting middleware using slowapi.

Configures per-endpoint rate limits keyed by client IP address.
Supports X-Forwarded-For for reverse proxy deployments.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import Settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _get_client_ip(request: Request) -> str:
    """
    Extract client IP from request, respecting X-Forwarded-For.

    Args:
        request: The incoming FastAPI request

    Returns:
        Client IP address string
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # First IP in the chain is the original client
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(
    key_func=_get_client_ip,
    default_limits=[],
    storage_uri="memory://",
)


def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Handle 429 rate limit exceeded errors.

    Returns a JSON response matching the app's standard error format.
    """
    request_id = getattr(request.state, "request_id", None)
    retry_after = exc.detail.split(" ")[-1] if exc.detail else None

    logger.warning(
        f"Rate limit exceeded: {exc.detail}",
        extra={
            "request_id": request_id,
            "client_ip": _get_client_ip(request),
            "path": request.url.path,
        },
    )

    response = JSONResponse(
        status_code=429,
        content={
            "error": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests. Please try again later.",
            "details": {"limit": str(exc.detail)},
            "request_id": request_id,
        },
    )

    if retry_after:
        response.headers["Retry-After"] = retry_after

    return response


def setup_rate_limiting(app: FastAPI, settings: Settings) -> None:
    """
    Configure rate limiting middleware for the FastAPI application.

    No-op if rate_limit_enabled is False in settings.

    Args:
        app: The FastAPI application instance
        settings: Application settings
    """
    if not settings.rate_limit_enabled:
        logger.info("Rate limiting is disabled")
        return

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    logger.info("Rate limiting middleware configured successfully")
