"""
Agent tool definitions and execution dispatcher.

Defines tools in Bedrock Converse API format and provides an
execute_tool() function that dispatches tool calls to existing services.
"""

import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool definitions (Converse API format)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    # --- Read tools ---
    {
        "toolSpec": {
            "name": "get_nutrition_summary",
            "description": "Get the user's nutrition summary for a specific date including meals, macros (calories, protein, carbs, fat), and daily goals.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format. Defaults to today.",
                        }
                    },
                    "required": [],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "search_foods",
            "description": "Search the user's food database by name. Returns matching foods with their nutritional info and their id (which is the food_id needed for log_food_entry). Always try this first before search_usda_foods.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Food name to search for (e.g. 'chicken breast', 'banana').",
                        }
                    },
                    "required": ["query"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "search_usda_foods",
            "description": "Search the USDA FoodData Central database for foods not in the user's database. Returns nutrition data. IMPORTANT: These results do NOT have a food_id. You must use create_food to add the food to the user's database before logging it with log_food_entry.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Food name to search for in USDA database.",
                        }
                    },
                    "required": ["query"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "get_workout_summary",
            "description": "Get the user's workout summary for a specific date including sessions, exercises, sets, volume, and distance.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format. Defaults to today.",
                        }
                    },
                    "required": [],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "search_exercises",
            "description": "Search for exercises by name and/or category. Use this before logging a workout to find the exercise_id.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Exercise name to search for (e.g. 'bench press', 'squat').",
                        },
                        "category": {
                            "type": "string",
                            "description": "Filter by category: 'strength', 'cardio', 'flexibility', 'sports', 'other'.",
                            "enum": ["strength", "cardio", "flexibility", "sports", "other"],
                        },
                    },
                    "required": [],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "get_whoop_summary",
            "description": "Get the user's Whoop recovery, sleep, HRV, resting heart rate, and strain metrics.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                }
            },
        }
    },
    # --- Analysis tools (multi-day trends) ---
    {
        "toolSpec": {
            "name": "get_nutrition_trends",
            "description": "Analyze the user's nutrition over a date range. Returns daily calorie/macro data, averages, goal adherence percentages, and days tracked. Max 30-day range.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format.",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format.",
                        },
                    },
                    "required": ["start_date", "end_date"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "get_workout_progression",
            "description": "Analyze progression for a specific exercise over time. For strength: tracks max weight, volume, reps. For cardio: tracks pace, distance, duration. Returns data points and first-vs-last comparison.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "exercise_name": {
                            "type": "string",
                            "description": "Name of the exercise to analyze (e.g. 'bench press', 'running').",
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back. Defaults to 30, max 90.",
                        },
                    },
                    "required": ["exercise_name"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "get_workout_trends",
            "description": "Analyze weekly workout trends including session count, total volume, distance, and duration. Compares against workout goals if set.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "weeks": {
                            "type": "integer",
                            "description": "Number of weeks to analyze. Defaults to 4, max 12.",
                        },
                    },
                    "required": [],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "get_recovery_trends",
            "description": "Analyze Whoop recovery and sleep trends. Returns recovery scores, HRV, resting HR, sleep hours/quality, and trend direction (improving/declining/stable). Requires Whoop connection.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to analyze. Defaults to 7, max 30.",
                        },
                    },
                    "required": [],
                }
            },
        }
    },
    # --- Write tools ---
    {
        "toolSpec": {
            "name": "log_food_entry",
            "description": "Log a food entry for a meal. Requires a food_id (from search_foods or create_food). Records the food, meal type, servings, and date.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "food_id": {
                            "type": "string",
                            "description": "The UUID of the food to log (from search_foods or create_food).",
                        },
                        "meal_type": {
                            "type": "string",
                            "description": "Which meal: 'breakfast', 'lunch', 'dinner', or 'snack'.",
                            "enum": ["breakfast", "lunch", "dinner", "snack"],
                        },
                        "servings": {
                            "type": "number",
                            "description": "Number of servings (e.g. 1, 1.5, 2). Defaults to 1.",
                        },
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format. Defaults to today.",
                        },
                    },
                    "required": ["food_id", "meal_type"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "create_food",
            "description": "Create a custom food with nutritional info. Use this when a food isn't found in search_foods or search_usda_foods. Returns the new food with its food_id for logging.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Food name (e.g. 'Homemade Protein Shake').",
                        },
                        "calories": {
                            "type": "number",
                            "description": "Calories per serving.",
                        },
                        "protein_g": {
                            "type": "number",
                            "description": "Protein in grams per serving.",
                        },
                        "carbs_g": {
                            "type": "number",
                            "description": "Carbohydrates in grams per serving.",
                        },
                        "fat_g": {
                            "type": "number",
                            "description": "Fat in grams per serving.",
                        },
                        "serving_size": {
                            "type": "number",
                            "description": "Serving size amount (e.g. 100). Defaults to 1.",
                        },
                        "serving_unit": {
                            "type": "string",
                            "description": "Serving unit (e.g. 'g', 'oz', 'cup', 'serving'). Defaults to 'serving'.",
                        },
                    },
                    "required": ["name", "calories", "protein_g", "carbs_g", "fat_g"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "log_workout",
            "description": "Log a workout session with sets. For strength: provide reps and weight. For cardio: provide duration and/or distance. Can log multiple exercises in one session.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "workout_type": {
                            "type": "string",
                            "description": "Type of workout: 'strength', 'cardio', 'flexibility', 'sports', 'other'.",
                            "enum": ["strength", "cardio", "flexibility", "sports", "other"],
                        },
                        "name": {
                            "type": "string",
                            "description": "Optional workout session name (e.g. 'Morning Run', 'Upper Body').",
                        },
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format. Defaults to today.",
                        },
                        "sets": {
                            "type": "array",
                            "description": "List of exercise sets to log.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "exercise_id": {
                                        "type": "string",
                                        "description": "UUID of the exercise (from search_exercises or create_exercise).",
                                    },
                                    "set_type": {
                                        "type": "string",
                                        "description": "'strength' or 'cardio'.",
                                        "enum": ["strength", "cardio"],
                                    },
                                    "reps": {
                                        "type": "integer",
                                        "description": "Number of reps (strength sets).",
                                    },
                                    "weight_kg": {
                                        "type": "number",
                                        "description": "Weight in kg (strength sets). Convert lbs to kg by dividing by 2.205.",
                                    },
                                    "duration_seconds": {
                                        "type": "integer",
                                        "description": "Duration in seconds (cardio sets).",
                                    },
                                    "distance_meters": {
                                        "type": "number",
                                        "description": "Distance in meters (cardio sets). 1 mile = 1609.34m, 1 km = 1000m.",
                                    },
                                },
                                "required": ["exercise_id", "set_type"],
                            },
                        },
                    },
                    "required": ["workout_type", "sets"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "create_exercise",
            "description": "Create a custom exercise. Use when an exercise isn't found via search_exercises. Returns the new exercise with its exercise_id.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Exercise name (e.g. 'Incline Dumbbell Press').",
                        },
                        "category": {
                            "type": "string",
                            "description": "Category: 'strength', 'cardio', 'flexibility', 'sports', 'other'.",
                            "enum": ["strength", "cardio", "flexibility", "sports", "other"],
                        },
                        "muscle_groups": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Target muscle groups (e.g. ['chest', 'shoulders', 'triceps']).",
                        },
                        "equipment": {
                            "type": "string",
                            "description": "Equipment needed (e.g. 'dumbbell', 'barbell', 'bodyweight').",
                        },
                    },
                    "required": ["name", "category"],
                }
            },
        }
    },
]


# ---------------------------------------------------------------------------
# Tool execution helpers
# ---------------------------------------------------------------------------

def _parse_date(date_str: Optional[str]) -> date:
    """Parse a YYYY-MM-DD date string, defaulting to today."""
    if date_str:
        try:
            return date.fromisoformat(date_str)
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}, using today")
    return date.today()


def _serialize(obj: Any) -> Any:
    """Recursively convert non-JSON-serializable types."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(item) for item in obj]
    return obj


# ---------------------------------------------------------------------------
# Individual tool executors
# ---------------------------------------------------------------------------

async def _get_nutrition_summary(user_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    from app.services.nutrition_service import get_nutrition_service
    service = get_nutrition_service()
    summary_date = _parse_date(tool_input.get("date"))
    summary = await service.get_daily_summary(user_id, summary_date)
    return _serialize(summary)


async def _search_foods(user_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    from app.services.nutrition_service import get_nutrition_service
    service = get_nutrition_service()
    query = tool_input.get("query", "")
    foods, total = await service.search_foods(user_id, query, page=1, page_size=10)
    return _serialize({"foods": foods, "total": total})


async def _search_usda_foods(user_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    from app.services.usda_service import get_usda_service
    service = get_usda_service()
    query = tool_input.get("query", "")
    results = await service.search_foods(query, page_size=10)
    # Parse results into our schema format for easier use
    parsed_foods = []
    for food in results.get("foods", [])[:10]:
        parsed = service.parse_food_to_schema(food)
        # Remove USDA-specific IDs that are NOT valid food_ids
        parsed.pop("usda_fdc_id", None)
        parsed.pop("data_type", None)
        parsed.pop("is_verified", None)
        parsed_foods.append(parsed)
    return _serialize({
        "foods": parsed_foods,
        "total": results.get("totalHits", 0),
        "note": "These are USDA results. To log one, first use create_food with the name and macros shown here, then use the returned id as food_id in log_food_entry.",
    })


async def _get_workout_summary(user_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    from app.services.workout_service import get_workout_service
    service = get_workout_service()
    summary_date = _parse_date(tool_input.get("date"))
    summary = await service.get_daily_summary(user_id, summary_date)
    return _serialize(summary)


async def _search_exercises(user_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    from app.services.workout_service import get_workout_service
    service = get_workout_service()
    query = tool_input.get("query", "")
    category = tool_input.get("category")
    exercises, total = await service.search_exercises(
        user_id, query=query, category=category, page=1, page_size=10
    )
    return _serialize({"exercises": exercises, "total": total})


async def _get_whoop_summary(user_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    from app.services.whoop_sync_service import get_whoop_sync_service
    service = get_whoop_sync_service()
    summary = await service.get_dashboard_summary(user_id)
    return _serialize(summary)


def _compute_trend(values: List[Optional[float]], threshold: float = 0.05) -> str:
    """
    Compare first-half vs second-half averages to determine trend direction.

    Returns "improving", "declining", "stable", or "insufficient_data".
    """
    valid = [v for v in values if v is not None]
    if len(valid) < 4:
        return "insufficient_data"

    mid = len(valid) // 2
    first_half = valid[:mid]
    second_half = valid[mid:]

    avg_first = sum(first_half) / len(first_half)
    avg_second = sum(second_half) / len(second_half)

    if avg_first == 0:
        return "stable" if avg_second == 0 else "improving"

    change = (avg_second - avg_first) / abs(avg_first)
    if change > threshold:
        return "improving"
    elif change < -threshold:
        return "declining"
    return "stable"


async def _get_nutrition_trends(user_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    from app.services.nutrition_service import get_nutrition_service
    service = get_nutrition_service()

    start = _parse_date(tool_input.get("start_date"))
    end = _parse_date(tool_input.get("end_date"))

    # Cap range at 30 days
    max_range = timedelta(days=30)
    if (end - start) > max_range:
        start = end - max_range

    if start > end:
        start, end = end, start

    # Fetch goals once
    goals = await service.get_goals(user_id)

    daily_data = []
    current = start
    while current <= end:
        summary = await service.get_daily_summary(user_id, current, goals=goals)
        daily_data.append(_serialize(summary))
        current += timedelta(days=1)

    # Compute averages only for days with logged food
    days_with_food = [d for d in daily_data if float(d.get("total_calories", 0)) > 0]
    days_tracked = len(days_with_food)
    days_in_range = (end - start).days + 1

    averages: Dict[str, Any] = {}
    if days_tracked > 0:
        averages = {
            "calories": round(sum(float(d.get("total_calories", 0)) for d in days_with_food) / days_tracked, 1),
            "protein_g": round(sum(float(d.get("total_protein_g", 0)) for d in days_with_food) / days_tracked, 1),
            "carbs_g": round(sum(float(d.get("total_carbs_g", 0)) for d in days_with_food) / days_tracked, 1),
            "fat_g": round(sum(float(d.get("total_fat_g", 0)) for d in days_with_food) / days_tracked, 1),
        }

    # Goal adherence
    goal_adherence: Dict[str, Any] = {}
    if goals and days_tracked > 0:
        cal_target = float(goals.get("calories_target") or 0)
        protein_target = float(goals.get("protein_g_target") or 0)
        if cal_target > 0:
            goal_adherence["calories_pct"] = round(averages["calories"] / cal_target * 100, 1)
        if protein_target > 0:
            goal_adherence["protein_pct"] = round(averages["protein_g"] / protein_target * 100, 1)

    return {
        "daily_data": daily_data,
        "averages": averages,
        "goals": _serialize(goals) if goals else None,
        "goal_adherence": goal_adherence,
        "days_tracked": days_tracked,
        "days_in_range": days_in_range,
    }


async def _get_workout_progression(user_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    from app.services.workout_service import get_workout_service
    service = get_workout_service()

    exercise_name = tool_input.get("exercise_name", "")
    days = min(tool_input.get("days", 30), 90)

    # Search for the exercise
    exercises, total = await service.search_exercises(user_id, query=exercise_name, page=1, page_size=5)
    if not exercises:
        return {"error": f"Exercise '{exercise_name}' not found. Try searching with search_exercises first."}

    exercise = exercises[0]
    exercise_id = exercise["id"]
    category = exercise.get("category", "strength")

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    if category == "cardio":
        data_points = await service.get_cardio_history(user_id, exercise_id, start_date, end_date)
        summary: Dict[str, Any] = {}
        if len(data_points) >= 2:
            first = data_points[0]
            last = data_points[-1]
            if first.get("avg_pace_seconds_per_km") and last.get("avg_pace_seconds_per_km"):
                pace_change = last["avg_pace_seconds_per_km"] - first["avg_pace_seconds_per_km"]
                summary["pace_change_seconds_per_km"] = pace_change
                summary["pace_improved"] = pace_change < 0  # Lower pace = faster
            if first.get("total_distance_meters") and last.get("total_distance_meters"):
                dist_change_pct = (last["total_distance_meters"] - first["total_distance_meters"]) / first["total_distance_meters"] * 100
                summary["distance_change_pct"] = round(dist_change_pct, 1)
        return _serialize({
            "exercise": {"name": exercise.get("name"), "id": exercise_id, "category": category},
            "type": "cardio",
            "data_points": data_points,
            "total_sessions": len(data_points),
            "summary": summary,
        })
    else:
        data_points = await service.get_exercise_history(user_id, exercise_id, start_date, end_date)
        summary = {}
        if len(data_points) >= 2:
            first = data_points[0]
            last = data_points[-1]
            if first.get("max_weight_kg") and last.get("max_weight_kg"):
                weight_change_pct = (last["max_weight_kg"] - first["max_weight_kg"]) / first["max_weight_kg"] * 100
                summary["weight_change_pct"] = round(weight_change_pct, 1)
            if first.get("total_volume_kg") and last.get("total_volume_kg"):
                vol_change_pct = (last["total_volume_kg"] - first["total_volume_kg"]) / first["total_volume_kg"] * 100
                summary["volume_change_pct"] = round(vol_change_pct, 1)
        return _serialize({
            "exercise": {"name": exercise.get("name"), "id": exercise_id, "category": category},
            "type": "strength",
            "data_points": data_points,
            "total_sessions": len(data_points),
            "summary": summary,
        })


async def _get_workout_trends(user_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    from app.services.workout_service import get_workout_service
    service = get_workout_service()

    weeks = min(tool_input.get("weeks", 4), 12)
    end_date = date.today()
    start_date = end_date - timedelta(weeks=weeks)

    weekly_data = await service.get_workout_trends(user_id, start_date, end_date)
    goals = await service.get_goals(user_id)

    # Compute per-week averages
    averages: Dict[str, Any] = {}
    if weekly_data:
        num_weeks = len(weekly_data)
        averages = {
            "sessions_per_week": round(sum(w.get("total_sessions", 0) for w in weekly_data) / num_weeks, 1),
            "sets_per_week": round(sum(w.get("total_sets", 0) for w in weekly_data) / num_weeks, 1),
            "volume_kg_per_week": round(sum(float(w.get("total_volume_kg") or 0) for w in weekly_data) / num_weeks, 1),
            "duration_minutes_per_week": round(sum(float(w.get("total_duration_minutes") or 0) for w in weekly_data) / num_weeks, 1),
        }

    return _serialize({
        "weekly_data": weekly_data,
        "averages": averages,
        "goals": goals,
        "weeks_analyzed": len(weekly_data),
    })


async def _get_recovery_trends(user_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    from app.services.whoop_sync_service import get_whoop_sync_service
    from app.services.whoop_service import get_whoop_service

    whoop_service = get_whoop_service()
    connection = await whoop_service.get_connection(user_id)
    if not connection:
        return {"error": "Whoop is not connected. The user needs to connect their Whoop account first."}

    days = min(tool_input.get("days", 7), 30)
    sync_service = get_whoop_sync_service()

    recovery_data = await sync_service.get_recovery_trend_data(user_id, days)
    sleep_data = await sync_service.get_sleep_trend_data(user_id, days)

    # Compute averages
    recovery_averages: Dict[str, Any] = {}
    if recovery_data:
        scores = [d["recovery_score"] for d in recovery_data if d.get("recovery_score") is not None]
        hrvs = [d["hrv_rmssd_milli"] for d in recovery_data if d.get("hrv_rmssd_milli") is not None]
        rhrs = [d["resting_heart_rate"] for d in recovery_data if d.get("resting_heart_rate") is not None]
        if scores:
            recovery_averages["recovery_score"] = round(sum(scores) / len(scores), 1)
        if hrvs:
            recovery_averages["hrv_rmssd_milli"] = round(sum(hrvs) / len(hrvs), 1)
        if rhrs:
            recovery_averages["resting_heart_rate"] = round(sum(rhrs) / len(rhrs), 1)

    sleep_averages: Dict[str, Any] = {}
    if sleep_data:
        sleep_hours_list = [d["total_sleep_hours"] for d in sleep_data if d.get("total_sleep_hours")]
        sleep_scores = [d["sleep_score"] for d in sleep_data if d.get("sleep_score") is not None]
        efficiencies = [d["sleep_efficiency"] for d in sleep_data if d.get("sleep_efficiency") is not None]
        if sleep_hours_list:
            sleep_averages["total_sleep_hours"] = round(sum(sleep_hours_list) / len(sleep_hours_list), 2)
        if sleep_scores:
            sleep_averages["sleep_score"] = round(sum(sleep_scores) / len(sleep_scores), 1)
        if efficiencies:
            sleep_averages["sleep_efficiency"] = round(sum(efficiencies) / len(efficiencies), 1)

    # Compute trend directions
    trend: Dict[str, str] = {}
    if recovery_data:
        trend["recovery_score"] = _compute_trend([d.get("recovery_score") for d in recovery_data])
        trend["hrv"] = _compute_trend([d.get("hrv_rmssd_milli") for d in recovery_data])
    if sleep_data:
        trend["sleep_hours"] = _compute_trend([d.get("total_sleep_hours") for d in sleep_data])
        trend["sleep_score"] = _compute_trend([d.get("sleep_score") for d in sleep_data])

    return {
        "recovery_data": recovery_data,
        "sleep_data": sleep_data,
        "recovery_averages": recovery_averages,
        "sleep_averages": sleep_averages,
        "trend": trend,
        "days_with_recovery_data": len(recovery_data),
        "days_with_sleep_data": len(sleep_data),
    }


async def _log_food_entry(user_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    from app.services.nutrition_service import get_nutrition_service
    service = get_nutrition_service()
    entry_date = _parse_date(tool_input.get("date"))
    entry_data = {
        "food_id": tool_input["food_id"],
        "meal_type": tool_input["meal_type"],
        "servings": Decimal(str(tool_input.get("servings", 1))),
        "entry_date": entry_date,
    }
    entry = await service.create_entry(user_id, entry_data)
    if entry:
        return _serialize(entry)
    return {"error": "Failed to create food entry. Check that the food_id is valid."}


async def _create_food(user_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    from app.services.nutrition_service import get_nutrition_service
    service = get_nutrition_service()
    food_data = {
        "name": tool_input["name"],
        "calories": tool_input["calories"],
        "protein_g": tool_input["protein_g"],
        "carbs_g": tool_input["carbs_g"],
        "fat_g": tool_input["fat_g"],
        "serving_size": tool_input.get("serving_size", 1),
        "serving_unit": tool_input.get("serving_unit", "serving"),
    }
    food = await service.create_food(user_id, food_data)
    if food:
        return _serialize(food)
    return {"error": "Failed to create food."}


async def _log_workout(user_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    from app.services.workout_service import get_workout_service
    service = get_workout_service()

    session_date = _parse_date(tool_input.get("date"))
    now = datetime.now(timezone.utc)

    session_data = {
        "session_date": session_date,
        "workout_type": tool_input["workout_type"],
        "name": tool_input.get("name"),
        "start_time": now,
        "end_time": now,
    }

    session = await service.create_session(user_id, session_data)
    session_id = session["id"]

    created_sets = []
    for i, set_data in enumerate(tool_input.get("sets", [])):
        set_record = {
            "exercise_id": set_data["exercise_id"],
            "set_type": set_data["set_type"],
            "set_order": i + 1,
        }
        if set_data["set_type"] == "strength":
            if "reps" in set_data:
                set_record["reps"] = set_data["reps"]
            if "weight_kg" in set_data:
                set_record["weight_kg"] = Decimal(str(set_data["weight_kg"]))
        elif set_data["set_type"] == "cardio":
            if "duration_seconds" in set_data:
                set_record["duration_seconds"] = set_data["duration_seconds"]
            if "distance_meters" in set_data:
                set_record["distance_meters"] = Decimal(str(set_data["distance_meters"]))

        result = await service.create_set(
            user_id, session_id, set_record, skip_ownership_check=True
        )
        if result:
            created_sets.append(result)

    # Clean up orphaned session if no sets were created
    if not created_sets:
        await service.delete_session(session_id, user_id)
        return {"error": "Failed to create any workout sets. Session was not saved."}

    return _serialize({
        "session": session,
        "sets_created": len(created_sets),
    })


async def _create_exercise(user_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    from app.services.workout_service import get_workout_service
    service = get_workout_service()
    exercise_data = {
        "name": tool_input["name"],
        "category": tool_input["category"],
        "muscle_groups": tool_input.get("muscle_groups", []),
        "equipment": tool_input.get("equipment"),
    }
    exercise = await service.create_exercise(user_id, exercise_data)
    return _serialize(exercise)


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

_TOOL_EXECUTORS = {
    "get_nutrition_summary": _get_nutrition_summary,
    "search_foods": _search_foods,
    "search_usda_foods": _search_usda_foods,
    "get_workout_summary": _get_workout_summary,
    "search_exercises": _search_exercises,
    "get_whoop_summary": _get_whoop_summary,
    "get_nutrition_trends": _get_nutrition_trends,
    "get_workout_progression": _get_workout_progression,
    "get_workout_trends": _get_workout_trends,
    "get_recovery_trends": _get_recovery_trends,
    "log_food_entry": _log_food_entry,
    "create_food": _create_food,
    "log_workout": _log_workout,
    "create_exercise": _create_exercise,
}

# Human-readable action summaries for UI display
_TOOL_ACTION_LABELS = {
    "get_nutrition_summary": "Checked nutrition data",
    "search_foods": "Searched foods",
    "search_usda_foods": "Searched USDA database",
    "get_workout_summary": "Checked workout data",
    "search_exercises": "Searched exercises",
    "get_whoop_summary": "Checked Whoop metrics",
    "get_nutrition_trends": "Analyzed nutrition trends",
    "get_workout_progression": "Analyzed exercise progression",
    "get_workout_trends": "Analyzed workout trends",
    "get_recovery_trends": "Analyzed recovery trends",
    "log_food_entry": "Logged food entry",
    "create_food": "Created custom food",
    "log_workout": "Logged workout",
    "create_exercise": "Created exercise",
}


async def execute_tool(
    tool_name: str,
    tool_input: Dict[str, Any],
    user_id: str,
) -> Dict[str, Any]:
    """
    Execute a tool by name and return the result.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters for the tool
        user_id: The authenticated user's ID

    Returns:
        Dict with tool execution result
    """
    executor = _TOOL_EXECUTORS.get(tool_name)
    if not executor:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        logger.info(f"Executing tool: {tool_name} for user {user_id}")
        result = await executor(user_id, tool_input)
        return result
    except Exception as e:
        logger.error(f"Tool execution error ({tool_name}): {e}")
        return {"error": f"Tool '{tool_name}' failed: {str(e)}"}


def get_tool_action_label(tool_name: str) -> str:
    """Get a human-readable label for a tool action."""
    return _TOOL_ACTION_LABELS.get(tool_name, tool_name)
