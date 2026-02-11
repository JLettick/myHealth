"""
Authentication endpoints for user signup, login, logout, and token refresh.

Refresh tokens are sent as httpOnly cookies for XSS protection.
Access tokens are returned in the JSON body (stored in memory by the frontend).
"""

from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.exceptions import AuthenticationError
from app.core.logging_config import get_logger
from app.dependencies import get_access_token, get_current_user
from app.middleware.rate_limit import limiter
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

# Cookie settings
_COOKIE_KEY = "refresh_token"
_COOKIE_PATH = "/api/v1/auth"
_COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 30 days


def _set_refresh_cookie(response: JSONResponse, token: str) -> None:
    """Set the refresh token as an httpOnly cookie on the response."""
    settings = get_settings()
    response.set_cookie(
        key=_COOKIE_KEY,
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path=_COOKIE_PATH,
        max_age=_COOKIE_MAX_AGE,
    )


def _clear_refresh_cookie(response: JSONResponse) -> None:
    """Clear the refresh token cookie on the response."""
    settings = get_settings()
    response.delete_cookie(
        key=_COOKIE_KEY,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path=_COOKIE_PATH,
    )


def _auth_response_with_cookie(result: AuthResponse) -> JSONResponse:
    """
    Build a JSONResponse from an AuthResponse, moving the refresh token
    from the JSON body into an httpOnly cookie.
    """
    # Extract refresh token before nulling it in the body
    refresh_token = result.session.refresh_token

    # Null the refresh token in the response body
    result.session.refresh_token = None

    response = JSONResponse(content=result.model_dump(mode="json"))

    if refresh_token:
        _set_refresh_cookie(response, refresh_token)

    return response


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
@limiter.limit("5/minute")
async def signup(
    request: Request,
    data: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Register a new user account.

    Creates a new user in Supabase Auth with the provided email and password.
    The refresh token is set as an httpOnly cookie; the access token is
    returned in the JSON response body.
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

    return _auth_response_with_cookie(result)


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
@limiter.limit("10/minute")
async def login(
    request: Request,
    data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate a user with email and password.

    The refresh token is set as an httpOnly cookie; the access token is
    returned in the JSON response body.
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

    return _auth_response_with_cookie(result)


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
@limiter.limit("30/minute")
async def logout(
    request: Request,
    access_token: str = Depends(get_access_token),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Sign out the current user.

    Invalidates the current session and clears the refresh token cookie.
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

    response = JSONResponse(content=result.model_dump(mode="json"))
    _clear_refresh_cookie(response)
    return response


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
@limiter.limit("30/minute")
async def refresh_token(
    request: Request,
    data: Optional[RefreshTokenRequest] = None,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Refresh the access token using a refresh token.

    Reads the refresh token from the httpOnly cookie first,
    falls back to the request body for backward compatibility.
    """
    request_id = getattr(request.state, "request_id", None)

    logger.info(
        "Token refresh request received",
        extra={"request_id": request_id},
    )

    # Prefer cookie, fall back to request body
    token = request.cookies.get(_COOKIE_KEY)
    if not token and data:
        token = data.refresh_token

    if not token:
        raise AuthenticationError(message="No refresh token provided")

    result = await auth_service.refresh_token(token)

    logger.info(
        "Token refresh successful",
        extra={"request_id": request_id},
    )

    return _auth_response_with_cookie(result)


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
@limiter.limit("30/minute")
async def get_me(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """
    Get the current authenticated user's information.

    Requires a valid access token in the Authorization header.
    """
    request_id = getattr(request.state, "request_id", None)

    logger.debug(
        f"Get current user request for: {current_user.id}",
        extra={"request_id": request_id, "user_id": current_user.id},
    )

    return current_user
