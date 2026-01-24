"""
Whoop API client for making authenticated requests.

Handles:
- Token-based authentication
- Rate limiting awareness
- Pagination
- Error handling
"""

import time
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx

from app.config import Settings, get_settings
from app.core.exceptions import WhoopAuthError, WhoopRateLimitError, WhoopError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class WhoopAPIClient:
    """
    Client for interacting with Whoop Developer API.

    Provides methods for fetching cycles, recovery, sleep, and workout data.
    Handles authentication headers and rate limiting.
    """

    def __init__(self, access_token: str, settings: Optional[Settings] = None):
        """
        Initialize Whoop API client.

        Args:
            access_token: Valid OAuth access token
            settings: Application settings (uses default if not provided)
        """
        self.settings = settings or get_settings()
        self.access_token = access_token
        self.base_url = self.settings.whoop_api_base_url

        # Rate limiting tracking
        self._request_count = 0
        self._minute_start = time.time()
        self._max_requests_per_minute = 100

    def _check_rate_limit(self) -> None:
        """Check if we're approaching rate limits."""
        current_time = time.time()

        # Reset counter if minute has passed
        if current_time - self._minute_start >= 60:
            self._request_count = 0
            self._minute_start = current_time

        # Check if we're at limit
        if self._request_count >= self._max_requests_per_minute:
            wait_time = 60 - (current_time - self._minute_start)
            logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
            raise WhoopRateLimitError(
                message="Rate limit reached - please wait before making more requests",
                retry_after=int(wait_time) + 1
            )

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authorization."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Make an authenticated request to Whoop API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/v1/cycle")
            params: Query parameters
            data: Request body data

        Returns:
            Response JSON data

        Raises:
            WhoopAuthError: If authentication fails
            WhoopRateLimitError: If rate limit exceeded
            WhoopError: For other API errors
        """
        self._check_rate_limit()

        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Whoop API request: {method} {endpoint}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    params=params,
                    json=data,
                    timeout=30.0,
                )

                self._request_count += 1

                # Handle rate limiting response
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Whoop API rate limited, retry after {retry_after}s")
                    raise WhoopRateLimitError(retry_after=retry_after)

                # Handle auth errors
                if response.status_code == 401:
                    logger.error("Whoop API authentication failed - token may be expired")
                    raise WhoopAuthError(message="Access token expired or invalid")

                # Handle other errors
                if response.status_code >= 400:
                    error_detail = response.text
                    logger.error(f"Whoop API error {response.status_code}: {error_detail}")
                    raise WhoopError(
                        message=f"Whoop API error: {response.status_code}",
                        details={"status_code": response.status_code, "response": error_detail}
                    )

                return response.json()

            except httpx.RequestError as e:
                logger.error(f"Whoop API request failed: {e}")
                raise WhoopError(
                    message="Failed to connect to Whoop API",
                    details={"error": str(e)}
                )

    async def get_user_profile(self) -> dict[str, Any]:
        """
        Get the authenticated user's profile.

        Returns:
            User profile data including user_id
        """
        return await self._make_request("GET", "/v2/user/profile/basic")

    async def get_cycles(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 25,
        next_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get physiological cycles.

        Args:
            start: Start datetime for range
            end: End datetime for range
            limit: Number of records per page (max 25)
            next_token: Pagination token

        Returns:
            Paginated cycle data
        """
        params: dict[str, Any] = {"limit": min(limit, 25)}

        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()
        if next_token:
            params["nextToken"] = next_token

        return await self._make_request("GET", "/v2/cycle", params=params)

    async def get_recovery(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 25,
        next_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get recovery records.

        Args:
            start: Start datetime for range
            end: End datetime for range
            limit: Number of records per page (max 25)
            next_token: Pagination token

        Returns:
            Paginated recovery data
        """
        params: dict[str, Any] = {"limit": min(limit, 25)}

        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()
        if next_token:
            params["nextToken"] = next_token

        return await self._make_request("GET", "/v2/recovery", params=params)

    async def get_sleep(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 25,
        next_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get sleep records.

        Args:
            start: Start datetime for range
            end: End datetime for range
            limit: Number of records per page (max 25)
            next_token: Pagination token

        Returns:
            Paginated sleep data
        """
        params: dict[str, Any] = {"limit": min(limit, 25)}

        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()
        if next_token:
            params["nextToken"] = next_token

        return await self._make_request("GET", "/v2/activity/sleep", params=params)

    async def get_workouts(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 25,
        next_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get workout records.

        Args:
            start: Start datetime for range
            end: End datetime for range
            limit: Number of records per page (max 25)
            next_token: Pagination token

        Returns:
            Paginated workout data
        """
        params: dict[str, Any] = {"limit": min(limit, 25)}

        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()
        if next_token:
            params["nextToken"] = next_token

        return await self._make_request("GET", "/v2/activity/workout", params=params)

    async def get_all_cycles(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch all cycles in date range, handling pagination.

        Args:
            start: Start datetime
            end: End datetime

        Returns:
            List of all cycle records
        """
        all_records = []
        next_token = None

        while True:
            response = await self.get_cycles(
                start=start, end=end, limit=25, next_token=next_token
            )

            records = response.get("records", [])
            all_records.extend(records)
            logger.debug(f"Fetched {len(records)} cycles, total so far: {len(all_records)}")

            next_token = response.get("nextToken") or response.get("next_token")
            if not next_token:
                break

        logger.info(f"Fetched {len(all_records)} total cycles")
        return all_records

    async def get_all_recovery(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        """Fetch all recovery records in date range."""
        all_records = []
        next_token = None

        while True:
            response = await self.get_recovery(
                start=start, end=end, limit=25, next_token=next_token
            )

            records = response.get("records", [])
            all_records.extend(records)
            logger.debug(f"Fetched {len(records)} recovery records, total so far: {len(all_records)}")

            next_token = response.get("nextToken") or response.get("next_token")
            if not next_token:
                break

        logger.info(f"Fetched {len(all_records)} total recovery records")
        return all_records

    async def get_all_sleep(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        """Fetch all sleep records in date range."""
        all_records = []
        next_token = None

        while True:
            response = await self.get_sleep(
                start=start, end=end, limit=25, next_token=next_token
            )

            records = response.get("records", [])
            all_records.extend(records)
            logger.debug(f"Fetched {len(records)} sleep records, total so far: {len(all_records)}")

            next_token = response.get("nextToken") or response.get("next_token")
            if not next_token:
                break

        logger.info(f"Fetched {len(all_records)} total sleep records")
        return all_records

    async def get_all_workouts(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        """Fetch all workout records in date range."""
        all_records = []
        next_token = None

        while True:
            response = await self.get_workouts(
                start=start, end=end, limit=25, next_token=next_token
            )

            records = response.get("records", [])
            all_records.extend(records)
            logger.debug(f"Fetched {len(records)} workout records, total so far: {len(all_records)}")

            next_token = response.get("nextToken") or response.get("next_token")
            if not next_token:
                break

        logger.info(f"Fetched {len(all_records)} total workout records")
        return all_records
