"""
Service for synchronizing Garmin data.

Handles fetching data from Garmin API and storing in the database.
"""

import logging
from datetime import datetime, date, timezone, timedelta
from typing import Dict, Any, List, Optional

from app.services.supabase_client import get_supabase_service
from app.services.garmin_service import GarminService
from app.services.garmin_client import GarminClient, GarminAPIError

logger = logging.getLogger(__name__)


class GarminSyncService:
    """Service for syncing Garmin data to the database."""

    def __init__(self):
        self.supabase = get_supabase_service()
        self.garmin_service = GarminService()

    async def sync_all(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, int]:
        """
        Sync all Garmin data for a user.

        Args:
            user_id: The user's ID.
            start_date: Start date for sync (default: 30 days ago).
            end_date: End date for sync (default: today).

        Returns:
            Dictionary with counts of synced records by type.

        Raises:
            ValueError: If no valid Garmin connection exists.
        """
        # Default to last 30 days
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        access_token = await self.garmin_service.get_valid_access_token(user_id)
        if not access_token:
            raise ValueError("No valid Garmin connection")

        client = GarminClient(access_token)

        logger.info(f"Starting Garmin sync for user {user_id} from {start_date} to {end_date}")

        # Sync each data type
        activities_count = await self._sync_activities(user_id, client, start_date, end_date)
        sleep_count = await self._sync_sleep(user_id, client, start_date, end_date)
        hr_count = await self._sync_heart_rate(user_id, client, start_date, end_date)
        daily_count = await self._sync_daily_stats(user_id, client, start_date, end_date)

        # Update last sync timestamp
        self.garmin_service.update_last_sync(user_id)

        logger.info(
            f"Garmin sync complete for user {user_id}: "
            f"activities={activities_count}, sleep={sleep_count}, "
            f"hr={hr_count}, daily={daily_count}"
        )

        return {
            "activities_synced": activities_count,
            "sleep_synced": sleep_count,
            "heart_rate_synced": hr_count,
            "daily_stats_synced": daily_count,
        }

    async def _sync_activities(
        self,
        user_id: str,
        client: GarminClient,
        start_date: date,
        end_date: date,
    ) -> int:
        """Sync activities data."""
        try:
            activities = await client.get_all_activities(start_date, end_date)
            count = 0

            for activity in activities:
                parsed = self._parse_activity(user_id, activity)
                self.supabase.admin_client.table("garmin_activities").upsert(
                    parsed,
                    on_conflict="user_id,garmin_activity_id",
                ).execute()
                count += 1

            return count
        except GarminAPIError as e:
            logger.warning(f"Failed to sync activities: {e}")
            return 0

    async def _sync_sleep(
        self,
        user_id: str,
        client: GarminClient,
        start_date: date,
        end_date: date,
    ) -> int:
        """Sync sleep data."""
        try:
            sleep_records = await client.get_sleep(start_date, end_date)
            count = 0

            for record in sleep_records:
                parsed = self._parse_sleep(user_id, record)
                if parsed.get("garmin_sleep_id"):  # Only insert if we have a valid ID
                    self.supabase.admin_client.table("garmin_sleep").upsert(
                        parsed,
                        on_conflict="user_id,garmin_sleep_id",
                    ).execute()
                    count += 1

            return count
        except GarminAPIError as e:
            logger.warning(f"Failed to sync sleep: {e}")
            return 0

    async def _sync_heart_rate(
        self,
        user_id: str,
        client: GarminClient,
        start_date: date,
        end_date: date,
    ) -> int:
        """Sync heart rate data."""
        count = 0
        current = start_date

        while current <= end_date:
            try:
                hr_data = await client.get_heart_rate(current)
                if hr_data:
                    parsed = self._parse_heart_rate(user_id, current, hr_data)
                    self.supabase.admin_client.table("garmin_heart_rate").upsert(
                        parsed,
                        on_conflict="user_id,date",
                    ).execute()
                    count += 1
            except GarminAPIError:
                pass  # Skip dates with no data
            current = current + timedelta(days=1)

        return count

    async def _sync_daily_stats(
        self,
        user_id: str,
        client: GarminClient,
        start_date: date,
        end_date: date,
    ) -> int:
        """Sync daily statistics."""
        count = 0
        current = start_date

        while current <= end_date:
            try:
                daily = await client.get_daily_summary(current)
                if daily:
                    parsed = self._parse_daily_stats(user_id, current, daily)
                    self.supabase.admin_client.table("garmin_daily_stats").upsert(
                        parsed,
                        on_conflict="user_id,date",
                    ).execute()
                    count += 1
            except GarminAPIError:
                pass  # Skip dates with no data
            current = current + timedelta(days=1)

        return count

    def _parse_activity(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse activity data from Garmin API format."""
        return {
            "user_id": user_id,
            "garmin_activity_id": str(data.get("activityId", "")),
            "activity_type": data.get("activityType", {}).get("typeKey", "unknown"),
            "activity_name": data.get("activityName"),
            "start_time": data.get("startTimeLocal"),
            "end_time": data.get("endTimeLocal"),
            "duration_seconds": data.get("duration"),
            "distance_meters": data.get("distance"),
            "calories": data.get("calories"),
            "average_hr": data.get("averageHR"),
            "max_hr": data.get("maxHR"),
            "average_speed": data.get("averageSpeed"),
            "max_speed": data.get("maxSpeed"),
            "elevation_gain_meters": data.get("elevationGain"),
        }

    def _parse_sleep(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse sleep data from Garmin API format."""
        sleep_id = data.get("sleepId") or data.get("id") or data.get("calendarDate")
        return {
            "user_id": user_id,
            "garmin_sleep_id": str(sleep_id) if sleep_id else "",
            "start_time": data.get("sleepStartTimestampLocal") or data.get("sleepTimeSeconds"),
            "end_time": data.get("sleepEndTimestampLocal") or data.get("sleepEndTimestampGMT"),
            "total_sleep_seconds": data.get("sleepTimeSeconds"),
            "deep_sleep_seconds": data.get("deepSleepSeconds"),
            "light_sleep_seconds": data.get("lightSleepSeconds"),
            "rem_sleep_seconds": data.get("remSleepSeconds"),
            "awake_seconds": data.get("awakeSleepSeconds"),
            "sleep_score": data.get("sleepScores", {}).get("overall") if isinstance(data.get("sleepScores"), dict) else data.get("sleepScores"),
            "sleep_quality": data.get("sleepScores", {}).get("qualityLevel") if isinstance(data.get("sleepScores"), dict) else None,
        }

    def _parse_heart_rate(
        self,
        user_id: str,
        record_date: date,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse heart rate data from Garmin API format."""
        return {
            "user_id": user_id,
            "date": record_date.isoformat(),
            "resting_hr": data.get("restingHeartRate"),
            "max_hr": data.get("maxHeartRate"),
            "min_hr": data.get("minHeartRate"),
            "average_hr": data.get("averageHeartRate"),
            "hrv_value": data.get("hrvValue"),
        }

    def _parse_daily_stats(
        self,
        user_id: str,
        record_date: date,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse daily stats from Garmin API format."""
        # Calculate active minutes from moderate and vigorous intensity
        moderate_mins = data.get("moderateIntensityMinutes", 0) or 0
        vigorous_mins = data.get("vigorousIntensityMinutes", 0) or 0
        active_minutes = moderate_mins + vigorous_mins

        # Calculate sedentary minutes from seconds
        sedentary_seconds = data.get("sedentarySeconds", 0) or 0
        sedentary_minutes = sedentary_seconds // 60

        return {
            "user_id": user_id,
            "date": record_date.isoformat(),
            "total_steps": data.get("totalSteps"),
            "distance_meters": data.get("totalDistanceMeters"),
            "calories_burned": data.get("totalKilocalories"),
            "active_calories": data.get("activeKilocalories"),
            "active_minutes": active_minutes,
            "sedentary_minutes": sedentary_minutes,
            "floors_climbed": data.get("floorsAscended"),
            "intensity_minutes": data.get("intensityMinutes"),
            "stress_level": data.get("averageStressLevel"),
            "body_battery_high": data.get("bodyBatteryChargedValue"),
            "body_battery_low": data.get("bodyBatteryDrainedValue"),
        }

    def get_dashboard_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get dashboard summary for a user.

        Args:
            user_id: The user's ID.

        Returns:
            Dashboard summary with latest and aggregated metrics.
        """
        connection = self.garmin_service.get_connection(user_id)
        if not connection:
            return {
                "is_connected": False,
                "last_sync_at": None,
            }

        # Get latest data
        today = date.today()
        week_ago = today - timedelta(days=7)

        # Helper to safely query
        def safe_query_single(table: str, order_col: str) -> Optional[Dict[str, Any]]:
            try:
                result = (
                    self.supabase.admin_client.table(table)
                    .select("*")
                    .eq("user_id", user_id)
                    .order(order_col, desc=True)
                    .limit(1)
                    .execute()
                )
                return result.data[0] if result.data else None
            except Exception as e:
                logger.warning(f"Failed to query {table}: {e}")
                return None

        def safe_query_range(table: str, date_col: str) -> List[Dict[str, Any]]:
            try:
                result = (
                    self.supabase.admin_client.table(table)
                    .select("*")
                    .eq("user_id", user_id)
                    .gte(date_col, week_ago.isoformat())
                    .execute()
                )
                return result.data or []
            except Exception as e:
                logger.warning(f"Failed to query {table}: {e}")
                return []

        # Latest metrics
        latest_daily = safe_query_single("garmin_daily_stats", "date")
        latest_hr = safe_query_single("garmin_heart_rate", "date")
        latest_sleep = safe_query_single("garmin_sleep", "start_time")

        # 7-day aggregates
        daily_stats_7d = safe_query_range("garmin_daily_stats", "date")
        hr_7d = safe_query_range("garmin_heart_rate", "date")
        sleep_7d = safe_query_range("garmin_sleep", "start_time")
        activities_7d = safe_query_range("garmin_activities", "start_time")

        # Calculate averages
        avg_resting_hr = None
        if hr_7d:
            hrs = [r["resting_hr"] for r in hr_7d if r.get("resting_hr")]
            avg_resting_hr = sum(hrs) / len(hrs) if hrs else None

        avg_steps = None
        total_active_mins = 0
        if daily_stats_7d:
            steps = [r["total_steps"] for r in daily_stats_7d if r.get("total_steps")]
            avg_steps = sum(steps) / len(steps) if steps else None
            total_active_mins = sum(
                r.get("active_minutes", 0) or 0 for r in daily_stats_7d
            )

        avg_sleep_hours = None
        if sleep_7d:
            sleep_secs = [
                r["total_sleep_seconds"] for r in sleep_7d
                if r.get("total_sleep_seconds")
            ]
            avg_sleep_hours = sum(sleep_secs) / len(sleep_secs) / 3600 if sleep_secs else None

        return {
            "is_connected": True,
            "last_sync_at": connection.get("last_sync_at"),

            # Latest metrics
            "latest_resting_hr": latest_hr.get("resting_hr") if latest_hr else None,
            "latest_hrv": latest_hr.get("hrv_value") if latest_hr else None,
            "latest_sleep_score": latest_sleep.get("sleep_score") if latest_sleep else None,
            "latest_sleep_hours": (
                latest_sleep["total_sleep_seconds"] / 3600
                if latest_sleep and latest_sleep.get("total_sleep_seconds")
                else None
            ),
            "latest_steps": latest_daily.get("total_steps") if latest_daily else None,
            "latest_calories": latest_daily.get("calories_burned") if latest_daily else None,
            "latest_active_minutes": latest_daily.get("active_minutes") if latest_daily else None,
            "latest_body_battery": latest_daily.get("body_battery_high") if latest_daily else None,

            # 7-day aggregates
            "avg_resting_hr_7d": avg_resting_hr,
            "avg_sleep_hours_7d": avg_sleep_hours,
            "avg_steps_7d": avg_steps,
            "total_activities_7d": len(activities_7d),
            "total_active_minutes_7d": total_active_mins,
        }
