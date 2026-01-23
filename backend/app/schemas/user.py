"""
Pydantic schemas for user-related request/response validation.

These schemas handle user profile operations.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class UserProfileResponse(BaseModel):
    """Schema for user profile response."""

    id: str = Field(..., description="User's unique ID")
    email: str = Field(..., description="User's email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "avatar_url": "https://example.com/avatar.jpg",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-16T14:30:00Z",
            }
        }
    }


class UpdateProfileRequest(BaseModel):
    """Schema for updating user profile."""

    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="User's full name",
    )
    avatar_url: Optional[str] = Field(
        None,
        max_length=500,
        description="URL to user's avatar image",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "full_name": "Jane Doe",
                "avatar_url": "https://example.com/new-avatar.jpg",
            }
        }
    }


class DeleteAccountRequest(BaseModel):
    """Schema for account deletion confirmation."""

    confirm: bool = Field(
        ...,
        description="Must be True to confirm account deletion",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "confirm": True,
            }
        }
    }


class ErrorDetail(BaseModel):
    """Schema for detailed error information."""

    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")

    model_config = {
        "json_schema_extra": {
            "example": {
                "field": "email",
                "message": "Email already exists",
                "code": "DUPLICATE_EMAIL",
            }
        }
    }


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for debugging")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "VALIDATION_ERROR",
                "message": "Invalid email format",
                "details": {"field": "email"},
                "request_id": "abc123",
            }
        }
    }
