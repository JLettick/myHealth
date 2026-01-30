"""
Garmin API endpoints.

Handles OAuth flow, data synchronization, and dashboard data retrieval.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.dependencies import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.garmin import (
    GarminConnectResponse,
    GarminConnectionStatus,
    GarminDisconnectResponse,
    GarminSyncRequest,
    GarminSyncResponse,
    GarminDashboardSummary,
    GarminActivityListResponse,
    GarminActivityResponse,
    GarminSleepListResponse,
    GarminSleepResponse,
    GarminHeartRateListResponse,
    GarminHeartRateResponse,
    GarminDailyStatsListResponse,
    GarminDailyStatsResponse,
)
from app.services.garmin_service import GarminService
from app.services.garmin_sync_service import GarminSyncService
from app.services.garmin_client import GarminClient
from app.services.supabase_client import get_supabase_service

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["garmin"])


def get_garmin_service() -> GarminService:
    """Dependency for Garmin service."""
    return GarminService()


def get_sync_service() -> GarminSyncService:
    """Dependency for Garmin sync service."""
    return GarminSyncService()


@router.get("/connect", response_model=GarminConnectResponse)
async def connect_garmin(
    current_user: UserResponse = Depends(get_current_user),
    garmin_service: GarminService = Depends(get_garmin_service),
):
    """
    Get Garmin OAuth authorization URL.

    Returns the URL to redirect the user to for Garmin OAuth authorization.
    """
    url, state = garmin_service.generate_authorization_url(str(current_user.id))
    return GarminConnectResponse(authorization_url=url, state=state)


@router.get("/callback")
async def garmin_callback(
    code: str = Query(..., description="Authorization code from Garmin"),
    state: str = Query(..., description="State token for CSRF protection"),
    garmin_service: GarminService = Depends(get_garmin_service),
):
    """
    Handle Garmin OAuth callback.

    Exchanges the authorization code for tokens and saves the connection.
    Redirects to the frontend dashboard with success or error status.
    """
    # Validate state
    user_id = garmin_service.validate_state(state)
    if not user_id:
        logger.warning("Invalid OAuth state received")
        return RedirectResponse(
            url=f"{settings.frontend_url}/dashboard?garmin_error=invalid_state"
        )

    try:
        # Exchange code for tokens
        tokens = await garmin_service.exchange_code_for_tokens(code)

        # Get user profile from Garmin
        client = GarminClient(tokens["access_token"])
        profile = await client.get_user_profile()

        # Extract user ID from profile
        garmin_user_id = str(
            profile.get("userId") or
            profile.get("id") or
            profile.get("displayName", "unknown")
        )

        # Save connection
        garmin_service.save_connection(
            user_id=user_id,
            garmin_user_id=garmin_user_id,
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token", ""),
            expires_in=tokens.get("expires_in", 3600),
            scopes=tokens.get("scope", "").split(" ") if tokens.get("scope") else [],
        )

        logger.info(f"Successfully connected Garmin for user {user_id}")
        return RedirectResponse(
            url=f"{settings.frontend_url}/dashboard?garmin_connected=true"
        )

    except Exception as e:
        logger.error(f"Garmin OAuth callback error: {e}")
        return RedirectResponse(
            url=f"{settings.frontend_url}/dashboard?garmin_error={str(e)}"
        )


@router.delete("/disconnect", response_model=GarminDisconnectResponse)
async def disconnect_garmin(
    current_user: UserResponse = Depends(get_current_user),
    garmin_service: GarminService = Depends(get_garmin_service),
):
    """
    Disconnect Garmin account.

    Marks the connection as inactive (soft delete). Historical data is retained.
    """
    success = garmin_service.disconnect(str(current_user.id))
    return GarminDisconnectResponse(
        success=success,
        message="Garmin account disconnected" if success else "No connection found",
    )


@router.get("/status", response_model=GarminConnectionStatus)
async def get_garmin_status(
    current_user: UserResponse = Depends(get_current_user),
    garmin_service: GarminService = Depends(get_garmin_service),
):
    """
    Get Garmin connection status.

    Returns information about the current Garmin connection including
    connection state, user ID, and last sync time.
    """
    status = garmin_service.get_connection_status(str(current_user.id))
    return GarminConnectionStatus(**status)


@router.post("/sync", response_model=GarminSyncResponse)
async def sync_garmin(
    request: GarminSyncRequest = None,
    current_user: UserResponse = Depends(get_current_user),
    sync_service: GarminSyncService = Depends(get_sync_service),
):
    """
    Sync Garmin data.

    Fetches and stores the latest data from Garmin Connect API.
    Optionally accepts a date range; defaults to the last 30 days.
    """
    try:
        result = await sync_service.sync_all(
            user_id=str(current_user.id),
            start_date=request.start_date if request else None,
            end_date=request.end_date if request else None,
        )
        return GarminSyncResponse(
            success=True,
            activities_synced=result["activities_synced"],
            sleep_synced=result["sleep_synced"],
            heart_rate_synced=result["heart_rate_synced"],
            daily_stats_synced=result["daily_stats_synced"],
            sync_completed_at=datetime.now(timezone.utc),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Garmin sync error: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync Garmin data")


@router.get("/dashboard", response_model=GarminDashboardSummary)
async def get_garmin_dashboard(
    current_user: UserResponse = Depends(get_current_user),
    sync_service: GarminSyncService = Depends(get_sync_service),
):
    """
    Get Garmin dashboard summary.

    Returns the latest metrics and 7-day aggregates for display on the dashboard.
    """
    summary = sync_service.get_dashboard_summary(str(current_user.id))
    return GarminDashboardSummary(**summary)


@router.get("/activities", response_model=GarminActivityListResponse)
async def get_garmin_activities(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get paginated Garmin activities.
    """
    supabase = get_supabase_service()
    offset = (page - 1) * page_size

    # Get total count
    count_result = (
        supabase.admin_client.table("garmin_activities")
        .select("*", count="exact")
        .eq("user_id", str(current_user.id))
        .execute()
    )
    total = count_result.count or 0

    # Get paginated data
    result = (
        supabase.admin_client.table("garmin_activities")
        .select("*")
        .eq("user_id", str(current_user.id))
        .order("start_time", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    activities = [
        GarminActivityResponse(
            id=str(r["id"]),
            garmin_activity_id=r["garmin_activity_id"],
            activity_type=r["activity_type"],
            activity_name=r.get("activity_name"),
            start_time=r["start_time"],
            end_time=r.get("end_time"),
            duration_seconds=r.get("duration_seconds"),
            distance_meters=r.get("distance_meters"),
            calories=r.get("calories"),
            average_hr=r.get("average_hr"),
            max_hr=r.get("max_hr"),
            average_speed=r.get("average_speed"),
            max_speed=r.get("max_speed"),
            elevation_gain_meters=r.get("elevation_gain_meters"),
        )
        for r in result.data
    ]

    return GarminActivityListResponse(
        data=activities,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/sleep", response_model=GarminSleepListResponse)
async def get_garmin_sleep(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get paginated Garmin sleep records.
    """
    supabase = get_supabase_service()
    offset = (page - 1) * page_size

    # Get total count
    count_result = (
        supabase.admin_client.table("garmin_sleep")
        .select("*", count="exact")
        .eq("user_id", str(current_user.id))
        .execute()
    )
    total = count_result.count or 0

    # Get paginated data
    result = (
        supabase.admin_client.table("garmin_sleep")
        .select("*")
        .eq("user_id", str(current_user.id))
        .order("start_time", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    sleep_records = [
        GarminSleepResponse(
            id=str(r["id"]),
            garmin_sleep_id=r["garmin_sleep_id"],
            start_time=r["start_time"],
            end_time=r["end_time"],
            total_sleep_seconds=r.get("total_sleep_seconds"),
            deep_sleep_seconds=r.get("deep_sleep_seconds"),
            light_sleep_seconds=r.get("light_sleep_seconds"),
            rem_sleep_seconds=r.get("rem_sleep_seconds"),
            awake_seconds=r.get("awake_seconds"),
            sleep_score=r.get("sleep_score"),
            sleep_quality=r.get("sleep_quality"),
        )
        for r in result.data
    ]

    return GarminSleepListResponse(
        data=sleep_records,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/heart-rate", response_model=GarminHeartRateListResponse)
async def get_garmin_heart_rate(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get paginated Garmin heart rate records.
    """
    supabase = get_supabase_service()
    offset = (page - 1) * page_size

    # Get total count
    count_result = (
        supabase.admin_client.table("garmin_heart_rate")
        .select("*", count="exact")
        .eq("user_id", str(current_user.id))
        .execute()
    )
    total = count_result.count or 0

    # Get paginated data
    result = (
        supabase.admin_client.table("garmin_heart_rate")
        .select("*")
        .eq("user_id", str(current_user.id))
        .order("date", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    hr_records = [
        GarminHeartRateResponse(
            id=str(r["id"]),
            date=r["date"],
            resting_hr=r.get("resting_hr"),
            max_hr=r.get("max_hr"),
            min_hr=r.get("min_hr"),
            average_hr=r.get("average_hr"),
            hrv_value=r.get("hrv_value"),
        )
        for r in result.data
    ]

    return GarminHeartRateListResponse(
        data=hr_records,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/daily", response_model=GarminDailyStatsListResponse)
async def get_garmin_daily_stats(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get paginated Garmin daily stats.
    """
    supabase = get_supabase_service()
    offset = (page - 1) * page_size

    # Get total count
    count_result = (
        supabase.admin_client.table("garmin_daily_stats")
        .select("*", count="exact")
        .eq("user_id", str(current_user.id))
        .execute()
    )
    total = count_result.count or 0

    # Get paginated data
    result = (
        supabase.admin_client.table("garmin_daily_stats")
        .select("*")
        .eq("user_id", str(current_user.id))
        .order("date", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    daily_stats = [
        GarminDailyStatsResponse(
            id=str(r["id"]),
            date=r["date"],
            total_steps=r.get("total_steps"),
            distance_meters=r.get("distance_meters"),
            calories_burned=r.get("calories_burned"),
            active_calories=r.get("active_calories"),
            active_minutes=r.get("active_minutes"),
            sedentary_minutes=r.get("sedentary_minutes"),
            floors_climbed=r.get("floors_climbed"),
            intensity_minutes=r.get("intensity_minutes"),
            stress_level=r.get("stress_level"),
            body_battery_high=r.get("body_battery_high"),
            body_battery_low=r.get("body_battery_low"),
        )
        for r in result.data
    ]

    return GarminDailyStatsListResponse(
        data=daily_stats,
        total=total,
        page=page,
        page_size=page_size,
    )
