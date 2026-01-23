"""
CORS middleware configuration.

Configures Cross-Origin Resource Sharing to allow the frontend
to communicate with the backend API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def setup_cors(app: FastAPI, settings: Settings) -> None:
    """
    Configure CORS middleware for the FastAPI application.

    Args:
        app: The FastAPI application instance
        settings: Application settings containing CORS configuration
    """
    logger.info(f"Setting up CORS with origins: {settings.cors_origins}")

    app.add_middleware(
        CORSMiddleware,
        # Specific origins - never use ["*"] in production
        allow_origins=settings.cors_origins,
        # Allow credentials (cookies, authorization headers)
        allow_credentials=True,
        # Allowed HTTP methods
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        # Allowed headers
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Request-ID",
            "Accept",
            "Origin",
            "X-Requested-With",
        ],
        # Headers exposed to the browser
        expose_headers=[
            "X-Request-ID",
            "Content-Length",
        ],
        # Cache preflight requests for 10 minutes
        max_age=600,
    )

    logger.info("CORS middleware configured successfully")
