"""
Security headers middleware.

Adds security-related HTTP headers to all responses to mitigate
common web vulnerabilities (clickjacking, MIME sniffing, etc.).
"""

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import Settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that adds security headers to every response."""

    def __init__(self, app, is_production: bool = False):
        super().__init__(app)
        self.is_production = is_production

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=()"

        if self.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


def setup_security_headers(app: FastAPI, settings: Settings) -> None:
    """
    Configure security headers middleware for the FastAPI application.

    Args:
        app: The FastAPI application instance
        settings: Application settings
    """
    app.add_middleware(SecurityHeadersMiddleware, is_production=settings.is_production)
    logger.info("Security headers middleware configured successfully")
