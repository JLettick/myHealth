"""
USDA FoodData Central API service.

Provides access to the USDA food database for searching and retrieving
nutritional information.

API Documentation: https://fdc.nal.usda.gov/api-guide.html
"""

from typing import Any, Optional

import httpx

from app.config import Settings, get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class USDAService:
    """Service for interacting with USDA FoodData Central API."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.base_url = self.settings.usda_api_base_url
        self.api_key = self.settings.usda_api_key

    async def search_foods(
        self,
        query: str,
        page_size: int = 20,
        page_number: int = 1,
        data_type: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Search for foods in the USDA database.

        Args:
            query: Search query string
            page_size: Number of results per page (max 200)
            page_number: Page number (1-indexed)
            data_type: Filter by data type (e.g., ["Foundation", "SR Legacy", "Branded"])

        Returns:
            Search results with foods and pagination info
        """
        if not self.api_key:
            logger.warning("USDA API key not configured")
            return {"foods": [], "totalHits": 0}

        url = f"{self.base_url}/foods/search"
        params = {
            "api_key": self.api_key,
            "query": query,
            "pageSize": min(page_size, 200),
            "pageNumber": page_number,
        }

        if data_type:
            params["dataType"] = ",".join(data_type)

        logger.debug(f"Searching USDA foods: {query}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                logger.info(f"USDA search returned {data.get('totalHits', 0)} results for '{query}'")
                return data

            except httpx.HTTPStatusError as e:
                logger.error(f"USDA API error: {e.response.status_code}")
                return {"foods": [], "totalHits": 0, "error": str(e)}
            except httpx.RequestError as e:
                logger.error(f"USDA request failed: {e}")
                return {"foods": [], "totalHits": 0, "error": str(e)}

    async def get_food(self, fdc_id: str) -> Optional[dict[str, Any]]:
        """
        Get detailed food information by FDC ID.

        Args:
            fdc_id: USDA FoodData Central ID

        Returns:
            Food details or None if not found
        """
        if not self.api_key:
            logger.warning("USDA API key not configured")
            return None

        url = f"{self.base_url}/food/{fdc_id}"
        params = {"api_key": self.api_key}

        logger.debug(f"Fetching USDA food: {url}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(f"USDA API error for FDC {fdc_id}: {e.response.status_code} - {e.response.text}")
                return None
            except httpx.RequestError as e:
                logger.error(f"USDA request failed for FDC {fdc_id}: {type(e).__name__} - {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error fetching USDA food {fdc_id}: {type(e).__name__} - {e}")
                return None

    def parse_food_to_schema(self, usda_food: dict[str, Any]) -> dict[str, Any]:
        """
        Parse USDA food data into our Food schema format.

        Args:
            usda_food: Raw USDA food data

        Returns:
            Food data matching our schema
        """
        # Extract nutrients
        nutrients = {}
        for nutrient in usda_food.get("foodNutrients", []):
            nutrient_id = nutrient.get("nutrientId") or nutrient.get("nutrient", {}).get("id")
            value = nutrient.get("value") or nutrient.get("amount", 0)

            # Map nutrient IDs to our fields
            # 1008 = Energy (kcal), 1003 = Protein, 1005 = Carbs, 1004 = Fat, 1079 = Fiber
            if nutrient_id == 1008:
                nutrients["calories"] = value
            elif nutrient_id == 1003:
                nutrients["protein_g"] = value
            elif nutrient_id == 1005:
                nutrients["carbs_g"] = value
            elif nutrient_id == 1004:
                nutrients["fat_g"] = value
            elif nutrient_id == 1079:
                nutrients["fiber_g"] = value
            elif nutrient_id == 1063:
                nutrients["sugar_g"] = value
            elif nutrient_id == 1093:
                nutrients["sodium_mg"] = value

        # Get serving size info
        serving_size = 100  # Default to 100g
        serving_unit = "g"

        # Check for serving size in food portions
        portions = usda_food.get("foodPortions", [])
        if portions:
            portion = portions[0]
            serving_size = portion.get("gramWeight", 100)
            serving_unit = "g"

        return {
            "usda_fdc_id": str(usda_food.get("fdcId")),
            "name": usda_food.get("description", "Unknown"),
            "brand": usda_food.get("brandOwner") or usda_food.get("brandName"),
            "serving_size": serving_size,
            "serving_unit": serving_unit,
            "calories": nutrients.get("calories", 0),
            "protein_g": nutrients.get("protein_g", 0),
            "carbs_g": nutrients.get("carbs_g", 0),
            "fat_g": nutrients.get("fat_g", 0),
            "fiber_g": nutrients.get("fiber_g", 0),
            "sugar_g": nutrients.get("sugar_g", 0),
            "sodium_mg": nutrients.get("sodium_mg", 0),
            "is_verified": True,  # USDA data is verified
            "data_type": usda_food.get("dataType", "Unknown"),
        }


# Singleton instance
_usda_service: Optional[USDAService] = None


def get_usda_service() -> USDAService:
    """Get the USDA service singleton."""
    global _usda_service
    if _usda_service is None:
        _usda_service = USDAService()
    return _usda_service
