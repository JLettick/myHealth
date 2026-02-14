"""
Workout tracking service.

Handles:
- Exercise CRUD operations
- Workout session management
- Workout set logging
- Daily/weekly summaries
- Workout goals management
"""

import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from app.core.logging_config import get_logger
from app.services.supabase_client import SupabaseService, get_supabase_service

# Regex to strip XML/HTML tags from exercise names
_TAG_RE = re.compile(r"<[^>]+>")

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
        # Sanitize name: strip XML/HTML tags and collapse whitespace
        if "name" in exercise_data:
            name = _TAG_RE.sub("", exercise_data["name"]).strip()
            name = re.sub(r"\s+", " ", name)
            exercise_data["name"] = name

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
        if "name" in update_data:
            name = _TAG_RE.sub("", update_data["name"]).strip()
            name = re.sub(r"\s+", " ", name)
            update_data["name"] = name

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
        """Search exercises by name/category (global + user's custom).

        Results are sorted with user's custom exercises first, then verified
        global exercises, both alphabetical by name.
        """
        offset = (page - 1) * page_size

        # Fetch user's custom exercises first
        user_q = (
            self.supabase.admin_client.table("exercises")
            .select("*", count="exact")
            .eq("user_id", user_id)
        )
        if query:
            user_q = user_q.ilike("name", f"%{query}%")
        if category:
            user_q = user_q.eq("category", category)
        user_response = user_q.order("name").execute()

        user_exercises = user_response.data or []
        user_count = user_response.count or 0

        # Fetch global exercises
        global_q = (
            self.supabase.admin_client.table("exercises")
            .select("*", count="exact")
            .is_("user_id", "null")
        )
        if query:
            global_q = global_q.ilike("name", f"%{query}%")
        if category:
            global_q = global_q.eq("category", category)
        global_response = global_q.order("name").execute()

        global_exercises = global_response.data or []
        global_count = global_response.count or 0

        # Combine: user's custom first, then global
        all_exercises = user_exercises + global_exercises
        total = user_count + global_count

        # Apply pagination
        paginated = all_exercises[offset:offset + page_size]

        return paginated, total

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

        if not response.data:
            return []

        session_ids = [s["id"] for s in response.data]

        # Fetch all sets for all sessions in one query to get counts
        sets_response = (
            self.supabase.admin_client.table("workout_sets")
            .select("session_id")
            .in_("session_id", session_ids)
            .execute()
        )

        # Count sets per session
        set_counts: dict[str, int] = {}
        for s in sets_response.data:
            sid = s["session_id"]
            set_counts[sid] = set_counts.get(sid, 0) + 1

        sessions = []
        for session in response.data:
            session["total_sets"] = set_counts.get(session["id"], 0)
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

        if not response.data:
            return []

        session_ids = [s["id"] for s in response.data]

        # Fetch all sets for all sessions in one query to get counts
        sets_response = (
            self.supabase.admin_client.table("workout_sets")
            .select("session_id")
            .in_("session_id", session_ids)
            .execute()
        )

        # Count sets per session
        set_counts: dict[str, int] = {}
        for s in sets_response.data:
            sid = s["session_id"]
            set_counts[sid] = set_counts.get(sid, 0) + 1

        sessions = []
        for session in response.data:
            session["total_sets"] = set_counts.get(session["id"], 0)
            session["total_duration_minutes"] = self._compute_session_duration(session)
            sessions.append(session)

        return sessions

    # =========================================================================
    # WORKOUT SETS CRUD
    # =========================================================================

    async def create_set(
        self, user_id: str, session_id: str, set_data: dict[str, Any],
        skip_ownership_check: bool = False,
    ) -> Optional[dict[str, Any]]:
        """Add a set to a workout session."""
        if not skip_ownership_check:
            # Lightweight ownership check — just verify session exists for this user
            check_response = (
                self.supabase.admin_client.table("workout_sessions")
                .select("id")
                .eq("id", session_id)
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            if not check_response.data:
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

        total_sets = 0
        total_duration = 0
        total_volume = Decimal("0")
        total_distance = Decimal("0")
        exercise_summaries = {}

        if sessions:
            session_ids = [s["id"] for s in sessions]

            # Fetch all sets for all sessions in one query with exercise details
            all_sets_response = (
                self.supabase.admin_client.table("workout_sets")
                .select("*, exercises(*)")
                .in_("session_id", session_ids)
                .order("set_order")
                .execute()
            )

            # Group sets by session_id
            sets_by_session: dict[str, list] = {}
            for s in all_sets_response.data:
                s["exercise"] = s.pop("exercises", None)
                sid = s["session_id"]
                if sid not in sets_by_session:
                    sets_by_session[sid] = []
                sets_by_session[sid].append(s)

            for session in sessions:
                session_sets = sets_by_session.get(session["id"], [])
                total_sets += len(session_sets)
                if session.get("total_duration_minutes"):
                    total_duration += session["total_duration_minutes"]

                for workout_set in session_sets:
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
    # ANALYTICS
    # =========================================================================

    async def get_logged_exercises(
        self, user_id: str, set_type: Optional[str] = None, query: str = ""
    ) -> list[dict[str, Any]]:
        """Get exercises the user has actually logged sets for.

        Returns exercise records (with id, name, category) for exercises
        that appear in the user's workout_sets, optionally filtered by
        set_type ('strength' or 'cardio') and name search.
        """
        # 1. Get distinct exercise_ids from user's sets
        q = (
            self.supabase.admin_client.table("workout_sets")
            .select("exercise_id")
            .eq("user_id", user_id)
        )
        if set_type:
            q = q.eq("set_type", set_type)

        sets_response = q.execute()

        if not sets_response.data:
            return []

        # Deduplicate exercise_ids
        exercise_ids = list({s["exercise_id"] for s in sets_response.data})

        # 2. Fetch those exercises
        ex_q = (
            self.supabase.admin_client.table("exercises")
            .select("*")
            .in_("id", exercise_ids)
        )
        if query:
            ex_q = ex_q.ilike("name", f"%{query}%")

        exercises_response = ex_q.order("name").execute()

        return exercises_response.data or []

    async def get_exercise_history(
        self, user_id: str, exercise_id: str, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """Get exercise performance history over a date range.

        Returns per-date aggregations: max_weight, total_volume, total_reps, avg_rpe, total_sets.
        """
        # 1. Fetch sessions in range → get session IDs + date map
        sessions_response = (
            self.supabase.admin_client.table("workout_sessions")
            .select("id, session_date")
            .eq("user_id", user_id)
            .gte("session_date", start_date.isoformat())
            .lte("session_date", end_date.isoformat())
            .execute()
        )

        if not sessions_response.data:
            return []

        session_ids = [s["id"] for s in sessions_response.data]
        session_date_map = {s["id"]: s["session_date"] for s in sessions_response.data}

        # 2. Fetch sets for this exercise in those sessions
        sets_response = (
            self.supabase.admin_client.table("workout_sets")
            .select("session_id, weight_kg, reps, rpe")
            .in_("session_id", session_ids)
            .eq("exercise_id", exercise_id)
            .execute()
        )

        if not sets_response.data:
            return []

        # 3. Group by date and aggregate
        date_data: dict[str, dict] = {}
        for s in sets_response.data:
            d = session_date_map[s["session_id"]]
            if d not in date_data:
                date_data[d] = {
                    "date": d,
                    "max_weight_kg": None,
                    "total_volume_kg": 0.0,
                    "total_reps": 0,
                    "rpe_sum": 0.0,
                    "rpe_count": 0,
                    "total_sets": 0,
                }
            agg = date_data[d]
            agg["total_sets"] += 1

            weight = float(s["weight_kg"]) if s.get("weight_kg") is not None else None
            reps = s.get("reps") or 0

            if weight is not None:
                if agg["max_weight_kg"] is None or weight > agg["max_weight_kg"]:
                    agg["max_weight_kg"] = weight
                if reps > 0:
                    agg["total_volume_kg"] += weight * reps

            agg["total_reps"] += reps

            if s.get("rpe") is not None:
                agg["rpe_sum"] += float(s["rpe"])
                agg["rpe_count"] += 1

        # 4. Finalize and sort
        result = []
        for d in sorted(date_data.keys()):
            agg = date_data[d]
            result.append({
                "date": agg["date"],
                "max_weight_kg": agg["max_weight_kg"],
                "total_volume_kg": agg["total_volume_kg"] if agg["total_volume_kg"] > 0 else None,
                "total_reps": agg["total_reps"],
                "avg_rpe": round(agg["rpe_sum"] / agg["rpe_count"], 1) if agg["rpe_count"] > 0 else None,
                "total_sets": agg["total_sets"],
            })

        return result

    async def get_cardio_history(
        self, user_id: str, exercise_id: str, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """Get cardio exercise history over a date range.

        Returns per-date aggregations: distance, duration, pace, heart rate, calories.
        """
        # 1. Fetch sessions in range
        sessions_response = (
            self.supabase.admin_client.table("workout_sessions")
            .select("id, session_date")
            .eq("user_id", user_id)
            .gte("session_date", start_date.isoformat())
            .lte("session_date", end_date.isoformat())
            .execute()
        )

        if not sessions_response.data:
            return []

        session_ids = [s["id"] for s in sessions_response.data]
        session_date_map = {s["id"]: s["session_date"] for s in sessions_response.data}

        # 2. Fetch cardio sets for this exercise
        sets_response = (
            self.supabase.admin_client.table("workout_sets")
            .select("session_id, distance_meters, duration_seconds, avg_heart_rate, calories_burned")
            .in_("session_id", session_ids)
            .eq("exercise_id", exercise_id)
            .eq("set_type", "cardio")
            .execute()
        )

        if not sets_response.data:
            return []

        # 3. Group by date and aggregate
        date_data: dict[str, dict] = {}
        for s in sets_response.data:
            d = session_date_map[s["session_id"]]
            if d not in date_data:
                date_data[d] = {
                    "date": d,
                    "total_distance_meters": 0.0,
                    "total_duration_seconds": 0,
                    "hr_weighted_sum": 0.0,
                    "hr_duration_sum": 0,
                    "total_calories": 0,
                    "total_sets": 0,
                }
            agg = date_data[d]
            agg["total_sets"] += 1

            if s.get("distance_meters") is not None:
                agg["total_distance_meters"] += float(s["distance_meters"])
            if s.get("duration_seconds") is not None:
                agg["total_duration_seconds"] += s["duration_seconds"]
                # Weighted HR average
                if s.get("avg_heart_rate") is not None:
                    agg["hr_weighted_sum"] += s["avg_heart_rate"] * s["duration_seconds"]
                    agg["hr_duration_sum"] += s["duration_seconds"]
            if s.get("calories_burned") is not None:
                agg["total_calories"] += s["calories_burned"]

        # 4. Finalize and sort
        result = []
        for d in sorted(date_data.keys()):
            agg = date_data[d]
            # Compute average pace: total_duration / (total_distance / 1000)
            avg_pace = None
            if agg["total_distance_meters"] > 0 and agg["total_duration_seconds"] > 0:
                km = agg["total_distance_meters"] / 1000.0
                avg_pace = round(agg["total_duration_seconds"] / km)

            avg_hr = None
            if agg["hr_duration_sum"] > 0:
                avg_hr = round(agg["hr_weighted_sum"] / agg["hr_duration_sum"])

            result.append({
                "date": agg["date"],
                "total_distance_meters": agg["total_distance_meters"] if agg["total_distance_meters"] > 0 else None,
                "total_duration_seconds": agg["total_duration_seconds"] if agg["total_duration_seconds"] > 0 else None,
                "avg_pace_seconds_per_km": avg_pace,
                "avg_heart_rate": avg_hr,
                "total_calories": agg["total_calories"] if agg["total_calories"] > 0 else None,
                "total_sets": agg["total_sets"],
            })

        return result

    async def get_workout_trends(
        self, user_id: str, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """Get weekly workout trends over a date range.

        Returns per-ISO-week aggregations: sessions, sets, volume, distance, duration.
        """
        # 1. Fetch sessions in range
        sessions_response = (
            self.supabase.admin_client.table("workout_sessions")
            .select("id, session_date, start_time, end_time")
            .eq("user_id", user_id)
            .gte("session_date", start_date.isoformat())
            .lte("session_date", end_date.isoformat())
            .order("session_date")
            .execute()
        )

        if not sessions_response.data:
            return []

        session_ids = [s["id"] for s in sessions_response.data]

        # 2. Fetch all sets in those sessions
        sets_response = (
            self.supabase.admin_client.table("workout_sets")
            .select("session_id, set_type, weight_kg, reps, distance_meters, duration_seconds")
            .in_("session_id", session_ids)
            .execute()
        )

        # Build sets-per-session map
        sets_by_session: dict[str, list] = {}
        for s in sets_response.data:
            sid = s["session_id"]
            if sid not in sets_by_session:
                sets_by_session[sid] = []
            sets_by_session[sid].append(s)

        # 3. Group sessions by ISO week (Monday-based)
        week_data: dict[str, dict] = {}
        for session in sessions_response.data:
            session_date_obj = date.fromisoformat(session["session_date"])
            # ISO week: year-Wnn
            iso_year, iso_week, _ = session_date_obj.isocalendar()
            week_key = f"{iso_year}-W{iso_week:02d}"

            # Compute week_start (Monday)
            week_start = session_date_obj - timedelta(days=session_date_obj.weekday())

            if week_key not in week_data:
                week_data[week_key] = {
                    "week": week_key,
                    "week_start": week_start.isoformat(),
                    "total_sessions": 0,
                    "total_sets": 0,
                    "total_volume_kg": 0.0,
                    "total_distance_meters": 0.0,
                    "total_duration_minutes": 0.0,
                }

            agg = week_data[week_key]
            agg["total_sessions"] += 1

            # Session duration
            duration_mins = self._compute_session_duration(session)
            if duration_mins:
                agg["total_duration_minutes"] += duration_mins

            # Aggregate sets
            session_sets = sets_by_session.get(session["id"], [])
            agg["total_sets"] += len(session_sets)

            for s in session_sets:
                # Volume from strength sets
                if s.get("weight_kg") is not None and s.get("reps") is not None and s["reps"] > 0:
                    agg["total_volume_kg"] += float(s["weight_kg"]) * s["reps"]
                # Distance from cardio sets
                if s.get("distance_meters") is not None:
                    agg["total_distance_meters"] += float(s["distance_meters"])

        # 4. Finalize and sort by week
        result = []
        for week_key in sorted(week_data.keys()):
            agg = week_data[week_key]
            result.append({
                "week": agg["week"],
                "week_start": agg["week_start"],
                "total_sessions": agg["total_sessions"],
                "total_sets": agg["total_sets"],
                "total_volume_kg": agg["total_volume_kg"] if agg["total_volume_kg"] > 0 else None,
                "total_distance_meters": agg["total_distance_meters"] if agg["total_distance_meters"] > 0 else None,
                "total_duration_minutes": round(agg["total_duration_minutes"], 1) if agg["total_duration_minutes"] > 0 else None,
            })

        return result

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
