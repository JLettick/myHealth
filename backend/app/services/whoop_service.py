"""
Whoop OAuth service for connection management.

Handles:
- OAuth authorization flow
- Token storage and encryption
- Token refresh
- Connection status management
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from app.config import Settings, get_settings
from app.core.encryption import get_encryption_service
from app.core.exceptions import (
    WhoopAuthError,
    WhoopNotConnectedError,
    WhoopTokenExpiredError,
)
from app.core.logging_config import get_logger
from app.services.supabase_client import SupabaseService, get_supabase_service

logger = get_logger(__name__)

# OAuth scopes to request
WHOOP_SCOPES = [
    "offline",  # Required to get refresh token
    "read:profile",
    "read:cycles",
    "read:recovery",
    "read:sleep",
    "read:workout",
]


class WhoopOAuthService:
    """
    Service for managing Whoop OAuth connections.

    Handles the complete OAuth flow and token management.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        supabase: Optional[SupabaseService] = None,
    ):
        """
        Initialize Whoop OAuth service.

        Args:
            settings: Application settings
            supabase: Supabase service instance
        """
        self.settings = settings or get_settings()
        self.supabase = supabase or get_supabase_service()
        self.encryption = get_encryption_service()

        # OAuth URLs
        self.auth_url = self.settings.whoop_auth_url
        self.token_url = self.settings.whoop_token_url
        self.redirect_uri = self.settings.whoop_redirect_uri
        self.client_id = self.settings.whoop_client_id
        self.client_secret = self.settings.whoop_client_secret

    def generate_authorization_url(self) -> tuple[str, str]:
        """
        Generate OAuth authorization URL.

        Returns:
            Tuple of (authorization_url, state)
        """
        # Generate cryptographic state for CSRF protection
        state = secrets.token_urlsafe(32)

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(WHOOP_SCOPES),
            "state": state,
        }

        authorization_url = f"{self.auth_url}?{urlencode(params)}"
        logger.info("Generated Whoop authorization URL")

        return authorization_url, state

    async def exchange_code_for_tokens(self, code: str) -> dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from callback

        Returns:
            Token response containing access_token, refresh_token, expires_in

        Raises:
            WhoopAuthError: If token exchange fails
        """
        logger.info("Exchanging authorization code for tokens")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": self.redirect_uri,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30.0,
                )

                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"Token exchange failed: {response.status_code} - {error_detail}")
                    raise WhoopAuthError(
                        message="Failed to exchange authorization code",
                        details={"status": response.status_code, "error": error_detail}
                    )

                tokens = response.json()
                logger.info("Successfully exchanged code for tokens")
                return tokens

            except httpx.RequestError as e:
                logger.error(f"Token exchange request failed: {e}")
                raise WhoopAuthError(
                    message="Failed to connect to Whoop for token exchange",
                    details={"error": str(e)}
                )

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Current refresh token

        Returns:
            New token response

        Raises:
            WhoopTokenExpiredError: If refresh token is invalid/expired
        """
        logger.info("Refreshing Whoop access token")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30.0,
                )

                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"Token refresh failed: {response.status_code} - {error_detail}")
                    raise WhoopTokenExpiredError(
                        message="Refresh token expired - please reconnect Whoop",
                        details={"status": response.status_code}
                    )

                tokens = response.json()
                logger.info("Successfully refreshed access token")
                return tokens

            except httpx.RequestError as e:
                logger.error(f"Token refresh request failed: {e}")
                raise WhoopAuthError(
                    message="Failed to connect to Whoop for token refresh",
                    details={"error": str(e)}
                )

    async def save_connection(
        self,
        user_id: str,
        whoop_user_id: str,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        scopes: list[str],
    ) -> dict[str, Any]:
        """
        Save or update Whoop connection in database.

        Tokens are encrypted before storage.

        Args:
            user_id: Application user ID
            whoop_user_id: Whoop user ID
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_in: Token validity in seconds
            scopes: Granted OAuth scopes

        Returns:
            Saved connection data
        """
        logger.info(f"Saving Whoop connection for user {user_id}")

        # Encrypt tokens
        encrypted_access = self.encryption.encrypt(access_token)
        encrypted_refresh = self.encryption.encrypt(refresh_token)

        # Calculate expiration time
        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        connection_data = {
            "user_id": user_id,
            "whoop_user_id": whoop_user_id,
            "access_token_encrypted": encrypted_access,
            "refresh_token_encrypted": encrypted_refresh,
            "token_expires_at": token_expires_at.isoformat(),
            "scopes": scopes,
            "is_active": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Upsert connection
        response = (
            self.supabase.admin_client.table("whoop_connections")
            .upsert(connection_data, on_conflict="user_id")
            .execute()
        )

        if response.data:
            logger.info(f"Whoop connection saved for user {user_id}")
            return response.data[0]

        logger.error(f"Failed to save Whoop connection for user {user_id}")
        raise WhoopAuthError(message="Failed to save Whoop connection")

    async def get_connection(self, user_id: str) -> Optional[dict[str, Any]]:
        """
        Get user's Whoop connection.

        Args:
            user_id: Application user ID

        Returns:
            Connection data or None if not connected
        """
        try:
            response = (
                self.supabase.admin_client.table("whoop_connections")
                .select("*")
                .eq("user_id", user_id)
                .eq("is_active", True)
                .limit(1)
                .execute()
            )

            return response.data[0] if response.data else None
        except Exception as e:
            logger.warning(f"Failed to get Whoop connection for user {user_id}: {e}")
            return None

    async def get_valid_access_token(self, user_id: str) -> str:
        """
        Get a valid access token, refreshing if necessary.

        Args:
            user_id: Application user ID

        Returns:
            Valid decrypted access token

        Raises:
            WhoopNotConnectedError: If user hasn't connected Whoop
            WhoopTokenExpiredError: If refresh fails
        """
        connection = await self.get_connection(user_id)

        if not connection:
            raise WhoopNotConnectedError()

        # Check if token is expired or about to expire (5 min buffer)
        expires_at = datetime.fromisoformat(connection["token_expires_at"].replace("Z", "+00:00"))
        buffer_time = timedelta(minutes=5)

        if datetime.now(timezone.utc) + buffer_time >= expires_at:
            logger.info(f"Token expired or expiring soon for user {user_id}, refreshing")

            # Decrypt refresh token
            refresh_token = self.encryption.decrypt(connection["refresh_token_encrypted"])

            # Get new tokens
            new_tokens = await self.refresh_access_token(refresh_token)

            # Save new tokens
            await self.save_connection(
                user_id=user_id,
                whoop_user_id=connection["whoop_user_id"],
                access_token=new_tokens["access_token"],
                refresh_token=new_tokens.get("refresh_token", refresh_token),
                expires_in=new_tokens["expires_in"],
                scopes=connection["scopes"],
            )

            return new_tokens["access_token"]

        # Token is valid, decrypt and return
        return self.encryption.decrypt(connection["access_token_encrypted"])

    async def disconnect(self, user_id: str) -> bool:
        """
        Disconnect user's Whoop account.

        Marks connection as inactive but retains historical data.

        Args:
            user_id: Application user ID

        Returns:
            True if disconnected successfully
        """
        logger.info(f"Disconnecting Whoop for user {user_id}")

        response = (
            self.supabase.admin_client.table("whoop_connections")
            .update({"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()})
            .eq("user_id", user_id)
            .execute()
        )

        if response.data:
            logger.info(f"Whoop disconnected for user {user_id}")
            return True

        logger.warning(f"No active Whoop connection found for user {user_id}")
        return False

    async def update_last_sync(self, user_id: str) -> None:
        """
        Update the last sync timestamp for a connection.

        Args:
            user_id: Application user ID
        """
        (
            self.supabase.admin_client.table("whoop_connections")
            .update({
                "last_sync_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
            .eq("user_id", user_id)
            .execute()
        )


# Singleton instance
_whoop_service: WhoopOAuthService | None = None


def get_whoop_service() -> WhoopOAuthService:
    """Get the Whoop OAuth service singleton."""
    global _whoop_service
    if _whoop_service is None:
        _whoop_service = WhoopOAuthService()
    return _whoop_service
