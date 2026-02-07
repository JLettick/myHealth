"""
Workout tracking service.

Handles:
- Exercise CRUD operations
- Workout session management
- Workout set logging
- Daily/weekly summaries
- Workout goals management
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from app.core.logging_config import get_logger
from app.services.supabase_client import SupabaseService, get_supabase_service

logger = get_logger(__name__)


class WorkoutService:
    """Service for workout tracking operations."""

    def __init__(self, supabase: Optional[SupabaseService] = None):
        self.supabase = supabase or get_supabase_service()

    # =========================================================================
    # EXERCISES CRUD
    # =========================================================================

    async def create_exercise(
        self, user_id: str, exercise_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a custom exercise for a user."""
        logger.info(f"Creating exercise for user {user_id}: {exercise_data.get('name')}")

        data = {
            "user_id": user_id,
            "is_verified": False,
            **exercise_data,
        }

        response = (
            self.supabase.admin_client.table("exercises").insert(data).execute()
        )

        return response.data[0] if response.data else None

    async def get_exercise(
        self, exercise_id: str, user_id: str
    ) -> Optional[dict[str, Any]]:
        """Get an exercise by ID (must be global or owned by user)."""
        response = (
            self.supabase.admin_client.table("exercises")
            .select("*")
            .eq("id", exercise_id)
            .execute()
        )

        if not response.data:
            return None

        exercise = response.data[0]
        # Check access: global exercise or owned by user
        if exercise["user_id"] is not None and exercise["user_id"] != user_id:
            return None

        return exercise

    async def update_exercise(
        self, exercise_id: str, user_id: str, update_data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Update a user's custom exercise."""
        response = (
            self.supabase.admin_client.table("exercises")
            .update(update_data)
            .eq("id", exercise_id)
            .eq("user_id", user_id)
            .execute()
        )

        return response.data[0] if response.data else None

    async def delete_exercise(self, exercise_id: str, user_id: str) -> bool:
        """Delete a user's custom exercise."""
        response = (
            self.supabase.admin_client.table("exercises")
            .delete()
            .eq("id", exercise_id)
            .eq("user_id", user_id)
            .execute()
        )

        return len(response.data) > 0

    async def search_exercises(
        self,
        user_id: str,
        query: str = "",
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[dict], int]:
        """Search exercises by name/category (global + user's custom)."""
        offset = (page - 1) * page_size

        # Build query
        q = (
            self.supabase.admin_client.table("exercises")
            .select("*", count="exact")
            .or_(f"user_id.is.null,user_id.eq.{user_id}")
        )

        if query:
            q = q.ilike("name", f"%{query}%")

        if category:
            q = q.eq("category", category)

        response = (
            q.order("is_verified", desc=True)
            .order("name")
            .range(offset, offset + page_size - 1)
            .execute()
        )

        return response.data, response.count or 0

    async def get_user_exercises(
        self, user_id: str, page: int = 1, page_size: int = 50
    ) -> tuple[list[dict], int]:
        """Get user's custom exercises."""
        offset = (page - 1) * page_size

        response = (
            self.supabase.admin_client.table("exercises")
            .select("*", count="exact")
            .eq("user_id", user_id)
            .order("name")
            .range(offset, offset + page_size - 1)
            .execute()
        )

        return response.data, response.count or 0

    # =========================================================================
    # WORKOUT SESSIONS CRUD
    # =========================================================================

    async def create_session(
        self, user_id: str, session_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a workout session."""
        logger.info(f"Creating workout session for user {user_id}")

        data = {
            "user_id": user_id,
            **session_data,
        }

        # Convert date/datetime to string
        if "session_date" in data and isinstance(data["session_date"], date):
            data["session_date"] = data["session_date"].isoformat()
        if "start_time" in data and isinstance(data["start_time"], datetime):
            data["start_time"] = data["start_time"].isoformat()
        if "end_time" in data and isinstance(data["end_time"], datetime):
            data["end_time"] = data["end_time"].isoformat()

        response = (
            self.supabase.admin_client.table("workout_sessions").insert(data).execute()
        )

        if response.data:
            return await self.get_session(response.data[0]["id"], user_id)

        return None

    async def get_session(
        self, session_id: str, user_id: str
    ) -> Optional[dict[str, Any]]:
        """Get a workout session with all sets."""
        response = (
            self.supabase.admin_client.table("workout_sessions")
            .select("*")
            .eq("id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            return None

        session = response.data[0]

        # Get sets for this session
        sets_response = (
            self.supabase.admin_client.table("workout_sets")
            .select("*, exercises(*)")
            .eq("session_id", session_id)
            .order("set_order")
            .execute()
        )

        sets = []
        for s in sets_response.data:
            s["exercise"] = s.pop("exercises", None)
            sets.append(s)

        session["sets"] = sets
        session["total_sets"] = len(sets)
        session["total_duration_minutes"] = self._compute_session_duration(session)

        return session

    async def update_session(
        self, session_id: str, user_id: str, update_data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Update a workout session."""
        # Convert date/datetime to string
        if "session_date" in update_data and isinstance(update_data["session_date"], date):
            update_data["session_date"] = update_data["session_date"].isoformat()
        if "start_time" in update_data and isinstance(update_data["start_time"], datetime):
            update_data["start_time"] = update_data["start_time"].isoformat()
        if "end_time" in update_data and isinstance(update_data["end_time"], datetime):
            update_data["end_time"] = update_data["end_time"].isoformat()

        response = (
            self.supabase.admin_client.table("workout_sessions")
            .update(update_data)
            .eq("id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        if response.data:
            return await self.get_session(session_id, user_id)
        return None

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a workout session (cascades to sets)."""
        response = (
            self.supabase.admin_client.table("workout_sessions")
            .delete()
            .eq("id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        return len(response.data) > 0

    async def get_sessions_by_date(
        self, user_id: str, session_date: date
    ) -> list[dict[str, Any]]:
        """Get all workout sessions for a specific date."""
        response = (
            self.supabase.admin_client.table("workout_sessions")
            .select("*")
            .eq("user_id", user_id)
            .eq("session_date", session_date.isoformat())
            .order("start_time")
            .execute()
        )

        sessions = []
        for session in response.data:
            # Get set count for each session
            sets_response = (
                self.supabase.admin_client.table("workout_sets")
                .select("id", count="exact")
                .eq("session_id", session["id"])
                .execute()
            )
            session["total_sets"] = sets_response.count or 0
            session["total_duration_minutes"] = self._compute_session_duration(session)
            sessions.append(session)

        return sessions

    async def get_sessions_by_date_range(
        self, user_id: str, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """Get all workout sessions for a date range."""
        response = (
            self.supabase.admin_client.table("workout_sessions")
            .select("*")
            .eq("user_id", user_id)
            .gte("session_date", start_date.isoformat())
            .lte("session_date", end_date.isoformat())
            .order("session_date", desc=True)
            .order("start_time")
            .execute()
        )

        sessions = []
        for session in response.data:
            sets_response = (
                self.supabase.admin_client.table("workout_sets")
                .select("id", count="exact")
                .eq("session_id", session["id"])
                .execute()
            )
            session["total_sets"] = sets_response.count or 0
            session["total_duration_minutes"] = self._compute_session_duration(session)
            sessions.append(session)

        return sessions

    # =========================================================================
    # WORKOUT SETS CRUD
    # =========================================================================

    async def create_set(
        self, user_id: str, session_id: str, set_data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Add a set to a workout session."""
        # Verify session belongs to user
        session = await self.get_session(session_id, user_id)
        if not session:
            return None

        logger.info(f"Creating workout set for session {session_id}")

        data = {
            "user_id": user_id,
            "session_id": session_id,
            **set_data,
        }

        # Convert Decimal to float
        for key in ["weight_kg", "rpe", "distance_meters", "elevation_gain_meters"]:
            if key in data and data[key] is not None:
                data[key] = float(data[key])

        response = (
            self.supabase.admin_client.table("workout_sets").insert(data).execute()
        )

        if response.data:
            return await self.get_set(response.data[0]["id"], user_id)
        return None

    async def get_set(self, set_id: str, user_id: str) -> Optional[dict[str, Any]]:
        """Get a workout set with exercise details."""
        response = (
            self.supabase.admin_client.table("workout_sets")
            .select("*, exercises(*)")
            .eq("id", set_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            return None

        workout_set = response.data[0]
        workout_set["exercise"] = workout_set.pop("exercises", None)
        return workout_set

    async def update_set(
        self, set_id: str, user_id: str, update_data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Update a workout set."""
        # Convert Decimal to float
        for key in ["weight_kg", "rpe", "distance_meters", "elevation_gain_meters"]:
            if key in update_data and update_data[key] is not None:
                update_data[key] = float(update_data[key])

        response = (
            self.supabase.admin_client.table("workout_sets")
            .update(update_data)
            .eq("id", set_id)
            .eq("user_id", user_id)
            .execute()
        )

        if response.data:
            return await self.get_set(set_id, user_id)
        return None

    async def delete_set(self, set_id: str, user_id: str) -> bool:
        """Delete a workout set."""
        response = (
            self.supabase.admin_client.table("workout_sets")
            .delete()
            .eq("id", set_id)
            .eq("user_id", user_id)
            .execute()
        )

        return len(response.data) > 0

    # =========================================================================
    # SUMMARIES
    # =========================================================================

    async def get_daily_summary(
        self, user_id: str, summary_date: date
    ) -> dict[str, Any]:
        """Get daily workout summary."""
        sessions = await self.get_sessions_by_date(user_id, summary_date)
        goals = await self.get_goals(user_id)

        # Get all sets for the day with exercise details
        total_sets = 0
        total_duration = 0
        total_volume = Decimal("0")
        total_distance = Decimal("0")
        exercise_summaries = {}

        for session in sessions:
            full_session = await self.get_session(session["id"], user_id)
            if not full_session:
                continue

            total_sets += len(full_session.get("sets", []))
            if full_session.get("total_duration_minutes"):
                total_duration += full_session["total_duration_minutes"]

            for workout_set in full_session.get("sets", []):
                exercise = workout_set.get("exercise", {}) or {}
                exercise_id = workout_set.get("exercise_id")

                if exercise_id not in exercise_summaries:
                    exercise_summaries[exercise_id] = {
                        "exercise_id": exercise_id,
                        "exercise_name": exercise.get("name", "Unknown"),
                        "category": exercise.get("category", "other"),
                        "total_sets": 0,
                        "total_reps": 0,
                        "max_weight_kg": None,
                        "total_volume_kg": Decimal("0"),
                        "total_duration_seconds": 0,
                        "total_distance_meters": Decimal("0"),
                    }

                summary = exercise_summaries[exercise_id]
                summary["total_sets"] += 1

                # Strength metrics
                if workout_set.get("reps"):
                    summary["total_reps"] += workout_set["reps"]

                if workout_set.get("weight_kg"):
                    weight = Decimal(str(workout_set["weight_kg"]))
                    if summary["max_weight_kg"] is None or weight > summary["max_weight_kg"]:
                        summary["max_weight_kg"] = weight
                    if workout_set.get("reps"):
                        volume = weight * workout_set["reps"]
                        summary["total_volume_kg"] += volume
                        total_volume += volume

                # Cardio metrics
                if workout_set.get("duration_seconds"):
                    summary["total_duration_seconds"] += workout_set["duration_seconds"]

                if workout_set.get("distance_meters"):
                    distance = Decimal(str(workout_set["distance_meters"]))
                    summary["total_distance_meters"] += distance
                    total_distance += distance

        return {
            "date": summary_date,
            "sessions": sessions,
            "exercises": list(exercise_summaries.values()),
            "total_sessions": len(sessions),
            "total_sets": total_sets,
            "total_duration_minutes": total_duration,
            "total_volume_kg": float(total_volume) if total_volume else None,
            "total_distance_meters": float(total_distance) if total_distance else None,
            "workouts_per_week_target": goals.get("workouts_per_week_target") if goals else None,
            "minutes_per_week_target": goals.get("minutes_per_week_target") if goals else None,
        }

    async def get_weekly_summary(
        self, user_id: str, start_date: date
    ) -> dict[str, Any]:
        """Get weekly workout summary."""
        end_date = start_date + timedelta(days=6)
        goals = await self.get_goals(user_id)

        daily_summaries = []
        total_sessions = 0
        total_duration = 0
        total_volume = Decimal("0")
        total_distance = Decimal("0")

        for i in range(7):
            day = start_date + timedelta(days=i)
            summary = await self.get_daily_summary(user_id, day)
            daily_summaries.append(summary)

            total_sessions += summary["total_sessions"]
            total_duration += summary["total_duration_minutes"]
            if summary.get("total_volume_kg"):
                total_volume += Decimal(str(summary["total_volume_kg"]))
            if summary.get("total_distance_meters"):
                total_distance += Decimal(str(summary["total_distance_meters"]))

        return {
            "start_date": start_date,
            "end_date": end_date,
            "daily_summaries": daily_summaries,
            "total_sessions": total_sessions,
            "total_duration_minutes": total_duration,
            "total_volume_kg": float(total_volume) if total_volume else None,
            "total_distance_meters": float(total_distance) if total_distance else None,
            "workouts_per_week_target": goals.get("workouts_per_week_target") if goals else None,
            "workouts_completed": total_sessions,
            "minutes_per_week_target": goals.get("minutes_per_week_target") if goals else None,
            "minutes_completed": total_duration,
        }

    # =========================================================================
    # WORKOUT GOALS
    # =========================================================================

    async def get_goals(self, user_id: str) -> Optional[dict[str, Any]]:
        """Get user's workout goals."""
        response = (
            self.supabase.admin_client.table("workout_goals")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )

        return response.data[0] if response.data else None

    async def upsert_goals(
        self, user_id: str, goals_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create or update user's workout goals."""
        data = {
            "user_id": user_id,
            "is_active": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            **goals_data,
        }

        response = (
            self.supabase.admin_client.table("workout_goals")
            .upsert(data, on_conflict="user_id")
            .execute()
        )

        return response.data[0] if response.data else None

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _compute_session_duration(self, session: dict[str, Any]) -> Optional[int]:
        """Compute session duration in minutes from start/end times."""
        start = session.get("start_time")
        end = session.get("end_time")

        if not start or not end:
            return None

        try:
            if isinstance(start, str):
                start = datetime.fromisoformat(start.replace("Z", "+00:00"))
            if isinstance(end, str):
                end = datetime.fromisoformat(end.replace("Z", "+00:00"))

            duration = (end - start).total_seconds() / 60
            return int(duration) if duration > 0 else None
        except (ValueError, TypeError):
            return None


# Singleton instance
_workout_service: Optional[WorkoutService] = None


def get_workout_service() -> WorkoutService:
    """Get the Workout service singleton."""
    global _workout_service
    if _workout_service is None:
        _workout_service = WorkoutService()
    return _workout_service
