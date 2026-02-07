"""Tests for agent tool definitions and execution."""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.agent_tools import (
    TOOL_DEFINITIONS,
    execute_tool,
    get_tool_action_label,
    _parse_date,
    _serialize,
)


class TestToolDefinitions:
    def test_all_10_tools_defined(self):
        assert len(TOOL_DEFINITIONS) == 10

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


class TestGetToolActionLabel:
    def test_known_tools(self):
        assert get_tool_action_label("log_food_entry") == "Logged food entry"
        assert get_tool_action_label("get_whoop_summary") == "Checked Whoop metrics"

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
