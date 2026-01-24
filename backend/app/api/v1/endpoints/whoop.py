"""
Whoop API endpoints.

Provides endpoints for:
- OAuth connection flow
- Data synchronization
- Dashboard and data retrieval
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.core.exceptions import WhoopAuthError, WhoopNotConnectedError
from app.core.logging_config import get_logger
from app.dependencies import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.whoop import (
    WhoopConnectResponse,
    WhoopConnectionStatus,
    WhoopDashboardSummary,
    WhoopDisconnectResponse,
    WhoopRecoveryListResponse,
    WhoopSleepListResponse,
    WhoopSyncResponse,
    WhoopWorkoutListResponse,
)
from app.services.whoop_client import WhoopAPIClient
from app.services.whoop_service import get_whoop_service
from app.services.whoop_sync_service import get_whoop_sync_service

logger = get_logger(__name__)

router = APIRouter()

# In-memory state storage (use Redis in production)
_oauth_states: dict[str, str] = {}

# Frontend URL for redirects after OAuth
FRONTEND_URL = "http://localhost:5173"


@router.get(
    "/connect",
    response_model=WhoopConnectResponse,
    summary="Get Whoop authorization URL",
    description="Generate OAuth authorization URL for connecting Whoop account",
)
async def get_connect_url(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
) -> WhoopConnectResponse:
    """Get the OAuth authorization URL for connecting Whoop."""
    logger.info(f"Generating Whoop connect URL for user {current_user.id}")

    whoop_service = get_whoop_service()
    auth_url, state = whoop_service.generate_authorization_url()

    # Store state with user ID for verification in callback
    _oauth_states[state] = current_user.id
    logger.info(f"Stored OAuth state: {state[:8]}... for user {current_user.id}. Total stored states: {len(_oauth_states)}")

    return WhoopConnectResponse(
        authorization_url=auth_url,
        state=state,
    )


@router.get(
    "/callback",
    summary="OAuth callback handler",
    description="Handles OAuth callback from Whoop after user authorization",
    include_in_schema=False,
)
async def oauth_callback(
    code: str = Query(..., description="Authorization code from Whoop"),
    state: str = Query(..., description="State parameter for CSRF verification"),
) -> RedirectResponse:
    """
    Handle OAuth callback from Whoop.

    This endpoint receives the authorization code after user approves access.
    It exchanges the code for tokens and stores the connection.
    """
    logger.info(f"Received Whoop OAuth callback with state: {state[:8]}...")
    logger.debug(f"Current stored states: {list(_oauth_states.keys())}")

    # Verify state and get user ID
    user_id = _oauth_states.pop(state, None)
    if not user_id:
        logger.warning(f"Invalid or expired OAuth state. Received: {state[:8]}..., stored states count: {len(_oauth_states)}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/dashboard?whoop_error=invalid_state",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        whoop_service = get_whoop_service()

        # Exchange code for tokens
        tokens = await whoop_service.exchange_code_for_tokens(code)
        logger.debug(f"Token response keys: {list(tokens.keys())}")

        # Get Whoop user profile to get whoop_user_id
        client = WhoopAPIClient(tokens["access_token"])
        profile = await client.get_user_profile()
        whoop_user_id = str(profile.get("user_id"))

        # Get refresh token - Whoop may use different key names
        refresh_token = tokens.get("refresh_token") or tokens.get("refreshToken") or ""
        if not refresh_token:
            logger.warning(f"No refresh token in Whoop response. Keys: {list(tokens.keys())}")

        # Save connection
        await whoop_service.save_connection(
            user_id=user_id,
            whoop_user_id=whoop_user_id,
            access_token=tokens["access_token"],
            refresh_token=refresh_token,
            expires_in=tokens.get("expires_in", 3600),
            scopes=tokens.get("scope", "").split(" "),
        )

        logger.info(f"Whoop connected successfully for user {user_id}")

        # Redirect to dashboard with success message
        return RedirectResponse(
            url=f"{FRONTEND_URL}/dashboard?whoop_connected=true",
            status_code=status.HTTP_302_FOUND,
        )

    except WhoopAuthError as e:
        logger.error(f"Whoop OAuth failed: {e.message}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/dashboard?whoop_error={e.error_code}",
            status_code=status.HTTP_302_FOUND,
        )
    except Exception as e:
        logger.exception(f"Unexpected error in Whoop callback: {e}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/dashboard?whoop_error=unexpected_error",
            status_code=status.HTTP_302_FOUND,
        )


@router.delete(
    "/disconnect",
    response_model=WhoopDisconnectResponse,
    summary="Disconnect Whoop account",
    description="Disconnect the user's Whoop account. Historical data is retained.",
)
async def disconnect_whoop(
    current_user: UserResponse = Depends(get_current_user),
) -> WhoopDisconnectResponse:
    """Disconnect the user's Whoop account."""
    logger.info(f"Disconnecting Whoop for user {current_user.id}")

    whoop_service = get_whoop_service()
    success = await whoop_service.disconnect(current_user.id)

    if success:
        return WhoopDisconnectResponse(
            success=True,
            message="Whoop account disconnected successfully",
        )
    else:
        return WhoopDisconnectResponse(
            success=False,
            message="No active Whoop connection found",
        )


@router.get(
    "/status",
    response_model=WhoopConnectionStatus,
    summary="Get Whoop connection status",
    description="Check if the user has connected their Whoop account",
)
async def get_connection_status(
    current_user: UserResponse = Depends(get_current_user),
) -> WhoopConnectionStatus:
    """Get the current Whoop connection status."""
    logger.debug(f"Getting Whoop status for user {current_user.id}")

    whoop_service = get_whoop_service()
    connection = await whoop_service.get_connection(current_user.id)

    if not connection:
        return WhoopConnectionStatus(
            is_connected=False,
            whoop_user_id=None,
            connected_at=None,
            last_sync_at=None,
            scopes=[],
        )

    return WhoopConnectionStatus(
        is_connected=True,
        whoop_user_id=connection.get("whoop_user_id"),
        connected_at=connection.get("created_at"),
        last_sync_at=connection.get("last_sync_at"),
        scopes=connection.get("scopes", []),
    )


@router.post(
    "/sync",
    response_model=WhoopSyncResponse,
    summary="Sync Whoop data",
    description="Trigger synchronization of Whoop data for the current user",
)
async def sync_whoop_data(
    current_user: UserResponse = Depends(get_current_user),
    start_date: Optional[datetime] = Query(None, description="Start date for sync"),
    end_date: Optional[datetime] = Query(None, description="End date for sync"),
) -> WhoopSyncResponse:
    """Sync Whoop data for the authenticated user."""
    logger.info(f"Syncing Whoop data for user {current_user.id}")

    sync_service = get_whoop_sync_service()

    try:
        result = await sync_service.sync_all(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
        )

        return WhoopSyncResponse(
            success=True,
            cycles_synced=result["cycles"],
            recovery_synced=result["recovery"],
            sleep_synced=result["sleep"],
            workouts_synced=result["workouts"],
            sync_completed_at=datetime.utcnow(),
        )

    except WhoopNotConnectedError:
        raise
    except Exception as e:
        logger.error(f"Sync failed for user {current_user.id}: {e}")
        return WhoopSyncResponse(
            success=False,
            cycles_synced=0,
            recovery_synced=0,
            sleep_synced=0,
            workouts_synced=0,
            sync_completed_at=datetime.utcnow(),
        )


@router.get(
    "/dashboard",
    response_model=WhoopDashboardSummary,
    summary="Get dashboard summary",
    description="Get summary metrics for dashboard display",
)
async def get_dashboard_summary(
    current_user: UserResponse = Depends(get_current_user),
) -> WhoopDashboardSummary:
    """Get Whoop dashboard summary with latest metrics."""
    logger.debug(f"Getting Whoop dashboard for user {current_user.id}")

    sync_service = get_whoop_sync_service()
    summary = await sync_service.get_dashboard_summary(current_user.id)

    return WhoopDashboardSummary(**summary)


@router.get(
    "/sleep",
    response_model=WhoopSleepListResponse,
    summary="Get sleep records",
    description="Get paginated sleep records for the current user",
)
async def get_sleep_records(
    current_user: UserResponse = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Records per page"),
    include_naps: bool = Query(False, description="Include nap records"),
) -> WhoopSleepListResponse:
    """Get paginated sleep records."""
    logger.debug(f"Getting sleep records for user {current_user.id}")

    sync_service = get_whoop_sync_service()
    data, total = await sync_service.get_sleep_records(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        include_naps=include_naps,
    )

    return WhoopSleepListResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/workouts",
    response_model=WhoopWorkoutListResponse,
    summary="Get workout records",
    description="Get paginated workout records for the current user",
)
async def get_workout_records(
    current_user: UserResponse = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Records per page"),
) -> WhoopWorkoutListResponse:
    """Get paginated workout records."""
    logger.debug(f"Getting workout records for user {current_user.id}")

    sync_service = get_whoop_sync_service()
    data, total = await sync_service.get_workout_records(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )

    return WhoopWorkoutListResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/recovery",
    response_model=WhoopRecoveryListResponse,
    summary="Get recovery records",
    description="Get paginated recovery records for the current user",
)
async def get_recovery_records(
    current_user: UserResponse = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Records per page"),
) -> WhoopRecoveryListResponse:
    """Get paginated recovery records."""
    logger.debug(f"Getting recovery records for user {current_user.id}")

    sync_service = get_whoop_sync_service()
    data, total = await sync_service.get_recovery_records(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )

    return WhoopRecoveryListResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
    )
