"""
HTTP client for Garmin Connect API.

Handles authenticated requests, rate limiting, and pagination.
"""

import logging
from datetime import date, timedelta
from typing import Optional, List, Dict, Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GarminAPIError(Exception):
    """Base Garmin API error."""
    pass


class GarminAuthError(GarminAPIError):
    """Authentication error (401)."""
    pass


class GarminRateLimitError(GarminAPIError):
    """Rate limit exceeded (429)."""
    pass


class GarminClient:
    """
    Client for Garmin Connect API.

    Handles authentication, rate limiting, and API requests.
    """

    def __init__(self, access_token: str):
        """
        Initialize the Garmin client.

        Args:
            access_token: OAuth access token for authentication.
        """
        self.access_token = access_token
        self.base_url = settings.garmin_api_base_url
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Make an authenticated request to the Garmin API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Optional query parameters

        Returns:
            Parsed JSON response

        Raises:
            GarminAuthError: If authentication fails (401)
            GarminRateLimitError: If rate limit is exceeded (429)
            GarminAPIError: For other API errors
        """
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method,
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=30.0,
                )

                if response.status_code == 401:
                    raise GarminAuthError("Invalid or expired token")
                elif response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise GarminRateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after} seconds"
                    )

                response.raise_for_status()

                # Handle empty responses
                if not response.content:
                    return {}

                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(f"Garmin API error: {e.response.status_code} - {e.response.text}")
                raise GarminAPIError(f"API request failed: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"Garmin request error: {e}")
                raise GarminAPIError(f"Request failed: {str(e)}")

    async def get_user_profile(self) -> Dict[str, Any]:
        """
        Get the authenticated user's profile.

        Returns:
            User profile data including userId.
        """
        return await self._request("GET", "/userprofile-service/userprofile")

    async def get_activities(
        self,
        start_date: date,
        end_date: date,
        limit: int = 25,
        start: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get activities within a date range.

        Args:
            start_date: Start date for the query
            end_date: End date for the query
            limit: Maximum number of results per page
            start: Offset for pagination

        Returns:
            List of activity dictionaries
        """
        result = await self._request(
            "GET",
            "/activitylist-service/activities",
            params={
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "limit": limit,
                "start": start,
            },
        )
        return result if isinstance(result, list) else []

    async def get_all_activities(
        self,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """
        Get all activities with automatic pagination.

        Args:
            start_date: Start date for the query
            end_date: End date for the query

        Returns:
            List of all activity dictionaries
        """
        all_activities = []
        start = 0
        limit = 25

        while True:
            activities = await self.get_activities(start_date, end_date, limit, start)
            if not activities:
                break
            all_activities.extend(activities)
            if len(activities) < limit:
                break
            start += limit

        return all_activities

    async def get_sleep(
        self,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """
        Get sleep data within a date range.

        Args:
            start_date: Start date for the query
            end_date: End date for the query

        Returns:
            List of sleep record dictionaries
        """
        result = await self._request(
            "GET",
            "/wellness-service/wellness/dailySleep",
            params={
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
            },
        )
        return result if isinstance(result, list) else []

    async def get_heart_rate(
        self,
        target_date: date,
    ) -> Dict[str, Any]:
        """
        Get heart rate data for a specific date.

        Args:
            target_date: The date to get heart rate data for

        Returns:
            Heart rate data dictionary
        """
        return await self._request(
            "GET",
            f"/wellness-service/wellness/dailyHeartRate/{target_date.isoformat()}",
        )

    async def get_daily_summary(
        self,
        target_date: date,
    ) -> Dict[str, Any]:
        """
        Get daily summary (steps, calories, etc.) for a specific date.

        Args:
            target_date: The date to get summary for

        Returns:
            Daily summary data dictionary
        """
        return await self._request(
            "GET",
            f"/usersummary-service/usersummary/daily/{target_date.isoformat()}",
        )

    async def get_daily_summaries(
        self,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """
        Get daily summaries for a date range.

        Args:
            start_date: Start date for the query
            end_date: End date for the query

        Returns:
            List of daily summary dictionaries
        """
        summaries = []
        current = start_date

        while current <= end_date:
            try:
                summary = await self.get_daily_summary(current)
                if summary:
                    summaries.append(summary)
            except GarminAPIError:
                # Skip dates with no data
                pass
            current = current + timedelta(days=1)

        return summaries

    async def get_hrv(
        self,
        target_date: date,
    ) -> Dict[str, Any]:
        """
        Get HRV (Heart Rate Variability) data for a specific date.

        Args:
            target_date: The date to get HRV data for

        Returns:
            HRV data dictionary
        """
        return await self._request(
            "GET",
            f"/hrv-service/hrv/{target_date.isoformat()}",
        )
