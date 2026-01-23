"""
Pydantic schemas for authentication request/response validation.

These schemas ensure type safety and validation for all auth-related
API endpoints.
"""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    """Schema for user registration request."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User's password (min 8 characters)",
    )
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="User's full name",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Enforce password complexity requirements.

        Password must contain:
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", v):
            raise ValueError("Password must contain at least one special character")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "full_name": "John Doe",
            }
        }
    }


class LoginRequest(BaseModel):
    """Schema for user login request."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
            }
        }
    }


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(..., description="The refresh token")

    model_config = {
        "json_schema_extra": {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    }


class TokenResponse(BaseModel):
    """Schema for authentication token response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Seconds until access token expiration")
    expires_at: datetime = Field(..., description="Timestamp when access token expires")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 3600,
                "expires_at": "2024-01-15T12:00:00Z",
            }
        }
    }


class UserResponse(BaseModel):
    """Schema for user data in responses."""

    id: str = Field(..., description="User's unique ID")
    email: str = Field(..., description="User's email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar")
    created_at: datetime = Field(..., description="Account creation timestamp")
    email_confirmed_at: Optional[datetime] = Field(
        None, description="Email confirmation timestamp"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "avatar_url": None,
                "created_at": "2024-01-15T10:00:00Z",
                "email_confirmed_at": "2024-01-15T10:05:00Z",
            }
        }
    }


class AuthResponse(BaseModel):
    """Schema for successful authentication response (login/signup)."""

    user: UserResponse = Field(..., description="User data")
    session: TokenResponse = Field(..., description="Session tokens")
    message: str = Field(..., description="Success message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "avatar_url": None,
                    "created_at": "2024-01-15T10:00:00Z",
                    "email_confirmed_at": "2024-01-15T10:05:00Z",
                },
                "session": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "expires_at": "2024-01-15T12:00:00Z",
                },
                "message": "Login successful",
            }
        }
    }


class MessageResponse(BaseModel):
    """Generic message response for operations like logout."""

    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Operation success status")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Logged out successfully",
                "success": True,
            }
        }
    }
