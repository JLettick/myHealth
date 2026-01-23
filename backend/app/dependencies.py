"""
FastAPI dependency injection functions.

Provides reusable dependencies for authentication, database access,
and other common operations.
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.exceptions import AuthenticationError
from app.core.logging_config import get_logger
from app.schemas.auth import UserResponse
from app.services.auth_service import AuthService, get_auth_service

logger = get_logger(__name__)


async def get_token_from_header(
    authorization: Optional[str] = Header(None, description="Bearer token"),
) -> Optional[str]:
    """
    Extract JWT token from Authorization header.

    Args:
        authorization: The Authorization header value

    Returns:
        The extracted token or None if not present
    """
    if not authorization:
        return None

    parts = authorization.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Get the current authenticated user.

    This dependency validates the JWT token and returns the user data.
    Use this for protected endpoints that require authentication.

    Args:
        request: The FastAPI request object
        token: JWT token extracted from Authorization header
        auth_service: Auth service instance

    Returns:
        UserResponse with current user data

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not token:
        logger.warning(
            "Authentication required but no token provided",
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await auth_service.get_current_user(token)

        # Store user in request state for logging
        request.state.user_id = user.id

        logger.debug(
            f"Authenticated user: {user.id}",
            extra={
                "user_id": user.id,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

        return user

    except AuthenticationError as e:
        logger.warning(
            f"Authentication failed: {e.message}",
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    request: Request,
    token: Optional[str] = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
) -> Optional[UserResponse]:
    """
    Get the current user if authenticated, or None if not.

    This dependency is similar to get_current_user but doesn't raise
    an exception if the user is not authenticated. Use this for
    endpoints that have different behavior for authenticated vs
    anonymous users.

    Args:
        request: The FastAPI request object
        token: JWT token extracted from Authorization header
        auth_service: Auth service instance

    Returns:
        UserResponse with current user data, or None if not authenticated
    """
    if not token:
        return None

    try:
        user = await auth_service.get_current_user(token)
        request.state.user_id = user.id
        return user

    except AuthenticationError:
        return None


async def get_access_token(
    token: Optional[str] = Depends(get_token_from_header),
) -> str:
    """
    Get the raw access token from the Authorization header.

    Use this when you need the actual token string (e.g., for logout).

    Args:
        token: JWT token extracted from Authorization header

    Returns:
        The access token string

    Raises:
        HTTPException: If token is missing
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token
