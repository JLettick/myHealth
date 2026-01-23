"""
Health check endpoint for monitoring and load balancer health checks.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "",
    summary="Health Check",
    description="Check if the API is running and healthy",
    response_description="Health status",
)
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns basic health information about the API.
    Used by load balancers and monitoring systems.

    Returns:
        Dictionary with health status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "myhealth-api",
        "version": "1.0.0",
    }
