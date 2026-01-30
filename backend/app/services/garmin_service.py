"""
Service for Garmin OAuth and connection management.

Handles OAuth flow, token storage/encryption, and connection status.
"""

import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

import httpx

from app.config import get_settings
from app.core.encryption import get_encryption_service
from app.services.supabase_client import get_supabase_service

logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory state storage for OAuth CSRF protection
# NOTE: In production, use Redis or another distributed store
oauth_states: Dict[str, str] = {}


class GarminService:
    """Service for managing Garmin OAuth connections."""

    def __init__(self):
        self.supabase = get_supabase_service()
        self.encryption = get_encryption_service()

    def generate_authorization_url(self, user_id: str) -> tuple[str, str]:
        """
        Generate OAuth authorization URL with state token.

        Args:
            user_id: The user's ID to associate with the OAuth flow.

        Returns:
            Tuple of (authorization_url, state_token)
        """
        state = secrets.token_urlsafe(32)
        oauth_states[state] = user_id

        # Build authorization URL with query parameters
        params = {
            "client_id": settings.garmin_client_id,
            "redirect_uri": settings.garmin_redirect_uri,
            "response_type": "code",
            "scope": "activity sleep heartrate daily",
            "state": state,
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{settings.garmin_auth_url}?{query_string}"

        logger.info(f"Generated Garmin authorization URL for user {user_id}")
        return url, state

    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            code: The authorization code from Garmin OAuth callback.

        Returns:
            Dictionary containing access_token, refresh_token, expires_in, etc.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.garmin_token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.garmin_client_id,
                    "client_secret": settings.garmin_client_secret,
                    "redirect_uri": settings.garmin_redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token.

        Args:
            refresh_token: The refresh token to use.

        Returns:
            Dictionary containing new access_token, refresh_token, expires_in, etc.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.garmin_token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.garmin_client_id,
                    "client_secret": settings.garmin_client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()

    def save_connection(
        self,
        user_id: str,
        garmin_user_id: str,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        scopes: list[str],
    ) -> None:
        """
        Save or update Garmin connection with encrypted tokens.

        Args:
            user_id: The user's ID.
            garmin_user_id: The user's Garmin ID.
            access_token: The OAuth access token (will be encrypted).
            refresh_token: The OAuth refresh token (will be encrypted).
            expires_in: Token expiration time in seconds.
            scopes: List of granted OAuth scopes.
        """
        encrypted_access = self.encryption.encrypt(access_token)
        encrypted_refresh = self.encryption.encrypt(refresh_token)
        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        self.supabase.admin_client.table("garmin_connections").upsert(
            {
                "user_id": user_id,
                "garmin_user_id": garmin_user_id,
                "access_token_encrypted": encrypted_access,
                "refresh_token_encrypted": encrypted_refresh,
                "token_expires_at": token_expires_at.isoformat(),
                "scopes": scopes,
                "is_active": True,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            on_conflict="user_id",
        ).execute()

        logger.info(f"Saved Garmin connection for user {user_id}")

    def get_connection(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Garmin connection for a user.

        Args:
            user_id: The user's ID.

        Returns:
            Connection data dictionary or None if not found.
        """
        try:
            result = (
                self.supabase.admin_client.table("garmin_connections")
                .select("*")
                .eq("user_id", user_id)
                .eq("is_active", True)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.warning(f"Failed to get Garmin connection for user {user_id}: {e}")
            return None

    async def get_valid_access_token(self, user_id: str) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary.

        Args:
            user_id: The user's ID.

        Returns:
            Valid access token or None if no connection exists.
        """
        connection = self.get_connection(user_id)
        if not connection:
            return None

        expires_at = datetime.fromisoformat(
            connection["token_expires_at"].replace("Z", "+00:00")
        )

        # Refresh if expiring within 5 minutes
        if datetime.now(timezone.utc) + timedelta(minutes=5) >= expires_at:
            logger.info(f"Refreshing expired Garmin token for user {user_id}")

            refresh_token = self.encryption.decrypt(
                connection["refresh_token_encrypted"]
            )
            new_tokens = await self.refresh_access_token(refresh_token)

            self.save_connection(
                user_id=user_id,
                garmin_user_id=connection["garmin_user_id"],
                access_token=new_tokens["access_token"],
                refresh_token=new_tokens.get("refresh_token", refresh_token),
                expires_in=new_tokens["expires_in"],
                scopes=connection["scopes"],
            )
            return new_tokens["access_token"]

        return self.encryption.decrypt(connection["access_token_encrypted"])

    def disconnect(self, user_id: str) -> bool:
        """
        Disconnect Garmin account (soft delete).

        Args:
            user_id: The user's ID.

        Returns:
            True if connection was found and deactivated, False otherwise.
        """
        result = (
            self.supabase.admin_client.table("garmin_connections")
            .update({
                "is_active": False,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            .eq("user_id", user_id)
            .execute()
        )

        success = len(result.data) > 0
        if success:
            logger.info(f"Disconnected Garmin for user {user_id}")
        return success

    def update_last_sync(self, user_id: str) -> None:
        """
        Update the last sync timestamp.

        Args:
            user_id: The user's ID.
        """
        self.supabase.admin_client.table("garmin_connections").update(
            {"last_sync_at": datetime.now(timezone.utc).isoformat()}
        ).eq("user_id", user_id).execute()

    def get_connection_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get connection status for a user.

        Args:
            user_id: The user's ID.

        Returns:
            Dictionary with connection status information.
        """
        connection = self.get_connection(user_id)
        if not connection:
            return {
                "is_connected": False,
                "garmin_user_id": None,
                "connected_at": None,
                "last_sync_at": None,
                "scopes": [],
            }

        return {
            "is_connected": True,
            "garmin_user_id": connection["garmin_user_id"],
            "connected_at": connection["created_at"],
            "last_sync_at": connection["last_sync_at"],
            "scopes": connection["scopes"] or [],
        }

    @staticmethod
    def validate_state(state: str) -> Optional[str]:
        """
        Validate and consume OAuth state token.

        Args:
            state: The state token from OAuth callback.

        Returns:
            The user_id if state is valid, None otherwise.
        """
        return oauth_states.pop(state, None)
