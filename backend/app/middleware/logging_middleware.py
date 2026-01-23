"""
Request logging middleware.

Provides comprehensive logging for all incoming requests and responses,
including timing information and request IDs for debugging.
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and responses.

    Features:
    - Generates unique request ID for each request
    - Logs request method, path, and client IP
    - Logs response status code and duration
    - Adds request ID to response headers for debugging
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Process the request and log relevant information.

        Args:
            request: The incoming request
            call_next: The next middleware/route handler

        Returns:
            The response from the route handler
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Get client IP (handle proxy headers)
        client_ip = request.headers.get(
            "X-Forwarded-For",
            request.client.host if request.client else "unknown",
        )

        # Skip logging for health check endpoints to reduce noise
        is_health_check = request.url.path in ["/health", "/api/v1/health"]

        if not is_health_check:
            logger.info(
                f"Request started: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": client_ip,
                    "user_agent": request.headers.get("User-Agent", "unknown"),
                },
            )

        # Process request and measure duration
        start_time = time.time()

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            if not is_health_check:
                # Log based on status code
                log_level = "info"
                if response.status_code >= 400:
                    log_level = "warning"
                if response.status_code >= 500:
                    log_level = "error"

                log_func = getattr(logger, log_level)
                log_func(
                    f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                    extra={
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "duration_ms": round(duration_ms, 2),
                        "method": request.method,
                        "path": request.url.path,
                    },
                )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            raise


def setup_logging_middleware(app) -> None:
    """
    Add logging middleware to the FastAPI application.

    Args:
        app: The FastAPI application instance
    """
    app.add_middleware(RequestLoggingMiddleware)
    logger.info("Request logging middleware configured")
