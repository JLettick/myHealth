"""
Pydantic schemas for Workout Tracking.

Defines request/response models for:
- Exercises (master list)
- Workout sessions (containers)
- Workout sets (individual entries)
- Workout goals
- Summaries
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Literal

from pydantic import BaseModel, Field


# =============================================================================
# Type Definitions
# =============================================================================

ExerciseCategory = Literal["strength", "cardio", "flexibility", "sports", "other"]
WorkoutType = Literal["strength", "cardio", "mixed", "flexibility", "sports", "other"]
SetType = Literal["strength", "cardio"]


# =============================================================================
# Exercise Schemas
# =============================================================================

class ExerciseBase(BaseModel):
    """Base schema for exercises."""

    name: str = Field(..., min_length=1, max_length=255, description="Exercise name")
    category: ExerciseCategory = Field(..., description="Exercise category")
    muscle_groups: list[str] = Field(default_factory=list, description="Target muscle groups")
    equipment: Optional[str] = Field(None, max_length=100, description="Equipment needed")
    description: Optional[str] = Field(None, max_length=500, description="Exercise description")


class ExerciseCreate(ExerciseBase):
    """Schema for creating a new exercise."""

    pass


class ExerciseUpdate(BaseModel):
    """Schema for updating an exercise (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[ExerciseCategory] = None
    muscle_groups: Optional[list[str]] = None
    equipment: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class ExerciseResponse(ExerciseBase):
    """Exercise response."""

    id: str = Field(..., description="Database UUID")
    user_id: Optional[str] = Field(None, description="Owner user ID (null for global)")
    is_verified: bool = Field(False, description="Admin verified")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Workout Set Schemas
# =============================================================================

class WorkoutSetBase(BaseModel):
    """Base schema for workout sets."""

    exercise_id: str = Field(..., description="Exercise UUID")
    set_type: SetType = Field(..., description="Type of set (strength/cardio)")
    set_order: int = Field(1, ge=1, description="Order within session")
    notes: Optional[str] = Field(None, max_length=500, description="Set notes")


class StrengthSetMixin(BaseModel):
    """Strength-specific fields."""

    reps: Optional[int] = Field(None, gt=0, description="Number of repetitions")
    weight_kg: Optional[Decimal] = Field(None, ge=0, description="Weight in kg")
    rpe: Optional[Decimal] = Field(None, ge=1, le=10, description="Rate of perceived exertion (1-10)")
    is_warmup: bool = Field(False, description="Is this a warmup set")
    is_failure: bool = Field(False, description="Did the set go to failure")


class CardioSetMixin(BaseModel):
    """Cardio-specific fields."""

    duration_seconds: Optional[int] = Field(None, gt=0, description="Duration in seconds")
    distance_meters: Optional[Decimal] = Field(None, ge=0, description="Distance in meters")
    pace_seconds_per_km: Optional[int] = Field(None, description="Pace in seconds per km")
    calories_burned: Optional[int] = Field(None, ge=0, description="Calories burned")
    avg_heart_rate: Optional[int] = Field(None, ge=0, description="Average heart rate")
    max_heart_rate: Optional[int] = Field(None, ge=0, description="Maximum heart rate")
    elevation_gain_meters: Optional[Decimal] = Field(None, ge=0, description="Elevation gain in meters")


class WorkoutSetCreate(WorkoutSetBase, StrengthSetMixin, CardioSetMixin):
    """Schema for creating a workout set."""

    pass


class WorkoutSetUpdate(BaseModel):
    """Schema for updating a workout set (all fields optional)."""

    exercise_id: Optional[str] = None
    set_type: Optional[SetType] = None
    set_order: Optional[int] = Field(None, ge=1)
    notes: Optional[str] = Field(None, max_length=500)

    # Strength fields
    reps: Optional[int] = Field(None, gt=0)
    weight_kg: Optional[Decimal] = Field(None, ge=0)
    rpe: Optional[Decimal] = Field(None, ge=1, le=10)
    is_warmup: Optional[bool] = None
    is_failure: Optional[bool] = None

    # Cardio fields
    duration_seconds: Optional[int] = Field(None, gt=0)
    distance_meters: Optional[Decimal] = Field(None, ge=0)
    pace_seconds_per_km: Optional[int] = None
    calories_burned: Optional[int] = Field(None, ge=0)
    avg_heart_rate: Optional[int] = Field(None, ge=0)
    max_heart_rate: Optional[int] = Field(None, ge=0)
    elevation_gain_meters: Optional[Decimal] = Field(None, ge=0)


class WorkoutSetResponse(WorkoutSetBase, StrengthSetMixin, CardioSetMixin):
    """Workout set response."""

    id: str = Field(..., description="Database UUID")
    user_id: str
    session_id: str
    created_at: datetime
    updated_at: datetime

    # Include exercise details for display
    exercise: Optional[ExerciseResponse] = None

    class Config:
        from_attributes = True


# =============================================================================
# Workout Session Schemas
# =============================================================================

class WorkoutSessionBase(BaseModel):
    """Base schema for workout sessions."""

    session_date: date = Field(..., description="Date of the workout")
    workout_type: WorkoutType = Field(..., description="Type of workout")
    name: Optional[str] = Field(None, max_length=255, description="Session name (e.g., 'Leg Day')")
    start_time: Optional[datetime] = Field(None, description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")
    notes: Optional[str] = Field(None, max_length=1000, description="Session notes")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Workout rating (1-5)")


class WorkoutSessionCreate(WorkoutSessionBase):
    """Schema for creating a workout session."""

    whoop_workout_id: Optional[str] = Field(None, description="Link to Whoop workout")


class WorkoutSessionUpdate(BaseModel):
    """Schema for updating a workout session (all fields optional)."""

    session_date: Optional[date] = None
    workout_type: Optional[WorkoutType] = None
    name: Optional[str] = Field(None, max_length=255)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)
    rating: Optional[int] = Field(None, ge=1, le=5)
    whoop_workout_id: Optional[str] = None


class WorkoutSessionResponse(WorkoutSessionBase):
    """Workout session response."""

    id: str = Field(..., description="Database UUID")
    user_id: str
    whoop_workout_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Include sets for full session details
    sets: list[WorkoutSetResponse] = Field(default_factory=list)

    # Computed values
    total_sets: int = 0
    total_duration_minutes: Optional[int] = None

    class Config:
        from_attributes = True


class WorkoutSessionListItem(WorkoutSessionBase):
    """Workout session list item (without nested sets for performance)."""

    id: str = Field(..., description="Database UUID")
    user_id: str
    whoop_workout_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    total_sets: int = 0
    total_duration_minutes: Optional[int] = None

    class Config:
        from_attributes = True


# =============================================================================
# Workout Goals Schemas
# =============================================================================

class WorkoutGoalsBase(BaseModel):
    """Base schema for workout goals."""

    workouts_per_week_target: Optional[int] = Field(None, ge=0, description="Target workouts per week")
    minutes_per_week_target: Optional[int] = Field(None, ge=0, description="Target minutes per week")


class WorkoutGoalsCreate(WorkoutGoalsBase):
    """Schema for creating/updating workout goals."""

    pass


class WorkoutGoalsResponse(WorkoutGoalsBase):
    """Workout goals response."""

    id: str
    user_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Summary Schemas
# =============================================================================

class ExerciseSummary(BaseModel):
    """Summary for a specific exercise in a day/week."""

    exercise_id: str
    exercise_name: str
    category: ExerciseCategory
    total_sets: int = 0
    total_reps: Optional[int] = None
    max_weight_kg: Optional[Decimal] = None
    total_volume_kg: Optional[Decimal] = None  # weight * reps across sets
    total_duration_seconds: Optional[int] = None
    total_distance_meters: Optional[Decimal] = None


class DailyWorkoutSummary(BaseModel):
    """Daily workout summary."""

    date: date
    sessions: list[WorkoutSessionListItem] = Field(default_factory=list)
    exercises: list[ExerciseSummary] = Field(default_factory=list)

    # Daily totals
    total_sessions: int = 0
    total_sets: int = 0
    total_duration_minutes: int = 0
    total_volume_kg: Optional[Decimal] = None  # Total weight * reps
    total_distance_meters: Optional[Decimal] = None

    # Goals (if set)
    workouts_per_week_target: Optional[int] = None
    minutes_per_week_target: Optional[int] = None


class WeeklyWorkoutSummary(BaseModel):
    """Weekly workout summary."""

    start_date: date
    end_date: date
    daily_summaries: list[DailyWorkoutSummary] = Field(default_factory=list)

    # Weekly totals
    total_sessions: int = 0
    total_duration_minutes: int = 0
    total_volume_kg: Optional[Decimal] = None
    total_distance_meters: Optional[Decimal] = None

    # Goal progress
    workouts_per_week_target: Optional[int] = None
    workouts_completed: int = 0
    minutes_per_week_target: Optional[int] = None
    minutes_completed: int = 0


# =============================================================================
# List Response Schemas
# =============================================================================

class ExerciseListResponse(BaseModel):
    """Paginated list of exercises."""

    data: list[ExerciseResponse] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class ExerciseSearchResponse(BaseModel):
    """Search results for exercises."""

    results: list[ExerciseResponse] = Field(default_factory=list)
    total: int = 0
    query: str


class WorkoutSessionListResponse(BaseModel):
    """Paginated list of workout sessions."""

    data: list[WorkoutSessionListItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
