"""
Custom exception classes and exception handlers for the application.

Provides consistent error handling and response formatting across all endpoints.
"""

from typing import Any, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """Base exception class for application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(AppException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
            details=details,
        )


class AuthorizationError(AppException):
    """Raised when user lacks permission for an action."""

    def __init__(
        self,
        message: str = "Permission denied",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
            details=details,
        )


class NotFoundError(AppException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details=details,
        )


class ValidationError(AppException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field

        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=error_details,
        )


class ConflictError(AppException):
    """Raised when there's a conflict (e.g., duplicate email)."""

    def __init__(
        self,
        message: str = "Resource already exists",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            details=details,
        )


class RateLimitError(AppException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after

        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
        )


class ExternalServiceError(AppException):
    """Raised when an external service (e.g., Supabase) fails."""

    def __init__(
        self,
        message: str = "External service error",
        service: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        error_details = details or {}
        if service:
            error_details["service"] = service

        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=error_details,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle AppException and return consistent JSON response.

    Args:
        request: The FastAPI request object
        exc: The AppException that was raised

    Returns:
        JSON response with error details
    """
    request_id = getattr(request.state, "request_id", None)

    logger.error(
        f"{exc.error_code}: {exc.message}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "details": exc.details,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "request_id": request_id,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTPException and return consistent JSON response.

    Args:
        request: The FastAPI request object
        exc: The HTTPException that was raised

    Returns:
        JSON response with error details
    """
    request_id = getattr(request.state, "request_id", None)

    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "details": {},
            "request_id": request_id,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions and return generic error response.

    Args:
        request: The FastAPI request object
        exc: The exception that was raised

    Returns:
        JSON response with generic error message
    """
    request_id = getattr(request.state, "request_id", None)

    logger.exception(
        f"Unhandled exception: {exc}",
        extra={
            "request_id": request_id,
            "error": str(exc),
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": {},
            "request_id": request_id,
        },
    )
