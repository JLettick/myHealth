"""Tests for workout analytics service methods."""

import pytest
from unittest.mock import MagicMock
from decimal import Decimal

from app.services.workout_service import WorkoutService


def make_chain(data=None):
    """Create a mock Supabase chain that returns the given data."""
    chain = MagicMock()
    chain.select.return_value = chain
    chain.insert.return_value = chain
    chain.update.return_value = chain
    chain.delete.return_value = chain
    chain.eq.return_value = chain
    chain.in_.return_value = chain
    chain.gte.return_value = chain
    chain.lte.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.or_.return_value = chain
    result = MagicMock()
    result.data = data or []
    chain.execute.return_value = result
    return chain


@pytest.fixture
def mock_supabase():
    supabase = MagicMock()
    admin = MagicMock()
    supabase.admin_client = admin
    return supabase


@pytest.fixture
def service(mock_supabase):
    return WorkoutService(supabase=mock_supabase)


class TestGetExerciseHistory:
    @pytest.mark.asyncio
    async def test_aggregation(self, service, mock_supabase, user_id):
        """Test that weight, volume, reps, RPE are computed correctly."""
        sessions_data = [
            {"id": "s1", "session_date": "2024-01-15"},
        ]
        sets_data = [
            {"session_id": "s1", "weight_kg": Decimal("100"), "reps": 5, "rpe": Decimal("8")},
            {"session_id": "s1", "weight_kg": Decimal("110"), "reps": 3, "rpe": Decimal("9")},
            {"session_id": "s1", "weight_kg": Decimal("90"), "reps": 8, "rpe": None},
        ]

        call_count = [0]

        def table_side_effect(name):
            if name == "workout_sessions":
                return make_chain(sessions_data)
            elif name == "workout_sets":
                return make_chain(sets_data)
            return make_chain()

        mock_supabase.admin_client.table.side_effect = table_side_effect

        from datetime import date
        result = await service.get_exercise_history(
            user_id, "ex-1", date(2024, 1, 1), date(2024, 1, 31)
        )

        assert len(result) == 1
        point = result[0]
        assert point["date"] == "2024-01-15"
        assert point["max_weight_kg"] == 110.0
        # Volume: 100*5 + 110*3 + 90*8 = 500 + 330 + 720 = 1550
        assert point["total_volume_kg"] == 1550.0
        # Reps: 5 + 3 + 8 = 16
        assert point["total_reps"] == 16
        # RPE: (8 + 9) / 2 = 8.5
        assert point["avg_rpe"] == 8.5
        assert point["total_sets"] == 3

    @pytest.mark.asyncio
    async def test_grouping_by_date(self, service, mock_supabase, user_id):
        """Test that sets from different sessions on the same date aggregate together."""
        sessions_data = [
            {"id": "s1", "session_date": "2024-01-15"},
            {"id": "s2", "session_date": "2024-01-15"},
            {"id": "s3", "session_date": "2024-01-16"},
        ]
        sets_data = [
            {"session_id": "s1", "weight_kg": Decimal("100"), "reps": 5, "rpe": None},
            {"session_id": "s2", "weight_kg": Decimal("105"), "reps": 5, "rpe": None},
            {"session_id": "s3", "weight_kg": Decimal("80"), "reps": 10, "rpe": None},
        ]

        def table_side_effect(name):
            if name == "workout_sessions":
                return make_chain(sessions_data)
            elif name == "workout_sets":
                return make_chain(sets_data)
            return make_chain()

        mock_supabase.admin_client.table.side_effect = table_side_effect

        from datetime import date
        result = await service.get_exercise_history(
            user_id, "ex-1", date(2024, 1, 1), date(2024, 1, 31)
        )

        assert len(result) == 2
        # Jan 15: max_weight 105, total_reps 10
        assert result[0]["date"] == "2024-01-15"
        assert result[0]["max_weight_kg"] == 105.0
        assert result[0]["total_reps"] == 10
        # Jan 16: max_weight 80, total_reps 10
        assert result[1]["date"] == "2024-01-16"
        assert result[1]["max_weight_kg"] == 80.0
        assert result[1]["total_reps"] == 10

    @pytest.mark.asyncio
    async def test_empty_result(self, service, mock_supabase, user_id):
        """Test that no sessions returns empty list."""
        mock_supabase.admin_client.table.side_effect = lambda name: make_chain([])

        from datetime import date
        result = await service.get_exercise_history(
            user_id, "ex-1", date(2024, 1, 1), date(2024, 1, 31)
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_no_sets_for_exercise(self, service, mock_supabase, user_id):
        """Test that sessions exist but no sets for exercise returns empty list."""
        sessions_data = [
            {"id": "s1", "session_date": "2024-01-15"},
        ]

        call_count = [0]

        def table_side_effect(name):
            if name == "workout_sessions":
                return make_chain(sessions_data)
            elif name == "workout_sets":
                return make_chain([])
            return make_chain()

        mock_supabase.admin_client.table.side_effect = table_side_effect

        from datetime import date
        result = await service.get_exercise_history(
            user_id, "ex-1", date(2024, 1, 1), date(2024, 1, 31)
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_decimal_to_float_conversion(self, service, mock_supabase, user_id):
        """Test that Decimal values are converted to float."""
        sessions_data = [{"id": "s1", "session_date": "2024-01-15"}]
        sets_data = [
            {"session_id": "s1", "weight_kg": Decimal("67.5"), "reps": 10, "rpe": Decimal("7.5")},
        ]

        def table_side_effect(name):
            if name == "workout_sessions":
                return make_chain(sessions_data)
            elif name == "workout_sets":
                return make_chain(sets_data)
            return make_chain()

        mock_supabase.admin_client.table.side_effect = table_side_effect

        from datetime import date
        result = await service.get_exercise_history(
            user_id, "ex-1", date(2024, 1, 1), date(2024, 1, 31)
        )

        point = result[0]
        assert isinstance(point["max_weight_kg"], float)
        assert isinstance(point["total_volume_kg"], float)
        assert isinstance(point["avg_rpe"], float)
        assert point["max_weight_kg"] == 67.5
        assert point["total_volume_kg"] == 675.0
        assert point["avg_rpe"] == 7.5


class TestGetCardioHistory:
    @pytest.mark.asyncio
    async def test_aggregation(self, service, mock_supabase, user_id):
        """Test distance, duration, calories aggregation."""
        sessions_data = [{"id": "s1", "session_date": "2024-01-15"}]
        sets_data = [
            {
                "session_id": "s1",
                "distance_meters": Decimal("5000"),
                "duration_seconds": 1500,
                "avg_heart_rate": 150,
                "calories_burned": 400,
            },
            {
                "session_id": "s1",
                "distance_meters": Decimal("3000"),
                "duration_seconds": 1000,
                "avg_heart_rate": 140,
                "calories_burned": 250,
            },
        ]

        def table_side_effect(name):
            if name == "workout_sessions":
                return make_chain(sessions_data)
            elif name == "workout_sets":
                return make_chain(sets_data)
            return make_chain()

        mock_supabase.admin_client.table.side_effect = table_side_effect

        from datetime import date
        result = await service.get_cardio_history(
            user_id, "ex-1", date(2024, 1, 1), date(2024, 1, 31)
        )

        assert len(result) == 1
        point = result[0]
        assert point["total_distance_meters"] == 8000.0
        assert point["total_duration_seconds"] == 2500
        assert point["total_calories"] == 650
        assert point["total_sets"] == 2

    @pytest.mark.asyncio
    async def test_pace_calculation(self, service, mock_supabase, user_id):
        """Test avg pace = total_duration / (total_distance/1000)."""
        sessions_data = [{"id": "s1", "session_date": "2024-01-15"}]
        sets_data = [
            {
                "session_id": "s1",
                "distance_meters": Decimal("10000"),
                "duration_seconds": 3000,
                "avg_heart_rate": None,
                "calories_burned": None,
            },
        ]

        def table_side_effect(name):
            if name == "workout_sessions":
                return make_chain(sessions_data)
            elif name == "workout_sets":
                return make_chain(sets_data)
            return make_chain()

        mock_supabase.admin_client.table.side_effect = table_side_effect

        from datetime import date
        result = await service.get_cardio_history(
            user_id, "ex-1", date(2024, 1, 1), date(2024, 1, 31)
        )

        point = result[0]
        # 3000s / (10000m / 1000) = 3000/10 = 300 s/km = 5:00/km
        assert point["avg_pace_seconds_per_km"] == 300

    @pytest.mark.asyncio
    async def test_weighted_heart_rate(self, service, mock_supabase, user_id):
        """Test duration-weighted heart rate average."""
        sessions_data = [{"id": "s1", "session_date": "2024-01-15"}]
        sets_data = [
            {
                "session_id": "s1",
                "distance_meters": Decimal("5000"),
                "duration_seconds": 1000,
                "avg_heart_rate": 160,
                "calories_burned": None,
            },
            {
                "session_id": "s1",
                "distance_meters": Decimal("5000"),
                "duration_seconds": 3000,
                "avg_heart_rate": 140,
                "calories_burned": None,
            },
        ]

        def table_side_effect(name):
            if name == "workout_sessions":
                return make_chain(sessions_data)
            elif name == "workout_sets":
                return make_chain(sets_data)
            return make_chain()

        mock_supabase.admin_client.table.side_effect = table_side_effect

        from datetime import date
        result = await service.get_cardio_history(
            user_id, "ex-1", date(2024, 1, 1), date(2024, 1, 31)
        )

        point = result[0]
        # Weighted: (160*1000 + 140*3000) / (1000+3000) = (160000+420000)/4000 = 145
        assert point["avg_heart_rate"] == 145

    @pytest.mark.asyncio
    async def test_empty_result(self, service, mock_supabase, user_id):
        """Test no sessions returns empty list."""
        mock_supabase.admin_client.table.side_effect = lambda name: make_chain([])

        from datetime import date
        result = await service.get_cardio_history(
            user_id, "ex-1", date(2024, 1, 1), date(2024, 1, 31)
        )

        assert result == []


class TestGetWorkoutTrends:
    @pytest.mark.asyncio
    async def test_weekly_grouping(self, service, mock_supabase, user_id):
        """Test sessions on different days in the same week aggregate together."""
        # Mon Jan 15, 2024 and Wed Jan 17, 2024 are same ISO week (W03)
        sessions_data = [
            {"id": "s1", "session_date": "2024-01-15", "start_time": "2024-01-15T08:00:00", "end_time": "2024-01-15T09:00:00"},
            {"id": "s2", "session_date": "2024-01-17", "start_time": "2024-01-17T08:00:00", "end_time": "2024-01-17T08:30:00"},
        ]
        sets_data = [
            {"session_id": "s1", "set_type": "strength", "weight_kg": Decimal("100"), "reps": 5, "distance_meters": None, "duration_seconds": None},
            {"session_id": "s2", "set_type": "strength", "weight_kg": Decimal("80"), "reps": 10, "distance_meters": None, "duration_seconds": None},
        ]

        def table_side_effect(name):
            if name == "workout_sessions":
                return make_chain(sessions_data)
            elif name == "workout_sets":
                return make_chain(sets_data)
            return make_chain()

        mock_supabase.admin_client.table.side_effect = table_side_effect

        from datetime import date
        result = await service.get_workout_trends(
            user_id, date(2024, 1, 1), date(2024, 1, 31)
        )

        assert len(result) == 1
        week = result[0]
        assert week["week"] == "2024-W03"
        assert week["total_sessions"] == 2
        assert week["total_sets"] == 2
        # Volume: 100*5 + 80*10 = 500 + 800 = 1300
        assert week["total_volume_kg"] == 1300.0
        # Duration: 60 + 30 = 90 minutes
        assert week["total_duration_minutes"] == 90.0

    @pytest.mark.asyncio
    async def test_cross_week_boundary(self, service, mock_supabase, user_id):
        """Test sessions in different weeks produce separate data points."""
        # Sun Jan 14, 2024 = W02, Mon Jan 15, 2024 = W03
        sessions_data = [
            {"id": "s1", "session_date": "2024-01-14", "start_time": None, "end_time": None},
            {"id": "s2", "session_date": "2024-01-15", "start_time": None, "end_time": None},
        ]
        sets_data = [
            {"session_id": "s1", "set_type": "strength", "weight_kg": Decimal("50"), "reps": 10, "distance_meters": None, "duration_seconds": None},
            {"session_id": "s2", "set_type": "strength", "weight_kg": Decimal("60"), "reps": 10, "distance_meters": None, "duration_seconds": None},
        ]

        def table_side_effect(name):
            if name == "workout_sessions":
                return make_chain(sessions_data)
            elif name == "workout_sets":
                return make_chain(sets_data)
            return make_chain()

        mock_supabase.admin_client.table.side_effect = table_side_effect

        from datetime import date
        result = await service.get_workout_trends(
            user_id, date(2024, 1, 1), date(2024, 1, 31)
        )

        assert len(result) == 2
        assert result[0]["week"] == "2024-W02"
        assert result[0]["total_sessions"] == 1
        assert result[0]["total_volume_kg"] == 500.0
        assert result[1]["week"] == "2024-W03"
        assert result[1]["total_sessions"] == 1
        assert result[1]["total_volume_kg"] == 600.0

    @pytest.mark.asyncio
    async def test_mixed_strength_cardio(self, service, mock_supabase, user_id):
        """Test that strength volume and cardio distance both appear."""
        sessions_data = [
            {"id": "s1", "session_date": "2024-01-15", "start_time": None, "end_time": None},
        ]
        sets_data = [
            {"session_id": "s1", "set_type": "strength", "weight_kg": Decimal("100"), "reps": 5, "distance_meters": None, "duration_seconds": None},
            {"session_id": "s1", "set_type": "cardio", "weight_kg": None, "reps": None, "distance_meters": Decimal("5000"), "duration_seconds": 1500},
        ]

        def table_side_effect(name):
            if name == "workout_sessions":
                return make_chain(sessions_data)
            elif name == "workout_sets":
                return make_chain(sets_data)
            return make_chain()

        mock_supabase.admin_client.table.side_effect = table_side_effect

        from datetime import date
        result = await service.get_workout_trends(
            user_id, date(2024, 1, 1), date(2024, 1, 31)
        )

        assert len(result) == 1
        week = result[0]
        assert week["total_volume_kg"] == 500.0
        assert week["total_distance_meters"] == 5000.0
        assert week["total_sets"] == 2

    @pytest.mark.asyncio
    async def test_empty_result(self, service, mock_supabase, user_id):
        """Test no sessions returns empty list."""
        mock_supabase.admin_client.table.side_effect = lambda name: make_chain([])

        from datetime import date
        result = await service.get_workout_trends(
            user_id, date(2024, 1, 1), date(2024, 1, 31)
        )

        assert result == []
