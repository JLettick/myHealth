"""
API v1 router that aggregates all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, users, whoop

# Create main API router
api_router = APIRouter()

# Include sub-routers with prefixes and tags
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
)

api_router.include_router(
    whoop.router,
    prefix="/whoop",
    tags=["Whoop"],
)
