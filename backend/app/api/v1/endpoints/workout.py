"""
Workout Tracking API endpoints.

Provides endpoints for:
- Exercises CRUD
- Workout sessions CRUD
- Workout sets CRUD
- Daily/weekly summaries
- Workout goals
"""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.exceptions import HTTPException

from app.core.logging_config import get_logger
from app.dependencies import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.workout import (
    ExerciseCreate,
    ExerciseUpdate,
    ExerciseResponse,
    ExerciseListResponse,
    ExerciseSearchResponse,
    WorkoutSessionCreate,
    WorkoutSessionUpdate,
    WorkoutSessionResponse,
    WorkoutSessionListItem,
    WorkoutSessionListResponse,
    WorkoutSetCreate,
    WorkoutSetUpdate,
    WorkoutSetResponse,
    DailyWorkoutSummary,
    WeeklyWorkoutSummary,
    WorkoutGoalsCreate,
    WorkoutGoalsResponse,
    ExerciseHistoryDataPoint,
    ExerciseHistoryResponse,
    CardioHistoryDataPoint,
    CardioHistoryResponse,
    WeeklyTrendDataPoint,
    WorkoutTrendsResponse,
)
from app.services.workout_service import get_workout_service

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# EXERCISES ENDPOINTS
# =============================================================================


@router.post(
    "/exercises",
    response_model=ExerciseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom exercise",
    description="Create a new custom exercise",
)
async def create_exercise(
    exercise: ExerciseCreate,
    current_user: UserResponse = Depends(get_current_user),
) -> ExerciseResponse:
    """Create a custom exercise for the user."""
    logger.info(f"Creating exercise for user {current_user.id}")

    service = get_workout_service()
    result = await service.create_exercise(current_user.id, exercise.model_dump())

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create exercise"
        )

    return ExerciseResponse(**result)


@router.get(
    "/exercises/search",
    response_model=ExerciseSearchResponse,
    summary="Search exercises",
    description="Search for exercises by name and/or category",
)
async def search_exercises(
    q: str = Query("", description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
) -> ExerciseSearchResponse:
    """Search exercises by name/category (global + user's custom)."""
    logger.debug(f"Searching exercises for user {current_user.id}: {q}")

    service = get_workout_service()
    results, total = await service.search_exercises(
        current_user.id, q, category, page, page_size
    )

    return ExerciseSearchResponse(
        results=[ExerciseResponse(**r) for r in results],
        total=total,
        query=q,
    )


@router.get(
    "/exercises/my",
    response_model=ExerciseListResponse,
    summary="Get my custom exercises",
    description="Get user's custom exercises",
)
async def get_my_exercises(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
) -> ExerciseListResponse:
    """Get user's custom exercises."""
    service = get_workout_service()
    data, total = await service.get_user_exercises(current_user.id, page, page_size)

    return ExerciseListResponse(
        data=[ExerciseResponse(**d) for d in data],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/exercises/{exercise_id}",
    response_model=ExerciseResponse,
    summary="Get exercise by ID",
)
async def get_exercise(
    exercise_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> ExerciseResponse:
    """Get a specific exercise."""
    service = get_workout_service()
    result = await service.get_exercise(exercise_id, current_user.id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found"
        )

    return ExerciseResponse(**result)


@router.put(
    "/exercises/{exercise_id}",
    response_model=ExerciseResponse,
    summary="Update exercise",
)
async def update_exercise(
    exercise_id: str,
    exercise: ExerciseUpdate,
    current_user: UserResponse = Depends(get_current_user),
) -> ExerciseResponse:
    """Update a custom exercise (user can only update their own)."""
    service = get_workout_service()
    result = await service.update_exercise(
        exercise_id, current_user.id, exercise.model_dump(exclude_unset=True)
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found or not owned by user",
        )

    return ExerciseResponse(**result)


@router.delete(
    "/exercises/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete exercise",
)
async def delete_exercise(
    exercise_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> None:
    """Delete a custom exercise."""
    service = get_workout_service()
    success = await service.delete_exercise(exercise_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found or not owned by user",
        )


# =============================================================================
# WORKOUT SESSIONS ENDPOINTS
# =============================================================================


@router.post(
    "/sessions",
    response_model=WorkoutSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create workout session",
    description="Create a new workout session",
)
async def create_session(
    session: WorkoutSessionCreate,
    current_user: UserResponse = Depends(get_current_user),
) -> WorkoutSessionResponse:
    """Create a workout session."""
    logger.info(f"Creating workout session for user {current_user.id}")

    service = get_workout_service()
    result = await service.create_session(current_user.id, session.model_dump())

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create session"
        )

    return WorkoutSessionResponse(**result)


@router.get(
    "/sessions",
    response_model=WorkoutSessionListResponse,
    summary="Get sessions by date",
    description="Get workout sessions for a date or date range",
)
async def get_sessions(
    session_date: Optional[date] = Query(None, description="Filter by date"),
    start_date: Optional[date] = Query(None, description="Start of date range"),
    end_date: Optional[date] = Query(None, description="End of date range"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
) -> WorkoutSessionListResponse:
    """Get workout sessions. Defaults to today if no date specified."""
    service = get_workout_service()

    if session_date:
        sessions = await service.get_sessions_by_date(current_user.id, session_date)
    elif start_date and end_date:
        sessions = await service.get_sessions_by_date_range(
            current_user.id, start_date, end_date
        )
    else:
        # Default to today
        sessions = await service.get_sessions_by_date(current_user.id, date.today())

    # Apply pagination
    total = len(sessions)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = sessions[start:end]

    return WorkoutSessionListResponse(
        data=[WorkoutSessionListItem(**s) for s in paginated],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=WorkoutSessionResponse,
    summary="Get session by ID",
)
async def get_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> WorkoutSessionResponse:
    """Get a specific workout session with all sets."""
    service = get_workout_service()
    result = await service.get_session(session_id, current_user.id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    return WorkoutSessionResponse(**result)


@router.put(
    "/sessions/{session_id}",
    response_model=WorkoutSessionResponse,
    summary="Update session",
)
async def update_session(
    session_id: str,
    session: WorkoutSessionUpdate,
    current_user: UserResponse = Depends(get_current_user),
) -> WorkoutSessionResponse:
    """Update a workout session."""
    service = get_workout_service()
    result = await service.update_session(
        session_id, current_user.id, session.model_dump(exclude_unset=True)
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    return WorkoutSessionResponse(**result)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete session",
)
async def delete_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> None:
    """Delete a workout session and all its sets."""
    service = get_workout_service()
    success = await service.delete_session(session_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )


# =============================================================================
# WORKOUT SETS ENDPOINTS
# =============================================================================


@router.post(
    "/sessions/{session_id}/sets",
    response_model=WorkoutSetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add set to session",
    description="Add a workout set to a session",
)
async def create_set(
    session_id: str,
    workout_set: WorkoutSetCreate,
    current_user: UserResponse = Depends(get_current_user),
) -> WorkoutSetResponse:
    """Add a set to a workout session."""
    logger.info(f"Adding set to session {session_id} for user {current_user.id}")

    service = get_workout_service()
    result = await service.create_set(
        current_user.id, session_id, workout_set.model_dump()
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create set. Session may not exist.",
        )

    return WorkoutSetResponse(**result)


@router.get(
    "/sets/{set_id}",
    response_model=WorkoutSetResponse,
    summary="Get set by ID",
)
async def get_set(
    set_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> WorkoutSetResponse:
    """Get a specific workout set."""
    service = get_workout_service()
    result = await service.get_set(set_id, current_user.id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Set not found"
        )

    return WorkoutSetResponse(**result)


@router.put(
    "/sets/{set_id}",
    response_model=WorkoutSetResponse,
    summary="Update set",
)
async def update_set(
    set_id: str,
    workout_set: WorkoutSetUpdate,
    current_user: UserResponse = Depends(get_current_user),
) -> WorkoutSetResponse:
    """Update a workout set."""
    service = get_workout_service()
    result = await service.update_set(
        set_id, current_user.id, workout_set.model_dump(exclude_unset=True)
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Set not found"
        )

    return WorkoutSetResponse(**result)


@router.delete(
    "/sets/{set_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete set",
)
async def delete_set(
    set_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> None:
    """Delete a workout set."""
    service = get_workout_service()
    success = await service.delete_set(set_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Set not found"
        )


# =============================================================================
# SUMMARY ENDPOINTS
# =============================================================================


@router.get(
    "/summary/daily",
    response_model=DailyWorkoutSummary,
    summary="Get daily summary",
    description="Get workout summary for a specific date",
)
async def get_daily_summary(
    summary_date: date = Query(default=None, description="Date (defaults to today)"),
    current_user: UserResponse = Depends(get_current_user),
) -> DailyWorkoutSummary:
    """Get daily workout summary."""
    if summary_date is None:
        summary_date = date.today()

    service = get_workout_service()
    result = await service.get_daily_summary(current_user.id, summary_date)

    return DailyWorkoutSummary(**result)


@router.get(
    "/summary/weekly",
    response_model=WeeklyWorkoutSummary,
    summary="Get weekly summary",
    description="Get workout summary for a week",
)
async def get_weekly_summary(
    start_date: date = Query(
        default=None, description="Week start date (defaults to this Monday)"
    ),
    current_user: UserResponse = Depends(get_current_user),
) -> WeeklyWorkoutSummary:
    """Get weekly workout summary."""
    if start_date is None:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())  # Monday

    service = get_workout_service()
    result = await service.get_weekly_summary(current_user.id, start_date)

    return WeeklyWorkoutSummary(**result)


# =============================================================================
# GOALS ENDPOINTS
# =============================================================================


@router.get(
    "/goals",
    response_model=Optional[WorkoutGoalsResponse],
    summary="Get workout goals",
)
async def get_goals(
    current_user: UserResponse = Depends(get_current_user),
) -> Optional[WorkoutGoalsResponse]:
    """Get user's workout goals. Returns null if not set."""
    service = get_workout_service()
    result = await service.get_goals(current_user.id)

    if not result:
        return None

    return WorkoutGoalsResponse(**result)


@router.put(
    "/goals",
    response_model=WorkoutGoalsResponse,
    summary="Set workout goals",
)
async def set_goals(
    goals: WorkoutGoalsCreate,
    current_user: UserResponse = Depends(get_current_user),
) -> WorkoutGoalsResponse:
    """Create or update workout goals."""
    service = get_workout_service()
    result = await service.upsert_goals(current_user.id, goals.model_dump())

    return WorkoutGoalsResponse(**result)


# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================


@router.get(
    "/analytics/exercises",
    response_model=ExerciseSearchResponse,
    summary="Get logged exercises",
    description="Get exercises the user has actually logged workouts for",
)
async def get_logged_exercises(
    q: str = Query("", description="Search query"),
    set_type: Optional[str] = Query(None, description="Filter by set type (strength/cardio)"),
    current_user: UserResponse = Depends(get_current_user),
) -> ExerciseSearchResponse:
    """Get exercises the user has actually performed."""
    service = get_workout_service()
    results = await service.get_logged_exercises(current_user.id, set_type, q)

    return ExerciseSearchResponse(
        results=[ExerciseResponse(**r) for r in results],
        total=len(results),
        query=q,
    )


@router.get(
    "/analytics/exercise/{exercise_id}",
    response_model=ExerciseHistoryResponse,
    summary="Get exercise history",
    description="Get exercise performance history over a date range for charts",
)
async def get_exercise_history(
    exercise_id: str,
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    current_user: UserResponse = Depends(get_current_user),
) -> ExerciseHistoryResponse:
    """Get exercise performance history for progression charts."""
    service = get_workout_service()

    # Verify exercise exists and user has access
    exercise = await service.get_exercise(exercise_id, current_user.id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found"
        )

    data = await service.get_exercise_history(
        current_user.id, exercise_id, start_date, end_date
    )

    return ExerciseHistoryResponse(
        exercise_id=exercise_id,
        exercise_name=exercise["name"],
        data=[ExerciseHistoryDataPoint(**d) for d in data],
    )


@router.get(
    "/analytics/cardio/{exercise_id}",
    response_model=CardioHistoryResponse,
    summary="Get cardio history",
    description="Get cardio exercise performance history over a date range",
)
async def get_cardio_history(
    exercise_id: str,
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    current_user: UserResponse = Depends(get_current_user),
) -> CardioHistoryResponse:
    """Get cardio exercise history for performance charts."""
    service = get_workout_service()

    # Verify exercise exists and user has access
    exercise = await service.get_exercise(exercise_id, current_user.id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found"
        )

    data = await service.get_cardio_history(
        current_user.id, exercise_id, start_date, end_date
    )

    return CardioHistoryResponse(
        exercise_id=exercise_id,
        exercise_name=exercise["name"],
        data=[CardioHistoryDataPoint(**d) for d in data],
    )


@router.get(
    "/analytics/trends",
    response_model=WorkoutTrendsResponse,
    summary="Get workout trends",
    description="Get weekly workout trends over a date range",
)
async def get_workout_trends(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    current_user: UserResponse = Depends(get_current_user),
) -> WorkoutTrendsResponse:
    """Get weekly workout trends for charts."""
    service = get_workout_service()

    data = await service.get_workout_trends(
        current_user.id, start_date, end_date
    )
    goals = await service.get_goals(current_user.id)

    return WorkoutTrendsResponse(
        data=[WeeklyTrendDataPoint(**d) for d in data],
        workouts_per_week_target=goals.get("workouts_per_week_target") if goals else None,
        minutes_per_week_target=goals.get("minutes_per_week_target") if goals else None,
    )
