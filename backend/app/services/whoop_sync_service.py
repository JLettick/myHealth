"""
Whoop data synchronization service.

Handles fetching data from Whoop API and storing it in the database.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from app.core.exceptions import WhoopSyncError
from app.core.logging_config import get_logger
from app.services.supabase_client import SupabaseService, get_supabase_service
from app.services.whoop_client import WhoopAPIClient
from app.services.whoop_service import WhoopOAuthService, get_whoop_service

logger = get_logger(__name__)


class WhoopSyncService:
    """
    Service for syncing Whoop data to the database.

    Fetches data from Whoop API and upserts into local tables.
    """

    def __init__(
        self,
        supabase: Optional[SupabaseService] = None,
        whoop_service: Optional[WhoopOAuthService] = None,
    ):
        """
        Initialize sync service.

        Args:
            supabase: Supabase service instance
            whoop_service: Whoop OAuth service instance
        """
        self.supabase = supabase or get_supabase_service()
        self.whoop_service = whoop_service or get_whoop_service()

    async def sync_all(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict[str, int]:
        """
        Sync all Whoop data for a user.

        Args:
            user_id: Application user ID
            start_date: Start of sync range (default: 30 days ago)
            end_date: End of sync range (default: now)

        Returns:
            Dictionary with counts of synced records by type

        Raises:
            WhoopSyncError: If sync fails
        """
        logger.info(f"Starting full Whoop sync for user {user_id}")

        # Set default date range
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=30)

        logger.info(f"Sync date range: {start_date.isoformat()} to {end_date.isoformat()}")

        try:
            # Get valid access token
            logger.debug(f"Getting access token for user {user_id}")
            access_token = await self.whoop_service.get_valid_access_token(user_id)
            logger.debug(f"Got access token (length: {len(access_token)})")
            client = WhoopAPIClient(access_token)

            # Sync each data type
            cycles_count = await self._sync_cycles(user_id, client, start_date, end_date)
            recovery_count = await self._sync_recovery(user_id, client, start_date, end_date)
            sleep_count = await self._sync_sleep(user_id, client, start_date, end_date)
            workouts_count = await self._sync_workouts(user_id, client, start_date, end_date)

            # Update last sync timestamp
            await self.whoop_service.update_last_sync(user_id)

            result = {
                "cycles": cycles_count,
                "recovery": recovery_count,
                "sleep": sleep_count,
                "workouts": workouts_count,
            }

            logger.info(f"Whoop sync completed for user {user_id}: {result}")
            return result

        except Exception as e:
            logger.error(f"Whoop sync failed for user {user_id}: {e}")
            raise WhoopSyncError(
                message="Failed to sync Whoop data",
                details={"error": str(e)}
            )

    async def _sync_cycles(
        self,
        user_id: str,
        client: WhoopAPIClient,
        start: datetime,
        end: datetime,
    ) -> int:
        """Sync cycle data."""
        logger.debug(f"Syncing cycles for user {user_id}")

        cycles = await client.get_all_cycles(start=start, end=end)
        synced_count = 0

        for cycle in cycles:
            try:
                cycle_data = self._parse_cycle(user_id, cycle)
                self.supabase.admin_client.table("whoop_cycles").upsert(
                    cycle_data,
                    on_conflict="user_id,whoop_cycle_id"
                ).execute()
                synced_count += 1
            except Exception as e:
                logger.warning(f"Failed to sync cycle {cycle.get('id')}: {e}")

        return synced_count

    async def _sync_recovery(
        self,
        user_id: str,
        client: WhoopAPIClient,
        start: datetime,
        end: datetime,
    ) -> int:
        """Sync recovery data."""
        logger.debug(f"Syncing recovery for user {user_id}")

        recoveries = await client.get_all_recovery(start=start, end=end)
        synced_count = 0

        for recovery in recoveries:
            try:
                recovery_data = self._parse_recovery(user_id, recovery)
                self.supabase.admin_client.table("whoop_recovery").upsert(
                    recovery_data,
                    on_conflict="user_id,whoop_cycle_id"
                ).execute()
                synced_count += 1
            except Exception as e:
                logger.warning(f"Failed to sync recovery {recovery.get('cycle_id')}: {e}")

        return synced_count

    async def _sync_sleep(
        self,
        user_id: str,
        client: WhoopAPIClient,
        start: datetime,
        end: datetime,
    ) -> int:
        """Sync sleep data."""
        logger.debug(f"Syncing sleep for user {user_id}")

        sleeps = await client.get_all_sleep(start=start, end=end)
        synced_count = 0

        for sleep in sleeps:
            try:
                sleep_data = self._parse_sleep(user_id, sleep)
                self.supabase.admin_client.table("whoop_sleep").upsert(
                    sleep_data,
                    on_conflict="user_id,whoop_sleep_id"
                ).execute()
                synced_count += 1
            except Exception as e:
                logger.warning(f"Failed to sync sleep {sleep.get('id')}: {e}")

        return synced_count

    async def _sync_workouts(
        self,
        user_id: str,
        client: WhoopAPIClient,
        start: datetime,
        end: datetime,
    ) -> int:
        """Sync workout data."""
        logger.debug(f"Syncing workouts for user {user_id}")

        workouts = await client.get_all_workouts(start=start, end=end)
        synced_count = 0

        for workout in workouts:
            try:
                workout_data = self._parse_workout(user_id, workout)
                self.supabase.admin_client.table("whoop_workouts").upsert(
                    workout_data,
                    on_conflict="user_id,whoop_workout_id"
                ).execute()
                synced_count += 1
            except Exception as e:
                logger.warning(f"Failed to sync workout {workout.get('id')}: {e}")

        return synced_count

    def _parse_cycle(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Parse Whoop cycle API response into database format."""
        score = data.get("score", {})

        return {
            "user_id": user_id,
            "whoop_cycle_id": data["id"],
            "start_time": data["start"],
            "end_time": data.get("end"),
            "strain_score": score.get("strain"),
            "kilojoules": score.get("kilojoule"),
            "average_heart_rate": score.get("average_heart_rate"),
            "max_heart_rate": score.get("max_heart_rate"),
        }

    def _parse_recovery(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Parse Whoop recovery API response into database format."""
        score = data.get("score", {})

        return {
            "user_id": user_id,
            "whoop_cycle_id": data["cycle_id"],
            "recovery_score": score.get("recovery_score"),
            "resting_heart_rate": score.get("resting_heart_rate"),
            "hrv_rmssd_milli": score.get("hrv_rmssd_milli"),
            "spo2_percentage": score.get("spo2_percentage"),
            "skin_temp_celsius": score.get("skin_temp_celsius"),
        }

    def _parse_sleep(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Parse Whoop sleep API response into database format."""
        score = data.get("score", {})
        stage = score.get("stage_summary", {})

        return {
            "user_id": user_id,
            "whoop_sleep_id": data["id"],
            "whoop_cycle_id": data.get("cycle_id"),
            "start_time": data["start"],
            "end_time": data["end"],
            "is_nap": data.get("nap", False),
            "sleep_score": score.get("sleep_performance_percentage"),
            "total_in_bed_milli": stage.get("total_in_bed_time_milli"),
            "total_awake_milli": stage.get("total_awake_time_milli"),
            "total_light_sleep_milli": stage.get("total_light_sleep_time_milli"),
            "total_slow_wave_sleep_milli": stage.get("total_slow_wave_sleep_time_milli"),
            "total_rem_sleep_milli": stage.get("total_rem_sleep_time_milli"),
            "sleep_efficiency": score.get("sleep_efficiency_percentage"),
            "respiratory_rate": score.get("respiratory_rate"),
        }

    def _parse_workout(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Parse Whoop workout API response into database format."""
        score = data.get("score", {})
        zone = score.get("zone_duration", {})

        return {
            "user_id": user_id,
            "whoop_workout_id": data["id"],
            "whoop_cycle_id": data.get("cycle_id"),
            "start_time": data["start"],
            "end_time": data["end"],
            "sport_id": data.get("sport_id", 0),
            "sport_name": data.get("sport_name"),
            "strain_score": score.get("strain"),
            "kilojoules": score.get("kilojoule"),
            "average_heart_rate": score.get("average_heart_rate"),
            "max_heart_rate": score.get("max_heart_rate"),
            "distance_meter": score.get("distance_meter"),
            "altitude_gain_meter": score.get("altitude_gain_meter"),
            "altitude_change_meter": score.get("altitude_change_meter"),
            "zone_zero_milli": zone.get("zone_zero_milli"),
            "zone_one_milli": zone.get("zone_one_milli"),
            "zone_two_milli": zone.get("zone_two_milli"),
            "zone_three_milli": zone.get("zone_three_milli"),
            "zone_four_milli": zone.get("zone_four_milli"),
            "zone_five_milli": zone.get("zone_five_milli"),
        }

    async def get_dashboard_summary(self, user_id: str) -> dict[str, Any]:
        """
        Get summary data for dashboard display.

        Args:
            user_id: Application user ID

        Returns:
            Dashboard summary with latest metrics and 7-day averages
        """
        logger.debug(f"Getting dashboard summary for user {user_id}")

        # Get connection status
        connection = await self.whoop_service.get_connection(user_id)

        if not connection:
            return {
                "is_connected": False,
                "last_sync_at": None,
                "latest_recovery_score": None,
                "latest_strain_score": None,
                "latest_hrv": None,
                "latest_resting_hr": None,
                "latest_sleep_score": None,
                "latest_sleep_hours": None,
                "avg_recovery_7d": None,
                "avg_strain_7d": None,
                "avg_sleep_hours_7d": None,
                "total_workouts_7d": 0,
            }

        # Get latest cycle for strain (and to find matching recovery)
        latest_cycle = (
            self.supabase.admin_client.table("whoop_cycles")
            .select("*")
            .eq("user_id", user_id)
            .order("start_time", desc=True)
            .limit(1)
            .execute()
        )

        # Get recovery for the latest cycle (not by created_at, which can be stale)
        # Recovery is tied to a cycle, so we fetch the recovery for the most recent cycle
        latest_recovery_data: dict[str, Any] = {}
        if latest_cycle.data:
            latest_cycle_id = latest_cycle.data[0].get("whoop_cycle_id")
            if latest_cycle_id:
                latest_recovery = (
                    self.supabase.admin_client.table("whoop_recovery")
                    .select("*")
                    .eq("user_id", user_id)
                    .eq("whoop_cycle_id", latest_cycle_id)
                    .limit(1)
                    .execute()
                )
                if latest_recovery.data:
                    latest_recovery_data = latest_recovery.data[0]

        # Get latest sleep
        latest_sleep = (
            self.supabase.admin_client.table("whoop_sleep")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_nap", False)
            .order("start_time", desc=True)
            .limit(1)
            .execute()
        )

        # Get 7-day data for averages
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

        # Get cycles from last 7 days (includes cycle IDs for recovery lookup)
        cycles_7d = (
            self.supabase.admin_client.table("whoop_cycles")
            .select("whoop_cycle_id, strain_score")
            .eq("user_id", user_id)
            .gte("start_time", seven_days_ago)
            .execute()
        )

        # Get recovery records for cycles in the last 7 days (not by created_at)
        cycle_ids_7d = [c.get("whoop_cycle_id") for c in cycles_7d.data if c.get("whoop_cycle_id")]
        recovery_7d_data = []
        if cycle_ids_7d:
            recovery_7d = (
                self.supabase.admin_client.table("whoop_recovery")
                .select("recovery_score")
                .eq("user_id", user_id)
                .in_("whoop_cycle_id", cycle_ids_7d)
                .execute()
            )
            recovery_7d_data = recovery_7d.data

        sleep_7d = (
            self.supabase.admin_client.table("whoop_sleep")
            .select("total_in_bed_milli, total_awake_milli")
            .eq("user_id", user_id)
            .eq("is_nap", False)
            .gte("start_time", seven_days_ago)
            .execute()
        )

        workouts_7d = (
            self.supabase.admin_client.table("whoop_workouts")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .gte("start_time", seven_days_ago)
            .execute()
        )

        # Parse latest values
        cycle_data = latest_cycle.data[0] if latest_cycle.data else {}
        sleep_data = latest_sleep.data[0] if latest_sleep.data else {}

        # Calculate sleep hours
        latest_sleep_hours = None
        if sleep_data.get("total_in_bed_milli") and sleep_data.get("total_awake_milli"):
            sleep_milli = sleep_data["total_in_bed_milli"] - sleep_data["total_awake_milli"]
            latest_sleep_hours = round(sleep_milli / 3600000, 2)

        # Calculate 7-day averages
        avg_recovery = self._calculate_average(
            [r.get("recovery_score") for r in recovery_7d_data]
        )
        avg_strain = self._calculate_average(
            [c.get("strain_score") for c in cycles_7d.data]
        )

        # Calculate average sleep hours
        sleep_hours_list = []
        for s in sleep_7d.data:
            if s.get("total_in_bed_milli") and s.get("total_awake_milli"):
                hours = (s["total_in_bed_milli"] - s["total_awake_milli"]) / 3600000
                sleep_hours_list.append(hours)
        avg_sleep = round(sum(sleep_hours_list) / len(sleep_hours_list), 2) if sleep_hours_list else None

        return {
            "is_connected": True,
            "last_sync_at": connection.get("last_sync_at"),
            "latest_recovery_score": latest_recovery_data.get("recovery_score"),
            "latest_strain_score": cycle_data.get("strain_score"),
            "latest_hrv": latest_recovery_data.get("hrv_rmssd_milli"),
            "latest_resting_hr": latest_recovery_data.get("resting_heart_rate"),
            "latest_sleep_score": sleep_data.get("sleep_score"),
            "latest_sleep_hours": latest_sleep_hours,
            "avg_recovery_7d": avg_recovery,
            "avg_strain_7d": avg_strain,
            "avg_sleep_hours_7d": avg_sleep,
            "total_workouts_7d": workouts_7d.count or 0,
        }

    def _calculate_average(self, values: list) -> Optional[float]:
        """Calculate average of numeric values, ignoring None."""
        valid = [v for v in values if v is not None]
        if not valid:
            return None
        return round(sum(valid) / len(valid), 2)

    async def get_sleep_records(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 10,
        include_naps: bool = False,
    ) -> tuple[list[dict], int]:
        """Get paginated sleep records."""
        offset = (page - 1) * page_size

        query = (
            self.supabase.admin_client.table("whoop_sleep")
            .select("*", count="exact")
            .eq("user_id", user_id)
        )

        if not include_naps:
            query = query.eq("is_nap", False)

        response = (
            query
            .order("start_time", desc=True)
            .range(offset, offset + page_size - 1)
            .execute()
        )

        return response.data, response.count or 0

    async def get_workout_records(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[dict], int]:
        """Get paginated workout records."""
        offset = (page - 1) * page_size

        response = (
            self.supabase.admin_client.table("whoop_workouts")
            .select("*", count="exact")
            .eq("user_id", user_id)
            .order("start_time", desc=True)
            .range(offset, offset + page_size - 1)
            .execute()
        )

        return response.data, response.count or 0

    async def get_recovery_records(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[dict], int]:
        """
        Get paginated recovery records.

        Note: Currently orders by created_at (database insertion time).
        For proper chronological ordering, would need to join with cycles
        or add cycle_start_time column to recovery table.
        """
        offset = (page - 1) * page_size

        response = (
            self.supabase.admin_client.table("whoop_recovery")
            .select("*", count="exact")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + page_size - 1)
            .execute()
        )

        return response.data, response.count or 0


# Singleton instance
_sync_service: WhoopSyncService | None = None


def get_whoop_sync_service() -> WhoopSyncService:
    """Get the Whoop sync service singleton."""
    global _sync_service
    if _sync_service is None:
        _sync_service = WhoopSyncService()
    return _sync_service
