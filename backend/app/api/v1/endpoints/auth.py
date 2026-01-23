"""
Authentication endpoints for user signup, login, logout, and token refresh.
"""

from fastapi import APIRouter, Depends, Request

from app.core.logging_config import get_logger
from app.dependencies import get_access_token, get_current_user
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    SignupRequest,
    UserResponse,
)
from app.services.auth_service import AuthService, get_auth_service

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/signup",
    response_model=AuthResponse,
    summary="Create Account",
    description="Register a new user account with email and password",
    responses={
        201: {"description": "Account created successfully"},
        409: {"description": "Email already exists"},
        422: {"description": "Validation error (invalid email or weak password)"},
    },
)
async def signup(
    request: Request,
    data: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """
    Register a new user account.

    Creates a new user in Supabase Auth with the provided email and password.
    Password must meet complexity requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Args:
        request: FastAPI request object
        data: Signup request data
        auth_service: Auth service instance

    Returns:
        AuthResponse with user data and session tokens
    """
    request_id = getattr(request.state, "request_id", None)

    logger.info(
        f"Signup request received for: {data.email}",
        extra={"request_id": request_id},
    )

    result = await auth_service.signup(
        email=data.email,
        password=data.password,
        full_name=data.full_name,
    )

    logger.info(
        f"Signup successful for user: {result.user.id}",
        extra={"request_id": request_id, "user_id": result.user.id},
    )

    return result


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login",
    description="Authenticate with email and password",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
    },
)
async def login(
    request: Request,
    data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """
    Authenticate a user with email and password.

    Validates credentials against Supabase Auth and returns
    session tokens for authenticated API requests.

    Args:
        request: FastAPI request object
        data: Login request data
        auth_service: Auth service instance

    Returns:
        AuthResponse with user data and session tokens
    """
    request_id = getattr(request.state, "request_id", None)

    logger.info(
        f"Login request received for: {data.email}",
        extra={"request_id": request_id},
    )

    result = await auth_service.login(
        email=data.email,
        password=data.password,
    )

    logger.info(
        f"Login successful for user: {result.user.id}",
        extra={"request_id": request_id, "user_id": result.user.id},
    )

    return result


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout",
    description="Sign out and invalidate the current session",
    responses={
        200: {"description": "Logout successful"},
        401: {"description": "Not authenticated"},
    },
)
async def logout(
    request: Request,
    access_token: str = Depends(get_access_token),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """
    Sign out the current user.

    Invalidates the current session in Supabase Auth.
    The client should discard their stored tokens after this call.

    Args:
        request: FastAPI request object
        access_token: Current access token
        auth_service: Auth service instance

    Returns:
        MessageResponse confirming logout
    """
    request_id = getattr(request.state, "request_id", None)

    logger.info(
        "Logout request received",
        extra={"request_id": request_id},
    )

    result = await auth_service.logout(access_token)

    logger.info(
        "Logout successful",
        extra={"request_id": request_id},
    )

    return result


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Refresh Token",
    description="Get new access token using refresh token",
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """
    Refresh the access token using a refresh token.

    When the access token expires, use this endpoint to get
    a new access token without requiring the user to log in again.

    Args:
        request: FastAPI request object
        data: Refresh token request data
        auth_service: Auth service instance

    Returns:
        AuthResponse with new session tokens
    """
    request_id = getattr(request.state, "request_id", None)

    logger.info(
        "Token refresh request received",
        extra={"request_id": request_id},
    )

    result = await auth_service.refresh_token(data.refresh_token)

    logger.info(
        "Token refresh successful",
        extra={"request_id": request_id},
    )

    return result


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User",
    description="Get the currently authenticated user's data",
    responses={
        200: {"description": "User data retrieved successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def get_me(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """
    Get the current authenticated user's information.

    Requires a valid access token in the Authorization header.

    Args:
        request: FastAPI request object
        current_user: Current authenticated user

    Returns:
        UserResponse with user data
    """
    request_id = getattr(request.state, "request_id", None)

    logger.debug(
        f"Get current user request for: {current_user.id}",
        extra={"request_id": request_id, "user_id": current_user.id},
    )

    return current_user
