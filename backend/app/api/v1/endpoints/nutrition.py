"""
Nutrition/Macro Tracking API endpoints.

Provides endpoints for:
- Food items CRUD
- Food entries (meal logging) CRUD
- Daily/weekly summaries
- Nutrition goals
"""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.exceptions import HTTPException

from app.core.logging_config import get_logger
from app.dependencies import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.nutrition import (
    FoodCreate,
    FoodUpdate,
    FoodResponse,
    FoodListResponse,
    FoodSearchResponse,
    FoodEntryCreate,
    FoodEntryUpdate,
    FoodEntryResponse,
    DailySummary,
    WeeklySummary,
    NutritionGoalsCreate,
    NutritionGoalsResponse,
    USDAFoodItem,
    USDASearchResponse,
)
from app.services.nutrition_service import get_nutrition_service
from app.services.usda_service import get_usda_service

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# FOODS ENDPOINTS
# =============================================================================


@router.post(
    "/foods",
    response_model=FoodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom food",
    description="Create a new custom food item",
)
async def create_food(
    food: FoodCreate,
    current_user: UserResponse = Depends(get_current_user),
) -> FoodResponse:
    """Create a custom food item for the user."""
    logger.info(f"Creating food for user {current_user.id}")

    service = get_nutrition_service()
    result = await service.create_food(current_user.id, food.model_dump())

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create food"
        )

    return FoodResponse(**result)


@router.get(
    "/foods/search",
    response_model=FoodSearchResponse,
    summary="Search foods",
    description="Search for foods by name",
)
async def search_foods(
    q: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
) -> FoodSearchResponse:
    """Search foods by name (global + user's custom)."""
    logger.debug(f"Searching foods for user {current_user.id}: {q}")

    service = get_nutrition_service()
    results, total = await service.search_foods(current_user.id, q, page, page_size)

    return FoodSearchResponse(
        results=[FoodResponse(**r) for r in results],
        total=total,
        query=q,
    )


@router.get(
    "/foods/my",
    response_model=FoodListResponse,
    summary="Get my custom foods",
    description="Get user's custom food items",
)
async def get_my_foods(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
) -> FoodListResponse:
    """Get user's custom foods."""
    service = get_nutrition_service()
    data, total = await service.get_user_foods(current_user.id, page, page_size)

    return FoodListResponse(
        data=[FoodResponse(**d) for d in data],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/foods/{food_id}",
    response_model=FoodResponse,
    summary="Get food by ID",
)
async def get_food(
    food_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> FoodResponse:
    """Get a specific food item."""
    service = get_nutrition_service()
    result = await service.get_food(food_id, current_user.id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Food not found"
        )

    return FoodResponse(**result)


@router.put(
    "/foods/{food_id}",
    response_model=FoodResponse,
    summary="Update food",
)
async def update_food(
    food_id: str,
    food: FoodUpdate,
    current_user: UserResponse = Depends(get_current_user),
) -> FoodResponse:
    """Update a custom food item (user can only update their own)."""
    service = get_nutrition_service()
    result = await service.update_food(
        food_id, current_user.id, food.model_dump(exclude_unset=True)
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found or not owned by user",
        )

    return FoodResponse(**result)


@router.delete(
    "/foods/{food_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete food",
)
async def delete_food(
    food_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> None:
    """Delete a custom food item."""
    service = get_nutrition_service()
    success = await service.delete_food(food_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found or not owned by user",
        )


# =============================================================================
# USDA FOOD DATABASE ENDPOINTS
# =============================================================================


@router.get(
    "/foods/usda/search",
    response_model=USDASearchResponse,
    summary="Search USDA food database",
    description="Search the USDA FoodData Central database for foods",
)
async def search_usda_foods(
    q: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    data_type: str = Query(
        "Foundation,SR Legacy",
        description="Comma-separated data types: Foundation, Branded, SR Legacy, Survey (FNDDS)",
    ),
    current_user: UserResponse = Depends(get_current_user),
) -> USDASearchResponse:
    """Search USDA FoodData Central for foods."""
    logger.debug(f"USDA search for user {current_user.id}: {q} (dataType: {data_type})")

    # Parse data_type into list
    data_type_list = [dt.strip() for dt in data_type.split(",") if dt.strip()]

    usda_service = get_usda_service()
    raw_results = await usda_service.search_foods(
        query=q,
        page_size=page_size,
        page_number=page,
        data_type=data_type_list if data_type_list else None,
    )

    # Parse USDA foods into our schema format
    parsed_foods = []
    for food in raw_results.get("foods", []):
        parsed = usda_service.parse_food_to_schema(food)
        parsed_foods.append(
            USDAFoodItem(
                fdc_id=parsed["usda_fdc_id"],
                name=parsed["name"],
                brand=parsed.get("brand"),
                data_type=parsed.get("data_type", "Unknown"),
                serving_size=parsed["serving_size"],
                serving_unit=parsed["serving_unit"],
                calories=parsed["calories"],
                protein_g=parsed["protein_g"],
                carbs_g=parsed["carbs_g"],
                fat_g=parsed["fat_g"],
                fiber_g=parsed.get("fiber_g", 0),
            )
        )

    return USDASearchResponse(
        results=parsed_foods,
        total=raw_results.get("totalHits", 0),
        query=q,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/foods/usda/import",
    response_model=FoodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import food from USDA",
    description="Import a USDA food into user's food list using search result data",
)
async def import_usda_food(
    usda_food: USDAFoodItem,
    current_user: UserResponse = Depends(get_current_user),
) -> FoodResponse:
    """Import a USDA food into the database for the user."""
    logger.info(f"Importing USDA food {usda_food.fdc_id} for user {current_user.id}")

    # Create food in our database using the provided USDA data
    nutrition_service = get_nutrition_service()
    food_data = {
        "name": usda_food.name,
        "brand": usda_food.brand,
        "serving_size": float(usda_food.serving_size),
        "serving_unit": usda_food.serving_unit,
        "calories": float(usda_food.calories),
        "protein_g": float(usda_food.protein_g),
        "carbs_g": float(usda_food.carbs_g),
        "fat_g": float(usda_food.fat_g),
        "fiber_g": float(usda_food.fiber_g) if usda_food.fiber_g else 0,
        "is_verified": True,
    }

    result = await nutrition_service.create_food(current_user.id, food_data)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to import food",
        )

    return FoodResponse(**result)


# =============================================================================
# FOOD ENTRIES ENDPOINTS
# =============================================================================


@router.post(
    "/entries",
    response_model=FoodEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log food entry",
    description="Log a food entry (meal)",
)
async def create_entry(
    entry: FoodEntryCreate,
    current_user: UserResponse = Depends(get_current_user),
) -> FoodEntryResponse:
    """Create a food entry (log a meal)."""
    logger.info(f"Logging food entry for user {current_user.id}")

    service = get_nutrition_service()
    result = await service.create_entry(current_user.id, entry.model_dump())

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create entry"
        )

    return FoodEntryResponse(**result)


@router.get(
    "/entries/{entry_id}",
    response_model=FoodEntryResponse,
    summary="Get entry by ID",
)
async def get_entry(
    entry_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> FoodEntryResponse:
    """Get a specific food entry."""
    service = get_nutrition_service()
    result = await service.get_entry(entry_id, current_user.id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found"
        )

    return FoodEntryResponse(**result)


@router.put(
    "/entries/{entry_id}",
    response_model=FoodEntryResponse,
    summary="Update entry",
)
async def update_entry(
    entry_id: str,
    entry: FoodEntryUpdate,
    current_user: UserResponse = Depends(get_current_user),
) -> FoodEntryResponse:
    """Update a food entry."""
    service = get_nutrition_service()
    result = await service.update_entry(
        entry_id, current_user.id, entry.model_dump(exclude_unset=True)
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found"
        )

    return FoodEntryResponse(**result)


@router.delete(
    "/entries/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete entry",
)
async def delete_entry(
    entry_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> None:
    """Delete a food entry."""
    service = get_nutrition_service()
    success = await service.delete_entry(entry_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found"
        )


# =============================================================================
# SUMMARY ENDPOINTS
# =============================================================================


@router.get(
    "/summary/daily",
    response_model=DailySummary,
    summary="Get daily summary",
    description="Get nutrition summary for a specific date",
)
async def get_daily_summary(
    summary_date: date = Query(default=None, description="Date (defaults to today)"),
    current_user: UserResponse = Depends(get_current_user),
) -> DailySummary:
    """Get daily nutrition summary."""
    if summary_date is None:
        summary_date = date.today()

    service = get_nutrition_service()
    result = await service.get_daily_summary(current_user.id, summary_date)

    return DailySummary(**result)


@router.get(
    "/summary/weekly",
    response_model=WeeklySummary,
    summary="Get weekly summary",
    description="Get nutrition summary for a week",
)
async def get_weekly_summary(
    start_date: date = Query(
        default=None, description="Week start date (defaults to this Monday)"
    ),
    current_user: UserResponse = Depends(get_current_user),
) -> WeeklySummary:
    """Get weekly nutrition summary."""
    if start_date is None:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())  # Monday

    service = get_nutrition_service()
    result = await service.get_weekly_summary(current_user.id, start_date)

    return WeeklySummary(**result)


# =============================================================================
# GOALS ENDPOINTS
# =============================================================================


@router.get(
    "/goals",
    response_model=Optional[NutritionGoalsResponse],
    summary="Get nutrition goals",
)
async def get_goals(
    current_user: UserResponse = Depends(get_current_user),
) -> Optional[NutritionGoalsResponse]:
    """Get user's nutrition goals. Returns null if not set."""
    service = get_nutrition_service()
    result = await service.get_goals(current_user.id)

    if not result:
        return None

    return NutritionGoalsResponse(**result)


@router.put(
    "/goals",
    response_model=NutritionGoalsResponse,
    summary="Set nutrition goals",
)
async def set_goals(
    goals: NutritionGoalsCreate,
    current_user: UserResponse = Depends(get_current_user),
) -> NutritionGoalsResponse:
    """Create or update nutrition goals."""
    service = get_nutrition_service()
    result = await service.upsert_goals(current_user.id, goals.model_dump())

    return NutritionGoalsResponse(**result)
