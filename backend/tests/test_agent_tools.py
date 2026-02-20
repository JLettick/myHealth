"""Tests for agent tool definitions and execution."""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.agent_tools import (
    TOOL_DEFINITIONS,
    execute_tool,
    get_tool_action_label,
    _parse_date,
    _serialize,
    _compute_trend,
)


class TestToolDefinitions:
    def test_all_14_tools_defined(self):
        assert len(TOOL_DEFINITIONS) == 14

    def test_all_tools_have_required_fields(self):
        for tool in TOOL_DEFINITIONS:
            spec = tool["toolSpec"]
            assert "name" in spec
            assert "description" in spec
            assert "inputSchema" in spec
            assert "json" in spec["inputSchema"]

    def test_tool_names(self):
        names = [t["toolSpec"]["name"] for t in TOOL_DEFINITIONS]
        expected = [
            "get_nutrition_summary",
            "search_foods",
            "search_usda_foods",
            "get_workout_summary",
            "search_exercises",
            "get_whoop_summary",
            "get_nutrition_trends",
            "get_workout_progression",
            "get_workout_trends",
            "get_recovery_trends",
            "log_food_entry",
            "create_food",
            "log_workout",
            "create_exercise",
        ]
        assert names == expected

    def test_write_tools_have_required_fields(self):
        """Write tools should have required input fields."""
        write_tools = {t["toolSpec"]["name"]: t for t in TOOL_DEFINITIONS}

        # log_food_entry requires food_id and meal_type
        log_food = write_tools["log_food_entry"]["toolSpec"]["inputSchema"]["json"]
        assert "food_id" in log_food["required"]
        assert "meal_type" in log_food["required"]

        # create_food requires name and macros
        create_food = write_tools["create_food"]["toolSpec"]["inputSchema"]["json"]
        assert "name" in create_food["required"]
        assert "calories" in create_food["required"]

        # log_workout requires workout_type and sets
        log_workout = write_tools["log_workout"]["toolSpec"]["inputSchema"]["json"]
        assert "workout_type" in log_workout["required"]
        assert "sets" in log_workout["required"]

        # create_exercise requires name and category
        create_ex = write_tools["create_exercise"]["toolSpec"]["inputSchema"]["json"]
        assert "name" in create_ex["required"]
        assert "category" in create_ex["required"]

    def test_analysis_tools_have_correct_schemas(self):
        """Analysis tools should have correct required/optional params."""
        tools = {t["toolSpec"]["name"]: t for t in TOOL_DEFINITIONS}

        # get_nutrition_trends requires start_date and end_date
        nt = tools["get_nutrition_trends"]["toolSpec"]["inputSchema"]["json"]
        assert "start_date" in nt["required"]
        assert "end_date" in nt["required"]

        # get_workout_progression requires exercise_name
        wp = tools["get_workout_progression"]["toolSpec"]["inputSchema"]["json"]
        assert "exercise_name" in wp["required"]
        assert "days" in wp["properties"]

        # get_workout_trends has no required params
        wt = tools["get_workout_trends"]["toolSpec"]["inputSchema"]["json"]
        assert wt["required"] == []
        assert "weeks" in wt["properties"]

        # get_recovery_trends has no required params
        rt = tools["get_recovery_trends"]["toolSpec"]["inputSchema"]["json"]
        assert rt["required"] == []
        assert "days" in rt["properties"]


class TestParseDate:
    def test_valid_date(self):
        assert _parse_date("2026-01-15") == date(2026, 1, 15)

    def test_none_returns_today(self):
        assert _parse_date(None) == date.today()

    def test_empty_string_returns_today(self):
        assert _parse_date("") == date.today()

    def test_invalid_format_returns_today(self):
        assert _parse_date("not-a-date") == date.today()


class TestSerialize:
    def test_decimal_to_float(self):
        assert _serialize(Decimal("3.14")) == 3.14

    def test_date_to_isoformat(self):
        assert _serialize(date(2026, 1, 15)) == "2026-01-15"

    def test_nested_dict(self):
        data = {"amount": Decimal("100.5"), "date": date(2026, 1, 1)}
        result = _serialize(data)
        assert result == {"amount": 100.5, "date": "2026-01-01"}

    def test_list_of_decimals(self):
        assert _serialize([Decimal("1"), Decimal("2")]) == [1.0, 2.0]

    def test_plain_values_unchanged(self):
        assert _serialize("hello") == "hello"
        assert _serialize(42) == 42
        assert _serialize(None) is None


class TestComputeTrend:
    def test_insufficient_data(self):
        assert _compute_trend([1.0, 2.0, 3.0]) == "insufficient_data"

    def test_insufficient_data_with_nones(self):
        assert _compute_trend([1.0, None, 2.0, None]) == "insufficient_data"

    def test_improving(self):
        # First half avg: 50, second half avg: 60 → 20% increase
        assert _compute_trend([50.0, 50.0, 60.0, 60.0]) == "improving"

    def test_declining(self):
        # First half avg: 60, second half avg: 50 → ~17% decrease
        assert _compute_trend([60.0, 60.0, 50.0, 50.0]) == "declining"

    def test_stable(self):
        # First half avg: 50, second half avg: 51 → 2% change (within 5%)
        assert _compute_trend([50.0, 50.0, 51.0, 51.0]) == "stable"

    def test_handles_none_values(self):
        # valid values: [50, 50, 60, 60] after filtering
        assert _compute_trend([50.0, None, 50.0, 60.0, None, 60.0]) == "improving"

    def test_all_zeros_stable(self):
        assert _compute_trend([0.0, 0.0, 0.0, 0.0]) == "stable"

    def test_zero_to_positive_improving(self):
        assert _compute_trend([0.0, 0.0, 5.0, 5.0]) == "improving"


class TestGetToolActionLabel:
    def test_known_tools(self):
        assert get_tool_action_label("log_food_entry") == "Logged food entry"
        assert get_tool_action_label("get_whoop_summary") == "Checked Whoop metrics"

    def test_analysis_tools(self):
        assert get_tool_action_label("get_nutrition_trends") == "Analyzed nutrition trends"
        assert get_tool_action_label("get_workout_progression") == "Analyzed exercise progression"
        assert get_tool_action_label("get_workout_trends") == "Analyzed workout trends"
        assert get_tool_action_label("get_recovery_trends") == "Analyzed recovery trends"

    def test_unknown_tool_returns_name(self):
        assert get_tool_action_label("unknown_tool") == "unknown_tool"


class TestExecuteTool:
    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self, user_id):
        result = await execute_tool("nonexistent_tool", {}, user_id)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_nutrition_summary(self, user_id):
        mock_summary = {
            "date": date.today(),
            "total_calories": Decimal("500"),
            "total_protein_g": Decimal("30"),
            "total_carbs_g": Decimal("60"),
            "total_fat_g": Decimal("20"),
            "meals": [],
        }
        with patch(
            "app.services.nutrition_service.get_nutrition_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.get_daily_summary = AsyncMock(return_value=mock_summary)
            mock_get.return_value = mock_service

            result = await execute_tool("get_nutrition_summary", {}, user_id)

            assert result["total_calories"] == 500.0
            assert isinstance(result["total_calories"], float)
            mock_service.get_daily_summary.assert_called_once_with(
                user_id, date.today()
            )

    @pytest.mark.asyncio
    async def test_get_nutrition_summary_with_date(self, user_id):
        mock_summary = {"date": date(2026, 1, 15), "total_calories": Decimal("0"), "meals": []}
        with patch(
            "app.services.nutrition_service.get_nutrition_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.get_daily_summary = AsyncMock(return_value=mock_summary)
            mock_get.return_value = mock_service

            await execute_tool(
                "get_nutrition_summary", {"date": "2026-01-15"}, user_id
            )

            mock_service.get_daily_summary.assert_called_once_with(
                user_id, date(2026, 1, 15)
            )

    @pytest.mark.asyncio
    async def test_search_foods(self, user_id):
        mock_foods = [{"id": "food-1", "name": "Chicken", "calories": 200}]
        with patch(
            "app.services.nutrition_service.get_nutrition_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.search_foods = AsyncMock(return_value=(mock_foods, 1))
            mock_get.return_value = mock_service

            result = await execute_tool(
                "search_foods", {"query": "chicken"}, user_id
            )

            assert result["total"] == 1
            assert len(result["foods"]) == 1
            assert result["foods"][0]["name"] == "Chicken"

    @pytest.mark.asyncio
    async def test_search_usda_foods(self, user_id):
        mock_usda_results = {
            "foods": [{"description": "Chicken breast", "fdcId": 12345}],
            "totalHits": 1,
        }
        mock_parsed = {
            "name": "Chicken breast",
            "calories": 165.0,
            "protein_g": 31.0,
        }
        with patch(
            "app.services.usda_service.get_usda_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.search_foods = AsyncMock(return_value=mock_usda_results)
            mock_service.parse_food_to_schema.return_value = mock_parsed
            mock_get.return_value = mock_service

            result = await execute_tool(
                "search_usda_foods", {"query": "chicken"}, user_id
            )

            assert result["total"] == 1
            assert result["foods"][0]["name"] == "Chicken breast"

    @pytest.mark.asyncio
    async def test_get_whoop_summary(self, user_id):
        mock_summary = {
            "is_connected": True,
            "latest_recovery_score": 85.0,
            "latest_hrv": 45.0,
        }
        with patch(
            "app.services.whoop_sync_service.get_whoop_sync_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.get_dashboard_summary = AsyncMock(return_value=mock_summary)
            mock_get.return_value = mock_service

            result = await execute_tool("get_whoop_summary", {}, user_id)

            assert result["is_connected"] is True
            assert result["latest_recovery_score"] == 85.0

    @pytest.mark.asyncio
    async def test_log_food_entry(self, user_id):
        mock_entry = {
            "id": "entry-1",
            "food_id": "food-1",
            "meal_type": "lunch",
            "servings": Decimal("1"),
            "total_calories": Decimal("350"),
        }
        with patch(
            "app.services.nutrition_service.get_nutrition_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.create_entry = AsyncMock(return_value=mock_entry)
            mock_get.return_value = mock_service

            result = await execute_tool(
                "log_food_entry",
                {"food_id": "food-1", "meal_type": "lunch", "servings": 1.5},
                user_id,
            )

            assert result["total_calories"] == 350.0
            call_args = mock_service.create_entry.call_args
            assert call_args[0][0] == user_id
            assert call_args[0][1]["food_id"] == "food-1"
            assert call_args[0][1]["meal_type"] == "lunch"
            assert call_args[0][1]["servings"] == Decimal("1.5")

    @pytest.mark.asyncio
    async def test_log_food_entry_failure(self, user_id):
        with patch(
            "app.services.nutrition_service.get_nutrition_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.create_entry = AsyncMock(return_value=None)
            mock_get.return_value = mock_service

            result = await execute_tool(
                "log_food_entry",
                {"food_id": "bad-id", "meal_type": "lunch"},
                user_id,
            )

            assert "error" in result

    @pytest.mark.asyncio
    async def test_create_food(self, user_id):
        mock_food = {
            "id": "food-new",
            "name": "Protein Shake",
            "calories": 250,
        }
        with patch(
            "app.services.nutrition_service.get_nutrition_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.create_food = AsyncMock(return_value=mock_food)
            mock_get.return_value = mock_service

            result = await execute_tool(
                "create_food",
                {
                    "name": "Protein Shake",
                    "calories": 250,
                    "protein_g": 30,
                    "carbs_g": 20,
                    "fat_g": 5,
                },
                user_id,
            )

            assert result["name"] == "Protein Shake"

    @pytest.mark.asyncio
    async def test_log_workout(self, user_id):
        mock_session = {"id": "session-1", "workout_type": "cardio"}
        mock_set = {"id": "set-1", "set_type": "cardio", "distance_meters": 5000}
        with patch(
            "app.services.workout_service.get_workout_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.create_session = AsyncMock(return_value=mock_session)
            mock_service.create_set = AsyncMock(return_value=mock_set)
            mock_get.return_value = mock_service

            result = await execute_tool(
                "log_workout",
                {
                    "workout_type": "cardio",
                    "sets": [
                        {
                            "exercise_id": "ex-1",
                            "set_type": "cardio",
                            "duration_seconds": 1500,
                            "distance_meters": 5000,
                        }
                    ],
                },
                user_id,
            )

            assert result["sets_created"] == 1
            mock_service.create_session.assert_called_once()
            mock_service.create_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_exercise(self, user_id):
        mock_exercise = {
            "id": "ex-new",
            "name": "Box Jumps",
            "category": "strength",
        }
        with patch(
            "app.services.workout_service.get_workout_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.create_exercise = AsyncMock(return_value=mock_exercise)
            mock_get.return_value = mock_service

            result = await execute_tool(
                "create_exercise",
                {"name": "Box Jumps", "category": "strength"},
                user_id,
            )

            assert result["name"] == "Box Jumps"

    @pytest.mark.asyncio
    async def test_tool_exception_returns_error(self, user_id):
        with patch(
            "app.services.nutrition_service.get_nutrition_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.get_daily_summary = AsyncMock(
                side_effect=Exception("DB connection failed")
            )
            mock_get.return_value = mock_service

            result = await execute_tool("get_nutrition_summary", {}, user_id)

            assert "error" in result
            assert "DB connection failed" in result["error"]


class TestNutritionTrendsExecution:
    @pytest.mark.asyncio
    async def test_returns_daily_data_and_averages(self, user_id):
        today = date.today()
        yesterday = today - timedelta(days=1)
        mock_goals = {"calories_target": 2000, "protein_g_target": 150}
        mock_summary_day1 = {
            "date": yesterday,
            "total_calories": Decimal("1800"),
            "total_protein_g": Decimal("120"),
            "total_carbs_g": Decimal("200"),
            "total_fat_g": Decimal("60"),
            "meals": [],
        }
        mock_summary_day2 = {
            "date": today,
            "total_calories": Decimal("2200"),
            "total_protein_g": Decimal("160"),
            "total_carbs_g": Decimal("250"),
            "total_fat_g": Decimal("70"),
            "meals": [],
        }

        with patch(
            "app.services.nutrition_service.get_nutrition_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.get_goals = AsyncMock(return_value=mock_goals)
            mock_service.get_daily_summary = AsyncMock(
                side_effect=[mock_summary_day1, mock_summary_day2]
            )
            mock_get.return_value = mock_service

            result = await execute_tool(
                "get_nutrition_trends",
                {"start_date": yesterday.isoformat(), "end_date": today.isoformat()},
                user_id,
            )

            assert result["days_tracked"] == 2
            assert result["days_in_range"] == 2
            assert len(result["daily_data"]) == 2
            assert result["averages"]["calories"] == 2000.0
            assert result["goals"] is not None
            assert "calories_pct" in result["goal_adherence"]

    @pytest.mark.asyncio
    async def test_caps_at_30_days(self, user_id):
        today = date.today()
        start = today - timedelta(days=60)

        with patch(
            "app.services.nutrition_service.get_nutrition_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.get_goals = AsyncMock(return_value=None)
            mock_service.get_daily_summary = AsyncMock(return_value={
                "date": today, "total_calories": Decimal("0"), "meals": [],
            })
            mock_get.return_value = mock_service

            result = await execute_tool(
                "get_nutrition_trends",
                {"start_date": start.isoformat(), "end_date": today.isoformat()},
                user_id,
            )

            # Should be capped to 31 days (30 day range = 31 days inclusive)
            assert result["days_in_range"] == 31

    @pytest.mark.asyncio
    async def test_no_food_logged_returns_zero_tracked(self, user_id):
        today = date.today()
        with patch(
            "app.services.nutrition_service.get_nutrition_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.get_goals = AsyncMock(return_value=None)
            mock_service.get_daily_summary = AsyncMock(return_value={
                "date": today, "total_calories": Decimal("0"), "meals": [],
            })
            mock_get.return_value = mock_service

            result = await execute_tool(
                "get_nutrition_trends",
                {"start_date": today.isoformat(), "end_date": today.isoformat()},
                user_id,
            )

            assert result["days_tracked"] == 0
            assert result["averages"] == {}


class TestWorkoutProgressionExecution:
    @pytest.mark.asyncio
    async def test_strength_exercise_returns_progression(self, user_id):
        mock_exercises = [{"id": "ex-1", "name": "Bench Press", "category": "strength"}]
        mock_history = [
            {"date": "2026-01-01", "max_weight_kg": 60.0, "total_volume_kg": 3600.0, "total_reps": 30, "total_sets": 3},
            {"date": "2026-01-15", "max_weight_kg": 65.0, "total_volume_kg": 3900.0, "total_reps": 30, "total_sets": 3},
        ]

        with patch(
            "app.services.workout_service.get_workout_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.search_exercises = AsyncMock(return_value=(mock_exercises, 1))
            mock_service.get_exercise_history = AsyncMock(return_value=mock_history)
            mock_get.return_value = mock_service

            result = await execute_tool(
                "get_workout_progression",
                {"exercise_name": "bench press"},
                user_id,
            )

            assert result["type"] == "strength"
            assert result["total_sessions"] == 2
            assert result["exercise"]["name"] == "Bench Press"
            assert "weight_change_pct" in result["summary"]

    @pytest.mark.asyncio
    async def test_cardio_exercise_returns_progression(self, user_id):
        mock_exercises = [{"id": "ex-2", "name": "Running", "category": "cardio"}]
        mock_history = [
            {"date": "2026-01-01", "total_distance_meters": 5000.0, "avg_pace_seconds_per_km": 330, "total_sets": 1},
            {"date": "2026-01-15", "total_distance_meters": 5500.0, "avg_pace_seconds_per_km": 310, "total_sets": 1},
        ]

        with patch(
            "app.services.workout_service.get_workout_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.search_exercises = AsyncMock(return_value=(mock_exercises, 1))
            mock_service.get_cardio_history = AsyncMock(return_value=mock_history)
            mock_get.return_value = mock_service

            result = await execute_tool(
                "get_workout_progression",
                {"exercise_name": "running"},
                user_id,
            )

            assert result["type"] == "cardio"
            assert result["total_sessions"] == 2
            assert result["summary"]["pace_improved"] is True

    @pytest.mark.asyncio
    async def test_exercise_not_found(self, user_id):
        with patch(
            "app.services.workout_service.get_workout_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.search_exercises = AsyncMock(return_value=([], 0))
            mock_get.return_value = mock_service

            result = await execute_tool(
                "get_workout_progression",
                {"exercise_name": "nonexistent"},
                user_id,
            )

            assert "error" in result

    @pytest.mark.asyncio
    async def test_caps_days_at_90(self, user_id):
        mock_exercises = [{"id": "ex-1", "name": "Squat", "category": "strength"}]

        with patch(
            "app.services.workout_service.get_workout_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.search_exercises = AsyncMock(return_value=(mock_exercises, 1))
            mock_service.get_exercise_history = AsyncMock(return_value=[])
            mock_get.return_value = mock_service

            result = await execute_tool(
                "get_workout_progression",
                {"exercise_name": "squat", "days": 200},
                user_id,
            )

            # Verify it used 90 days max
            call_args = mock_service.get_exercise_history.call_args
            start_date = call_args[0][2]
            end_date = call_args[0][3]
            assert (end_date - start_date).days == 90


class TestWorkoutTrendsExecution:
    @pytest.mark.asyncio
    async def test_returns_weekly_data_and_averages(self, user_id):
        mock_weekly = [
            {"week": "2026-W06", "total_sessions": 3, "total_sets": 15, "total_volume_kg": 5000.0, "total_duration_minutes": 180.0},
            {"week": "2026-W07", "total_sessions": 4, "total_sets": 20, "total_volume_kg": 6000.0, "total_duration_minutes": 240.0},
        ]
        mock_goals = {"workouts_per_week_target": 4, "minutes_per_week_target": 200}

        with patch(
            "app.services.workout_service.get_workout_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.get_workout_trends = AsyncMock(return_value=mock_weekly)
            mock_service.get_goals = AsyncMock(return_value=mock_goals)
            mock_get.return_value = mock_service

            result = await execute_tool("get_workout_trends", {}, user_id)

            assert result["weeks_analyzed"] == 2
            assert len(result["weekly_data"]) == 2
            assert result["averages"]["sessions_per_week"] == 3.5
            assert result["goals"] is not None

    @pytest.mark.asyncio
    async def test_caps_weeks_at_12(self, user_id):
        with patch(
            "app.services.workout_service.get_workout_service"
        ) as mock_get:
            mock_service = MagicMock()
            mock_service.get_workout_trends = AsyncMock(return_value=[])
            mock_service.get_goals = AsyncMock(return_value=None)
            mock_get.return_value = mock_service

            await execute_tool(
                "get_workout_trends", {"weeks": 52}, user_id
            )

            call_args = mock_service.get_workout_trends.call_args
            start_date = call_args[0][1]
            end_date = call_args[0][2]
            weeks_diff = (end_date - start_date).days / 7
            assert weeks_diff == 12


class TestRecoveryTrendsExecution:
    @pytest.mark.asyncio
    async def test_whoop_not_connected(self, user_id):
        with patch(
            "app.services.whoop_service.get_whoop_service"
        ) as mock_whoop:
            mock_service = MagicMock()
            mock_service.get_connection = AsyncMock(return_value=None)
            mock_whoop.return_value = mock_service

            result = await execute_tool("get_recovery_trends", {}, user_id)

            assert "error" in result
            assert "not connected" in result["error"]

    @pytest.mark.asyncio
    async def test_returns_recovery_and_sleep_data(self, user_id):
        mock_recovery = [
            {"date": "2026-02-13", "recovery_score": 70.0, "hrv_rmssd_milli": 40.0, "resting_heart_rate": 55.0, "spo2_percentage": 97.0},
            {"date": "2026-02-14", "recovery_score": 75.0, "hrv_rmssd_milli": 42.0, "resting_heart_rate": 54.0, "spo2_percentage": 98.0},
            {"date": "2026-02-15", "recovery_score": 80.0, "hrv_rmssd_milli": 45.0, "resting_heart_rate": 53.0, "spo2_percentage": 97.0},
            {"date": "2026-02-16", "recovery_score": 85.0, "hrv_rmssd_milli": 48.0, "resting_heart_rate": 52.0, "spo2_percentage": 98.0},
        ]
        mock_sleep = [
            {"date": "2026-02-13", "sleep_score": 75.0, "sleep_efficiency": 90.0, "total_sleep_hours": 7.0, "rem_hours": 1.5, "deep_sleep_hours": 1.0, "light_sleep_hours": 4.5, "respiratory_rate": 15.0},
            {"date": "2026-02-14", "sleep_score": 80.0, "sleep_efficiency": 92.0, "total_sleep_hours": 7.5, "rem_hours": 1.8, "deep_sleep_hours": 1.2, "light_sleep_hours": 4.5, "respiratory_rate": 14.5},
            {"date": "2026-02-15", "sleep_score": 82.0, "sleep_efficiency": 91.0, "total_sleep_hours": 7.2, "rem_hours": 1.6, "deep_sleep_hours": 1.1, "light_sleep_hours": 4.5, "respiratory_rate": 15.0},
            {"date": "2026-02-16", "sleep_score": 85.0, "sleep_efficiency": 93.0, "total_sleep_hours": 8.0, "rem_hours": 2.0, "deep_sleep_hours": 1.3, "light_sleep_hours": 4.7, "respiratory_rate": 14.0},
        ]

        with patch(
            "app.services.whoop_service.get_whoop_service"
        ) as mock_whoop, patch(
            "app.services.whoop_sync_service.get_whoop_sync_service"
        ) as mock_sync:
            mock_whoop_svc = MagicMock()
            mock_whoop_svc.get_connection = AsyncMock(return_value={"id": "conn-1"})
            mock_whoop.return_value = mock_whoop_svc

            mock_sync_svc = MagicMock()
            mock_sync_svc.get_recovery_trend_data = AsyncMock(return_value=mock_recovery)
            mock_sync_svc.get_sleep_trend_data = AsyncMock(return_value=mock_sleep)
            mock_sync.return_value = mock_sync_svc

            result = await execute_tool("get_recovery_trends", {"days": 7}, user_id)

            assert result["days_with_recovery_data"] == 4
            assert result["days_with_sleep_data"] == 4
            assert "recovery_score" in result["recovery_averages"]
            assert "total_sleep_hours" in result["sleep_averages"]
            assert "recovery_score" in result["trend"]
            assert "sleep_hours" in result["trend"]

    @pytest.mark.asyncio
    async def test_caps_days_at_30(self, user_id):
        with patch(
            "app.services.whoop_service.get_whoop_service"
        ) as mock_whoop, patch(
            "app.services.whoop_sync_service.get_whoop_sync_service"
        ) as mock_sync:
            mock_whoop_svc = MagicMock()
            mock_whoop_svc.get_connection = AsyncMock(return_value={"id": "conn-1"})
            mock_whoop.return_value = mock_whoop_svc

            mock_sync_svc = MagicMock()
            mock_sync_svc.get_recovery_trend_data = AsyncMock(return_value=[])
            mock_sync_svc.get_sleep_trend_data = AsyncMock(return_value=[])
            mock_sync.return_value = mock_sync_svc

            await execute_tool("get_recovery_trends", {"days": 100}, user_id)

            # Verify it capped at 30
            call_args = mock_sync_svc.get_recovery_trend_data.call_args
            assert call_args[0][1] == 30
