"""
Pydantic schemas for Nutrition/Macro tracking.

Defines request/response models for:
- Food items (CRUD)
- Food entries (logging meals)
- Daily/weekly summaries
- Nutrition goals
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Literal

from pydantic import BaseModel, Field


# =============================================================================
# Food Schemas
# =============================================================================

class FoodBase(BaseModel):
    """Base schema for food items."""

    name: str = Field(..., min_length=1, max_length=255, description="Food name")
    brand: Optional[str] = Field(None, max_length=255, description="Brand name")
    serving_size: Decimal = Field(..., gt=0, description="Serving size amount")
    serving_unit: str = Field("g", description="Serving unit (g, ml, oz, cup, piece)")
    calories: Decimal = Field(..., ge=0, description="Calories per serving")
    protein_g: Decimal = Field(0, ge=0, description="Protein in grams")
    carbs_g: Decimal = Field(0, ge=0, description="Carbohydrates in grams")
    fat_g: Decimal = Field(0, ge=0, description="Fat in grams")
    fiber_g: Optional[Decimal] = Field(0, ge=0, description="Fiber in grams")
    sugar_g: Optional[Decimal] = Field(0, ge=0, description="Sugar in grams")
    sodium_mg: Optional[Decimal] = Field(0, ge=0, description="Sodium in milligrams")
    barcode: Optional[str] = Field(None, description="UPC/EAN barcode")


class FoodCreate(FoodBase):
    """Schema for creating a new food item."""

    pass


class FoodUpdate(BaseModel):
    """Schema for updating a food item (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=255)
    serving_size: Optional[Decimal] = Field(None, gt=0)
    serving_unit: Optional[str] = None
    calories: Optional[Decimal] = Field(None, ge=0)
    protein_g: Optional[Decimal] = Field(None, ge=0)
    carbs_g: Optional[Decimal] = Field(None, ge=0)
    fat_g: Optional[Decimal] = Field(None, ge=0)
    fiber_g: Optional[Decimal] = Field(None, ge=0)
    sugar_g: Optional[Decimal] = Field(None, ge=0)
    sodium_mg: Optional[Decimal] = Field(None, ge=0)
    barcode: Optional[str] = None


class FoodResponse(FoodBase):
    """Food item response."""

    id: str = Field(..., description="Database UUID")
    user_id: Optional[str] = Field(None, description="Owner user ID (null for global)")
    is_verified: bool = Field(False, description="Admin verified")
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Food Entry Schemas
# =============================================================================

MealType = Literal["breakfast", "lunch", "dinner", "snack"]


class FoodEntryBase(BaseModel):
    """Base schema for food entries."""

    food_id: str = Field(..., description="Food item UUID")
    entry_date: date = Field(..., description="Date of the entry")
    meal_type: MealType = Field(..., description="Meal type")
    servings: Decimal = Field(1, gt=0, description="Number of servings")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")


class FoodEntryCreate(FoodEntryBase):
    """Schema for creating a food entry."""

    pass


class FoodEntryUpdate(BaseModel):
    """Schema for updating a food entry."""

    food_id: Optional[str] = None
    entry_date: Optional[date] = None
    meal_type: Optional[MealType] = None
    servings: Optional[Decimal] = Field(None, gt=0)
    notes: Optional[str] = Field(None, max_length=500)


class FoodEntryResponse(FoodEntryBase):
    """Food entry response with computed macros."""

    id: str = Field(..., description="Database UUID")
    user_id: str
    logged_at: datetime
    created_at: datetime

    # Include food details for display
    food: Optional[FoodResponse] = None

    # Computed values (servings * food macros)
    total_calories: Optional[Decimal] = None
    total_protein_g: Optional[Decimal] = None
    total_carbs_g: Optional[Decimal] = None
    total_fat_g: Optional[Decimal] = None

    class Config:
        from_attributes = True


# =============================================================================
# Daily Summary Schemas
# =============================================================================

class MealSummary(BaseModel):
    """Summary for a single meal."""

    meal_type: MealType
    entries: list[FoodEntryResponse] = Field(default_factory=list)
    total_calories: Decimal = Decimal("0")
    total_protein_g: Decimal = Decimal("0")
    total_carbs_g: Decimal = Decimal("0")
    total_fat_g: Decimal = Decimal("0")


class DailySummary(BaseModel):
    """Daily nutrition summary."""

    date: date
    meals: list[MealSummary] = Field(default_factory=list)

    # Daily totals
    total_calories: Decimal = Decimal("0")
    total_protein_g: Decimal = Decimal("0")
    total_carbs_g: Decimal = Decimal("0")
    total_fat_g: Decimal = Decimal("0")
    total_fiber_g: Decimal = Decimal("0")

    # Goals (if set)
    calories_target: Optional[Decimal] = None
    protein_g_target: Optional[Decimal] = None
    carbs_g_target: Optional[Decimal] = None
    fat_g_target: Optional[Decimal] = None


class WeeklySummary(BaseModel):
    """Weekly nutrition summary."""

    start_date: date
    end_date: date
    daily_summaries: list[DailySummary] = Field(default_factory=list)

    # Weekly averages
    avg_calories: Decimal = Decimal("0")
    avg_protein_g: Decimal = Decimal("0")
    avg_carbs_g: Decimal = Decimal("0")
    avg_fat_g: Decimal = Decimal("0")


# =============================================================================
# Nutrition Goals Schemas
# =============================================================================

class NutritionGoalsBase(BaseModel):
    """Base schema for nutrition goals."""

    calories_target: Optional[Decimal] = Field(None, ge=0)
    protein_g_target: Optional[Decimal] = Field(None, ge=0)
    carbs_g_target: Optional[Decimal] = Field(None, ge=0)
    fat_g_target: Optional[Decimal] = Field(None, ge=0)
    fiber_g_target: Optional[Decimal] = Field(None, ge=0)


class NutritionGoalsCreate(NutritionGoalsBase):
    """Schema for creating/updating nutrition goals."""

    pass


class NutritionGoalsResponse(NutritionGoalsBase):
    """Nutrition goals response."""

    id: str
    user_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# List Response Schemas
# =============================================================================

class FoodListResponse(BaseModel):
    """Paginated list of foods."""

    data: list[FoodResponse] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class FoodEntryListResponse(BaseModel):
    """Paginated list of food entries."""

    data: list[FoodEntryResponse] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class FoodSearchResponse(BaseModel):
    """Search results for foods."""

    results: list[FoodResponse] = Field(default_factory=list)
    total: int = 0
    query: str


# =============================================================================
# USDA Food Schemas
# =============================================================================


class USDAFoodItem(BaseModel):
    """USDA food item from search results."""

    fdc_id: str = Field(..., description="USDA FoodData Central ID")
    name: str = Field(..., description="Food description")
    brand: Optional[str] = Field(None, description="Brand owner or name")
    data_type: str = Field(..., description="USDA data type (Branded, Foundation, etc.)")
    serving_size: Decimal = Field(100, description="Serving size in grams")
    serving_unit: str = Field("g", description="Serving unit")
    calories: Decimal = Field(0, description="Calories per serving")
    protein_g: Decimal = Field(0, description="Protein in grams")
    carbs_g: Decimal = Field(0, description="Carbohydrates in grams")
    fat_g: Decimal = Field(0, description="Fat in grams")
    fiber_g: Optional[Decimal] = Field(0, description="Fiber in grams")


class USDASearchResponse(BaseModel):
    """USDA food search response."""

    results: list[USDAFoodItem] = Field(default_factory=list)
    total: int = 0
    query: str
    page: int = 1
    page_size: int = 20
