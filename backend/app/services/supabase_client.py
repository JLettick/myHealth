"""
Supabase client wrapper service.

Provides a singleton Supabase client instance and helper methods
for interacting with Supabase services.
"""

from functools import lru_cache
from typing import Any, Optional

from supabase import Client, create_client

from app.config import Settings, get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SupabaseService:
    """
    Wrapper service for Supabase client operations.

    Provides methods for authentication and database operations
    with proper error handling and logging.
    """

    def __init__(self, settings: Settings):
        """
        Initialize Supabase service with settings.

        Args:
            settings: Application settings containing Supabase credentials
        """
        self.settings = settings
        self._client: Optional[Client] = None
        self._admin_client: Optional[Client] = None

    @property
    def client(self) -> Client:
        """
        Get the Supabase client (anon key).

        Uses lazy initialization to create client on first access.
        """
        if self._client is None:
            logger.info("Initializing Supabase client")
            self._client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_anon_key,
            )
        return self._client

    @property
    def admin_client(self) -> Client:
        """
        Get the Supabase admin client (service role key).

        This client has elevated privileges and should be used
        carefully for admin operations only.
        """
        if self._admin_client is None:
            logger.info("Initializing Supabase admin client")
            self._admin_client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_service_role_key,
            )
        return self._admin_client

    async def sign_up(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Register a new user with Supabase Auth.

        Args:
            email: User's email address
            password: User's password
            full_name: Optional full name to store in metadata

        Returns:
            Dictionary containing user and session data

        Raises:
            Exception: If signup fails
        """
        logger.info(f"Attempting signup for email: {email}")

        options = {}
        if full_name:
            options["data"] = {"full_name": full_name}

        try:
            response = self.client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": options,
                }
            )

            if response.user:
                logger.info(
                    f"Signup successful for user: {response.user.id}",
                    extra={"user_id": response.user.id},
                )
            else:
                logger.warning(f"Signup returned no user for email: {email}")

            return {
                "user": response.user,
                "session": response.session,
            }

        except Exception as e:
            logger.error(f"Signup failed for email {email}: {e}")
            raise

    async def sign_in(self, email: str, password: str) -> dict[str, Any]:
        """
        Authenticate a user with email and password.

        Args:
            email: User's email address
            password: User's password

        Returns:
            Dictionary containing user and session data

        Raises:
            Exception: If login fails
        """
        logger.info(f"Attempting login for email: {email}")

        try:
            response = self.client.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password,
                }
            )

            if response.user:
                logger.info(
                    f"Login successful for user: {response.user.id}",
                    extra={"user_id": response.user.id},
                )

            return {
                "user": response.user,
                "session": response.session,
            }

        except Exception as e:
            logger.warning(f"Login failed for email {email}: {e}")
            raise

    async def sign_out(self, access_token: str) -> bool:
        """
        Sign out a user and invalidate their session.

        Args:
            access_token: The user's access token

        Returns:
            True if signout was successful
        """
        logger.info("Attempting to sign out user")

        try:
            # Use admin client to sign out — avoids mutating shared anon client session state
            self.admin_client.auth.admin.sign_out(access_token)
            logger.info("Sign out successful")
            return True

        except Exception as e:
            # Token will expire naturally; frontend already clears tokens
            logger.warning(f"Sign out via admin failed (token will expire naturally): {e}")
            return True

    async def refresh_session(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh a user's session using their refresh token.

        Args:
            refresh_token: The user's refresh token

        Returns:
            Dictionary containing new session data

        Raises:
            Exception: If refresh fails
        """
        logger.info("Attempting to refresh session")

        try:
            response = self.client.auth.refresh_session(refresh_token)

            if response.session:
                logger.info("Session refresh successful")

            return {
                "user": response.user,
                "session": response.session,
            }

        except Exception as e:
            logger.warning(f"Session refresh failed: {e}")
            raise

    async def get_user(self, access_token: str) -> dict[str, Any]:
        """
        Get user data from an access token.

        Args:
            access_token: The user's access token

        Returns:
            User data dictionary

        Raises:
            Exception: If token is invalid
        """
        logger.debug("Getting user from access token")

        try:
            response = self.client.auth.get_user(access_token)

            if response.user:
                logger.debug(
                    f"Got user data for: {response.user.id}",
                    extra={"user_id": response.user.id},
                )

            return {"user": response.user}

        except Exception as e:
            logger.warning(f"Failed to get user: {e}")
            raise

    async def get_profile(self, user_id: str) -> Optional[dict[str, Any]]:
        """
        Get user profile from the profiles table.

        Args:
            user_id: The user's UUID

        Returns:
            Profile data or None if not found
        """
        logger.debug(f"Getting profile for user: {user_id}")

        try:
            response = (
                self.admin_client.table("profiles")
                .select("*")
                .eq("id", user_id)
                .single()
                .execute()
            )

            return response.data

        except Exception as e:
            logger.warning(f"Failed to get profile for user {user_id}: {e}")
            return None

    async def update_profile(
        self,
        user_id: str,
        data: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        """
        Update user profile in the profiles table.

        Args:
            user_id: The user's UUID
            data: Dictionary of fields to update

        Returns:
            Updated profile data or None if failed
        """
        logger.info(f"Updating profile for user: {user_id}")

        try:
            response = (
                self.admin_client.table("profiles")
                .update(data)
                .eq("id", user_id)
                .execute()
            )

            if response.data:
                logger.info(f"Profile updated for user: {user_id}")
                return response.data[0] if response.data else None

            return None

        except Exception as e:
            logger.error(f"Failed to update profile for user {user_id}: {e}")
            raise

    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user account (admin operation).

        Args:
            user_id: The user's UUID

        Returns:
            True if deletion was successful
        """
        logger.warning(f"Deleting user account: {user_id}")

        try:
            self.admin_client.auth.admin.delete_user(user_id)
            logger.info(f"User account deleted: {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise


@lru_cache()
def get_supabase_service() -> SupabaseService:
    """
    Get cached Supabase service instance.

    Uses lru_cache to ensure only one instance is created.
    """
    return SupabaseService(get_settings())
