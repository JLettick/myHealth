"""
Authentication service containing business logic for auth operations.

This service layer handles the authentication workflow and transforms
Supabase responses into our application's schema format.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from gotrue.errors import AuthApiError

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    ExternalServiceError,
    ValidationError,
)
from app.core.logging_config import get_logger
from app.schemas.auth import (
    AuthResponse,
    MessageResponse,
    TokenResponse,
    UserResponse,
)
from app.services.supabase_client import SupabaseService, get_supabase_service

logger = get_logger(__name__)


class AuthService:
    """
    Authentication service for handling user auth operations.

    Provides a clean interface for signup, login, logout, and token refresh
    operations, with proper error handling and response transformation.
    """

    def __init__(self, supabase: SupabaseService):
        """
        Initialize auth service with Supabase service.

        Args:
            supabase: Supabase service instance
        """
        self.supabase = supabase

    def _transform_user(self, user: Any) -> UserResponse:
        """
        Transform Supabase user object to UserResponse schema.

        Args:
            user: Supabase user object

        Returns:
            UserResponse schema instance
        """
        user_metadata = user.user_metadata or {}

        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user_metadata.get("full_name"),
            avatar_url=user_metadata.get("avatar_url"),
            created_at=user.created_at,
            email_confirmed_at=user.email_confirmed_at,
        )

    def _transform_session(self, session: Any) -> TokenResponse:
        """
        Transform Supabase session object to TokenResponse schema.

        Args:
            session: Supabase session object

        Returns:
            TokenResponse schema instance
        """
        return TokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            token_type="Bearer",
            expires_in=session.expires_in,
            expires_at=datetime.fromtimestamp(session.expires_at, tz=timezone.utc),
        )

    async def signup(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
    ) -> AuthResponse:
        """
        Register a new user account.

        Args:
            email: User's email address
            password: User's password (must meet complexity requirements)
            full_name: Optional full name

        Returns:
            AuthResponse with user data and session tokens

        Raises:
            ConflictError: If email already exists
            ValidationError: If email is invalid
            ExternalServiceError: If Supabase operation fails
        """
        logger.info(f"Processing signup request for: {email}")

        try:
            result = await self.supabase.sign_up(email, password, full_name)

            user = result.get("user")
            session = result.get("session")

            if not user:
                logger.error("Signup succeeded but no user returned")
                raise ExternalServiceError(
                    message="Signup failed: No user data returned",
                    service="supabase",
                )

            # If no session, email confirmation is required
            if not session:
                logger.info(f"Signup successful, email confirmation required: {email}")
                # For now, we'll still return user data but with empty tokens
                # In production, you might want to handle this differently
                return AuthResponse(
                    user=self._transform_user(user),
                    session=TokenResponse(
                        access_token="",
                        refresh_token="",
                        token_type="Bearer",
                        expires_in=0,
                        expires_at=datetime.now(timezone.utc),
                    ),
                    message="Account created. Please check your email to confirm your account.",
                )

            logger.info(f"Signup successful for user: {user.id}")

            return AuthResponse(
                user=self._transform_user(user),
                session=self._transform_session(session),
                message="Account created successfully",
            )

        except AuthApiError as e:
            error_message = str(e).lower()

            if "already registered" in error_message or "already exists" in error_message:
                logger.warning(f"Signup failed - email already exists: {email}")
                raise ConflictError(
                    message="An account with this email already exists",
                    details={"field": "email"},
                )

            if "invalid" in error_message and "email" in error_message:
                logger.warning(f"Signup failed - invalid email: {email}")
                raise ValidationError(
                    message="Invalid email address",
                    field="email",
                )

            logger.error(f"Supabase auth error during signup: {e}")
            raise ExternalServiceError(
                message="Failed to create account",
                service="supabase",
                details={"error": str(e)},
            )

        except Exception as e:
            logger.exception(f"Unexpected error during signup: {e}")
            raise ExternalServiceError(
                message="An unexpected error occurred during signup",
                service="supabase",
            )

    async def login(self, email: str, password: str) -> AuthResponse:
        """
        Authenticate a user with email and password.

        Args:
            email: User's email address
            password: User's password

        Returns:
            AuthResponse with user data and session tokens

        Raises:
            AuthenticationError: If credentials are invalid
            ExternalServiceError: If Supabase operation fails
        """
        logger.info(f"Processing login request for: {email}")

        try:
            result = await self.supabase.sign_in(email, password)

            user = result.get("user")
            session = result.get("session")

            if not user or not session:
                logger.warning(f"Login failed - invalid credentials: {email}")
                raise AuthenticationError(
                    message="Invalid email or password",
                )

            logger.info(
                f"Login successful for user: {user.id}",
                extra={"user_id": str(user.id)},
            )

            return AuthResponse(
                user=self._transform_user(user),
                session=self._transform_session(session),
                message="Login successful",
            )

        except AuthenticationError:
            raise

        except AuthApiError as e:
            error_message = str(e).lower()

            if "invalid" in error_message or "credentials" in error_message:
                logger.warning(f"Login failed - invalid credentials: {email}")
                raise AuthenticationError(
                    message="Invalid email or password",
                )

            if "email not confirmed" in error_message:
                logger.warning(f"Login failed - email not confirmed: {email}")
                raise AuthenticationError(
                    message="Please confirm your email before logging in",
                    details={"reason": "email_not_confirmed"},
                )

            logger.error(f"Supabase auth error during login: {e}")
            raise ExternalServiceError(
                message="Login failed",
                service="supabase",
                details={"error": str(e)},
            )

        except Exception as e:
            logger.exception(f"Unexpected error during login: {e}")
            raise ExternalServiceError(
                message="An unexpected error occurred during login",
                service="supabase",
            )

    async def logout(self, access_token: str) -> MessageResponse:
        """
        Sign out a user and invalidate their session.

        Args:
            access_token: The user's access token

        Returns:
            MessageResponse confirming logout

        Raises:
            ExternalServiceError: If logout fails
        """
        logger.info("Processing logout request")

        try:
            await self.supabase.sign_out(access_token)

            logger.info("Logout successful")
            return MessageResponse(
                message="Logged out successfully",
                success=True,
            )

        except Exception as e:
            logger.error(f"Logout failed: {e}")
            # Even if logout fails on Supabase side, we consider it successful
            # from the client's perspective
            return MessageResponse(
                message="Logged out successfully",
                success=True,
            )

    async def refresh_token(self, refresh_token: str) -> AuthResponse:
        """
        Refresh a user's session using their refresh token.

        Args:
            refresh_token: The user's refresh token

        Returns:
            AuthResponse with new session tokens

        Raises:
            AuthenticationError: If refresh token is invalid
            ExternalServiceError: If Supabase operation fails
        """
        logger.info("Processing token refresh request")

        try:
            result = await self.supabase.refresh_session(refresh_token)

            user = result.get("user")
            session = result.get("session")

            if not session:
                logger.warning("Token refresh failed - invalid refresh token")
                raise AuthenticationError(
                    message="Invalid or expired refresh token",
                )

            logger.info("Token refresh successful")

            return AuthResponse(
                user=self._transform_user(user),
                session=self._transform_session(session),
                message="Token refreshed successfully",
            )

        except AuthenticationError:
            raise

        except AuthApiError as e:
            logger.warning(f"Token refresh failed: {e}")
            raise AuthenticationError(
                message="Invalid or expired refresh token",
            )

        except Exception as e:
            logger.exception(f"Unexpected error during token refresh: {e}")
            raise ExternalServiceError(
                message="An unexpected error occurred during token refresh",
                service="supabase",
            )

    async def get_current_user(self, access_token: str) -> UserResponse:
        """
        Get current user data from access token.

        Args:
            access_token: The user's access token

        Returns:
            UserResponse with current user data

        Raises:
            AuthenticationError: If token is invalid
        """
        logger.debug("Getting current user from token")

        try:
            result = await self.supabase.get_user(access_token)
            user = result.get("user")

            if not user:
                raise AuthenticationError(
                    message="Invalid or expired token",
                )

            return self._transform_user(user)

        except AuthApiError as e:
            logger.warning(f"Failed to get current user: {e}")
            raise AuthenticationError(
                message="Invalid or expired token",
            )

        except AuthenticationError:
            raise

        except Exception as e:
            logger.exception(f"Unexpected error getting current user: {e}")
            raise AuthenticationError(
                message="Failed to verify authentication",
            )


def get_auth_service() -> AuthService:
    """Get auth service instance."""
    return AuthService(get_supabase_service())
