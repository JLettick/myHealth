"""
Nutrition tracking service.

Handles:
- Food CRUD operations
- Food entry logging
- Daily/weekly summaries
- Nutrition goals management
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from app.core.logging_config import get_logger
from app.services.supabase_client import SupabaseService, get_supabase_service

logger = get_logger(__name__)


class NutritionService:
    """Service for nutrition/macro tracking operations."""

    def __init__(self, supabase: Optional[SupabaseService] = None):
        self.supabase = supabase or get_supabase_service()

    # =========================================================================
    # FOODS CRUD
    # =========================================================================

    async def create_food(self, user_id: str, food_data: dict[str, Any]) -> dict[str, Any]:
        """Create a custom food item for a user."""
        logger.info(f"Creating food for user {user_id}: {food_data.get('name')}")

        data = {
            "user_id": user_id,
            "is_verified": False,
            **food_data,
        }

        # Convert Decimal to float for JSON serialization
        for key in ["serving_size", "calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g", "sodium_mg"]:
            if key in data and data[key] is not None:
                data[key] = float(data[key])

        response = self.supabase.admin_client.table("foods").insert(data).execute()

        return response.data[0] if response.data else None

    async def get_food(self, food_id: str, user_id: str) -> Optional[dict[str, Any]]:
        """Get a food item by ID (must be global or owned by user)."""
        response = (
            self.supabase.admin_client.table("foods")
            .select("*")
            .eq("id", food_id)
            .execute()
        )

        if not response.data:
            return None

        food = response.data[0]
        # Check access: global food or owned by user
        if food["user_id"] is not None and food["user_id"] != user_id:
            return None

        return food

    async def update_food(
        self, food_id: str, user_id: str, update_data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Update a user's custom food item."""
        # Convert Decimal to float
        for key in ["serving_size", "calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g", "sodium_mg"]:
            if key in update_data and update_data[key] is not None:
                update_data[key] = float(update_data[key])

        response = (
            self.supabase.admin_client.table("foods")
            .update(update_data)
            .eq("id", food_id)
            .eq("user_id", user_id)
            .execute()
        )

        return response.data[0] if response.data else None

    async def delete_food(self, food_id: str, user_id: str) -> bool:
        """Delete a user's custom food item."""
        response = (
            self.supabase.admin_client.table("foods")
            .delete()
            .eq("id", food_id)
            .eq("user_id", user_id)
            .execute()
        )

        return len(response.data) > 0

    async def search_foods(
        self, user_id: str, query: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[dict], int]:
        """Search foods by name (global + user's custom foods)."""
        offset = (page - 1) * page_size

        # Use ilike for case-insensitive search
        response = (
            self.supabase.admin_client.table("foods")
            .select("*", count="exact")
            .or_(f"user_id.is.null,user_id.eq.{user_id}")
            .ilike("name", f"%{query}%")
            .order("is_verified", desc=True)
            .order("name")
            .range(offset, offset + page_size - 1)
            .execute()
        )

        return response.data, response.count or 0

    async def get_user_foods(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[dict], int]:
        """Get user's custom foods."""
        offset = (page - 1) * page_size

        response = (
            self.supabase.admin_client.table("foods")
            .select("*", count="exact")
            .eq("user_id", user_id)
            .order("name")
            .range(offset, offset + page_size - 1)
            .execute()
        )

        return response.data, response.count or 0

    # =========================================================================
    # FOOD ENTRIES CRUD
    # =========================================================================

    async def create_entry(
        self, user_id: str, entry_data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Create a food entry (log a meal)."""
        logger.info(f"Creating food entry for user {user_id}")

        data = {
            "user_id": user_id,
            "logged_at": datetime.now(timezone.utc).isoformat(),
            **entry_data,
        }

        # Convert date to string and Decimal to float
        if "entry_date" in data and isinstance(data["entry_date"], date):
            data["entry_date"] = data["entry_date"].isoformat()
        if "servings" in data:
            data["servings"] = float(data["servings"])

        response = self.supabase.admin_client.table("food_entries").insert(data).execute()

        if response.data:
            return await self.get_entry(response.data[0]["id"], user_id)

        return None

    async def get_entry(self, entry_id: str, user_id: str) -> Optional[dict[str, Any]]:
        """Get a food entry with food details."""
        response = (
            self.supabase.admin_client.table("food_entries")
            .select("*, foods(*)")
            .eq("id", entry_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            return None

        entry = response.data[0]
        entry = self._compute_entry_totals(entry)
        return entry

    async def update_entry(
        self, entry_id: str, user_id: str, update_data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Update a food entry."""
        # Convert types
        if "entry_date" in update_data and isinstance(update_data["entry_date"], date):
            update_data["entry_date"] = update_data["entry_date"].isoformat()
        if "servings" in update_data:
            update_data["servings"] = float(update_data["servings"])

        response = (
            self.supabase.admin_client.table("food_entries")
            .update(update_data)
            .eq("id", entry_id)
            .eq("user_id", user_id)
            .execute()
        )

        if response.data:
            return await self.get_entry(entry_id, user_id)
        return None

    async def delete_entry(self, entry_id: str, user_id: str) -> bool:
        """Delete a food entry."""
        response = (
            self.supabase.admin_client.table("food_entries")
            .delete()
            .eq("id", entry_id)
            .eq("user_id", user_id)
            .execute()
        )

        return len(response.data) > 0

    async def get_entries_by_date(
        self, user_id: str, entry_date: date
    ) -> list[dict[str, Any]]:
        """Get all food entries for a specific date."""
        response = (
            self.supabase.admin_client.table("food_entries")
            .select("*, foods(*)")
            .eq("user_id", user_id)
            .eq("entry_date", entry_date.isoformat())
            .order("logged_at")
            .execute()
        )

        return [self._compute_entry_totals(e) for e in response.data]

    # =========================================================================
    # SUMMARIES
    # =========================================================================

    async def get_daily_summary(self, user_id: str, summary_date: date) -> dict[str, Any]:
        """Get daily nutrition summary with meal breakdowns."""
        entries = await self.get_entries_by_date(user_id, summary_date)
        goals = await self.get_goals(user_id)

        # Group entries by meal type
        meals = []
        for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
            meal_entries = [e for e in entries if e["meal_type"] == meal_type]
            meals.append({
                "meal_type": meal_type,
                "entries": meal_entries,
                "total_calories": sum(
                    Decimal(str(e.get("total_calories", 0) or 0)) for e in meal_entries
                ),
                "total_protein_g": sum(
                    Decimal(str(e.get("total_protein_g", 0) or 0)) for e in meal_entries
                ),
                "total_carbs_g": sum(
                    Decimal(str(e.get("total_carbs_g", 0) or 0)) for e in meal_entries
                ),
                "total_fat_g": sum(
                    Decimal(str(e.get("total_fat_g", 0) or 0)) for e in meal_entries
                ),
            })

        # Calculate daily totals
        total_calories = sum(Decimal(str(m["total_calories"])) for m in meals)
        total_protein = sum(Decimal(str(m["total_protein_g"])) for m in meals)
        total_carbs = sum(Decimal(str(m["total_carbs_g"])) for m in meals)
        total_fat = sum(Decimal(str(m["total_fat_g"])) for m in meals)
        total_fiber = sum(
            Decimal(str(e.get("foods", {}).get("fiber_g", 0) or 0)) * Decimal(str(e.get("servings", 1)))
            for e in entries
        )

        return {
            "date": summary_date,
            "meals": meals,
            "total_calories": total_calories,
            "total_protein_g": total_protein,
            "total_carbs_g": total_carbs,
            "total_fat_g": total_fat,
            "total_fiber_g": total_fiber,
            "calories_target": Decimal(str(goals["calories_target"])) if goals and goals.get("calories_target") else None,
            "protein_g_target": Decimal(str(goals["protein_g_target"])) if goals and goals.get("protein_g_target") else None,
            "carbs_g_target": Decimal(str(goals["carbs_g_target"])) if goals and goals.get("carbs_g_target") else None,
            "fat_g_target": Decimal(str(goals["fat_g_target"])) if goals and goals.get("fat_g_target") else None,
        }

    async def get_weekly_summary(self, user_id: str, start_date: date) -> dict[str, Any]:
        """Get weekly nutrition summary."""
        daily_summaries = []

        for i in range(7):
            day = start_date + timedelta(days=i)
            summary = await self.get_daily_summary(user_id, day)
            daily_summaries.append(summary)

        # Calculate averages
        days_with_data = [d for d in daily_summaries if d["total_calories"] > 0]
        count = len(days_with_data) or 1

        return {
            "start_date": start_date,
            "end_date": start_date + timedelta(days=6),
            "daily_summaries": daily_summaries,
            "avg_calories": sum(d["total_calories"] for d in days_with_data) / count,
            "avg_protein_g": sum(d["total_protein_g"] for d in days_with_data) / count,
            "avg_carbs_g": sum(d["total_carbs_g"] for d in days_with_data) / count,
            "avg_fat_g": sum(d["total_fat_g"] for d in days_with_data) / count,
        }

    # =========================================================================
    # NUTRITION GOALS
    # =========================================================================

    async def get_goals(self, user_id: str) -> Optional[dict[str, Any]]:
        """Get user's nutrition goals."""
        response = (
            self.supabase.admin_client.table("nutrition_goals")
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
        """Create or update user's nutrition goals."""
        data = {
            "user_id": user_id,
            "is_active": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            **goals_data,
        }

        # Convert Decimal to float
        for key in ["calories_target", "protein_g_target", "carbs_g_target", "fat_g_target", "fiber_g_target"]:
            if key in data and data[key] is not None:
                data[key] = float(data[key])

        response = (
            self.supabase.admin_client.table("nutrition_goals")
            .upsert(data, on_conflict="user_id")
            .execute()
        )

        return response.data[0] if response.data else None

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _compute_entry_totals(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Compute total macros for an entry based on servings."""
        food = entry.get("foods", {}) or {}
        servings = Decimal(str(entry.get("servings", 1)))

        entry["food"] = food
        entry["total_calories"] = float(Decimal(str(food.get("calories", 0) or 0)) * servings)
        entry["total_protein_g"] = float(Decimal(str(food.get("protein_g", 0) or 0)) * servings)
        entry["total_carbs_g"] = float(Decimal(str(food.get("carbs_g", 0) or 0)) * servings)
        entry["total_fat_g"] = float(Decimal(str(food.get("fat_g", 0) or 0)) * servings)

        return entry


# Singleton instance
_nutrition_service: Optional[NutritionService] = None


def get_nutrition_service() -> NutritionService:
    """Get the Nutrition service singleton."""
    global _nutrition_service
    if _nutrition_service is None:
        _nutrition_service = NutritionService()
    return _nutrition_service
