"""
Security utilities for authentication and authorization.

Handles JWT token verification with Supabase and provides
password hashing utilities if needed for additional security.
"""

import secrets
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Password hashing context (if needed beyond Supabase)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Note: Supabase handles password hashing internally, but this is
    available if additional password operations are needed.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against

    Returns:
        True if passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate a bcrypt hash of a password.

    Args:
        password: Plain text password to hash

    Returns:
        Bcrypt hashed password
    """
    return pwd_context.hash(password)


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Args:
        length: Length of the token in bytes (default 32)

    Returns:
        URL-safe base64 encoded token
    """
    return secrets.token_urlsafe(length)


async def verify_supabase_token(
    token: str,
    supabase_url: str,
    supabase_anon_key: str,
) -> dict[str, Any]:
    """
    Verify a Supabase JWT token by calling the Supabase API.

    This method validates the token by making a request to Supabase's
    /auth/v1/user endpoint with the token. If the token is valid,
    Supabase returns the user data.

    Args:
        token: The JWT access token to verify
        supabase_url: The Supabase project URL
        supabase_anon_key: The Supabase anonymous key

    Returns:
        User data dictionary from Supabase

    Raises:
        JWTError: If the token is invalid or expired
    """
    logger.debug("Verifying Supabase token", extra={"token_prefix": token[:20] + "..."})

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{supabase_url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": supabase_anon_key,
                },
                timeout=10.0,
            )

            if response.status_code == 401:
                logger.warning("Token verification failed: Unauthorized")
                raise JWTError("Invalid or expired token")

            if response.status_code != 200:
                logger.error(
                    f"Token verification failed with status {response.status_code}",
                    extra={"status_code": response.status_code},
                )
                raise JWTError(f"Token verification failed: {response.status_code}")

            user_data = response.json()
            logger.debug(
                "Token verified successfully",
                extra={"user_id": user_data.get("id")},
            )
            return user_data

        except httpx.RequestError as e:
            logger.error(f"Network error during token verification: {e}")
            raise JWTError(f"Network error during token verification: {e}")


def decode_jwt_without_verification(token: str) -> Optional[dict[str, Any]]:
    """
    Decode a JWT token without verification (for debugging/logging only).

    WARNING: This should only be used for debugging. Always use
    verify_supabase_token for actual authentication.

    Args:
        token: The JWT token to decode

    Returns:
        Decoded payload or None if decoding fails
    """
    try:
        # Decode without verification - only for debugging
        payload = jwt.get_unverified_claims(token)
        return payload
    except JWTError:
        return None


def is_token_expired(token: str) -> bool:
    """
    Check if a JWT token is expired based on its exp claim.

    Args:
        token: The JWT token to check

    Returns:
        True if expired, False otherwise
    """
    payload = decode_jwt_without_verification(token)
    if not payload or "exp" not in payload:
        return True

    exp_timestamp = payload["exp"]
    current_timestamp = datetime.now(timezone.utc).timestamp()

    return current_timestamp >= exp_timestamp
