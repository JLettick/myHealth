"""
Pydantic schemas for Whoop API integration.

Defines request/response models for:
- OAuth connection flow
- Data sync operations
- Sleep, recovery, workout, and cycle data
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# OAuth Schemas
# =============================================================================


class WhoopConnectResponse(BaseModel):
    """Response with OAuth authorization URL."""

    authorization_url: str = Field(..., description="URL to redirect user for Whoop authorization")
    state: str = Field(..., description="CSRF state parameter")


class WhoopCallbackRequest(BaseModel):
    """OAuth callback parameters."""

    code: str = Field(..., description="Authorization code from Whoop")
    state: str = Field(..., description="State parameter for CSRF verification")


class WhoopConnectionStatus(BaseModel):
    """Current Whoop connection status."""

    is_connected: bool = Field(..., description="Whether Whoop is connected")
    whoop_user_id: Optional[str] = Field(None, description="Whoop user ID if connected")
    connected_at: Optional[datetime] = Field(None, description="When connection was established")
    last_sync_at: Optional[datetime] = Field(None, description="Last successful sync time")
    scopes: list[str] = Field(default_factory=list, description="Granted OAuth scopes")


class WhoopDisconnectResponse(BaseModel):
    """Response after disconnecting Whoop."""

    success: bool = Field(..., description="Whether disconnect was successful")
    message: str = Field(..., description="Status message")


# =============================================================================
# Sync Schemas
# =============================================================================


class WhoopSyncRequest(BaseModel):
    """Request to sync Whoop data."""

    start_date: Optional[datetime] = Field(None, description="Start date for sync range")
    end_date: Optional[datetime] = Field(None, description="End date for sync range")


class WhoopSyncResponse(BaseModel):
    """Response after syncing Whoop data."""

    success: bool = Field(..., description="Whether sync was successful")
    cycles_synced: int = Field(0, description="Number of cycles synced")
    recovery_synced: int = Field(0, description="Number of recovery records synced")
    sleep_synced: int = Field(0, description="Number of sleep records synced")
    workouts_synced: int = Field(0, description="Number of workouts synced")
    sync_completed_at: datetime = Field(..., description="When sync completed")


# =============================================================================
# Cycle Schemas
# =============================================================================


class WhoopCycleBase(BaseModel):
    """Base schema for cycle data."""

    whoop_cycle_id: str = Field(..., description="Whoop's cycle ID (UUID in v2)")
    start_time: datetime = Field(..., description="Cycle start time")
    end_time: Optional[datetime] = Field(None, description="Cycle end time")
    strain_score: Optional[Decimal] = Field(None, ge=0, le=21, description="Day strain (0-21)")
    kilojoules: Optional[Decimal] = Field(None, ge=0, description="Calories burned in kJ")
    average_heart_rate: Optional[int] = Field(None, ge=0, description="Average heart rate")
    max_heart_rate: Optional[int] = Field(None, ge=0, description="Max heart rate")


class WhoopCycleResponse(WhoopCycleBase):
    """Cycle data response."""

    id: str = Field(..., description="Database UUID")
    created_at: datetime = Field(..., description="Record creation time")

    class Config:
        from_attributes = True


# =============================================================================
# Recovery Schemas
# =============================================================================


class WhoopRecoveryBase(BaseModel):
    """Base schema for recovery data."""

    whoop_cycle_id: str = Field(..., description="Associated cycle ID (UUID in v2)")
    recovery_score: Optional[Decimal] = Field(None, ge=0, le=100, description="Recovery score (0-100%)")
    resting_heart_rate: Optional[Decimal] = Field(None, ge=0, description="Resting heart rate")
    hrv_rmssd_milli: Optional[Decimal] = Field(None, ge=0, description="HRV in milliseconds")
    spo2_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Blood oxygen %")
    skin_temp_celsius: Optional[Decimal] = Field(None, description="Skin temperature in Celsius")


class WhoopRecoveryResponse(WhoopRecoveryBase):
    """Recovery data response."""

    id: str = Field(..., description="Database UUID")
    created_at: datetime = Field(..., description="Record creation time")

    class Config:
        from_attributes = True


# =============================================================================
# Sleep Schemas
# =============================================================================


class WhoopSleepBase(BaseModel):
    """Base schema for sleep data."""

    whoop_sleep_id: str = Field(..., description="Whoop's sleep ID (UUID in v2)")
    whoop_cycle_id: Optional[str] = Field(None, description="Associated cycle ID (UUID in v2)")
    start_time: datetime = Field(..., description="Sleep start time")
    end_time: datetime = Field(..., description="Sleep end time")
    is_nap: bool = Field(False, description="Whether this is a nap")
    sleep_score: Optional[Decimal] = Field(None, ge=0, le=100, description="Sleep performance score")
    total_in_bed_milli: Optional[int] = Field(None, ge=0, description="Total time in bed (ms)")
    total_awake_milli: Optional[int] = Field(None, ge=0, description="Time awake (ms)")
    total_light_sleep_milli: Optional[int] = Field(None, ge=0, description="Light sleep time (ms)")
    total_slow_wave_sleep_milli: Optional[int] = Field(None, ge=0, description="Deep sleep time (ms)")
    total_rem_sleep_milli: Optional[int] = Field(None, ge=0, description="REM sleep time (ms)")
    sleep_efficiency: Optional[Decimal] = Field(None, ge=0, le=1, description="Sleep efficiency (0-1)")
    respiratory_rate: Optional[Decimal] = Field(None, ge=0, description="Respiratory rate")


class WhoopSleepResponse(WhoopSleepBase):
    """Sleep data response."""

    id: str = Field(..., description="Database UUID")
    created_at: datetime = Field(..., description="Record creation time")

    # Computed fields for convenience
    @property
    def total_sleep_hours(self) -> Optional[float]:
        """Calculate total sleep time in hours."""
        if self.total_in_bed_milli and self.total_awake_milli:
            sleep_milli = self.total_in_bed_milli - self.total_awake_milli
            return round(sleep_milli / 3600000, 2)
        return None

    class Config:
        from_attributes = True


# =============================================================================
# Workout Schemas
# =============================================================================


class WhoopWorkoutBase(BaseModel):
    """Base schema for workout data."""

    whoop_workout_id: str = Field(..., description="Whoop's workout ID (UUID in v2)")
    whoop_cycle_id: Optional[str] = Field(None, description="Associated cycle ID (UUID in v2)")
    start_time: datetime = Field(..., description="Workout start time")
    end_time: datetime = Field(..., description="Workout end time")
    sport_id: int = Field(..., description="Sport type ID")
    sport_name: Optional[str] = Field(None, description="Sport name")
    strain_score: Optional[Decimal] = Field(None, ge=0, le=21, description="Workout strain")
    kilojoules: Optional[Decimal] = Field(None, ge=0, description="Calories burned in kJ")
    average_heart_rate: Optional[int] = Field(None, ge=0, description="Average heart rate")
    max_heart_rate: Optional[int] = Field(None, ge=0, description="Max heart rate")
    distance_meter: Optional[Decimal] = Field(None, ge=0, description="Distance in meters")
    altitude_gain_meter: Optional[Decimal] = Field(None, description="Altitude gained in meters")


class WhoopWorkoutResponse(WhoopWorkoutBase):
    """Workout data response."""

    id: str = Field(..., description="Database UUID")
    created_at: datetime = Field(..., description="Record creation time")

    @property
    def duration_minutes(self) -> float:
        """Calculate workout duration in minutes."""
        delta = self.end_time - self.start_time
        return round(delta.total_seconds() / 60, 1)

    class Config:
        from_attributes = True


# =============================================================================
# Dashboard Summary Schemas
# =============================================================================


class WhoopDashboardSummary(BaseModel):
    """Summary data for dashboard display."""

    # Connection status
    is_connected: bool = Field(..., description="Whether Whoop is connected")
    last_sync_at: Optional[datetime] = Field(None, description="Last sync time")

    # Latest metrics (from most recent cycle)
    latest_recovery_score: Optional[Decimal] = Field(None, description="Most recent recovery %")
    latest_strain_score: Optional[Decimal] = Field(None, description="Most recent strain")
    latest_hrv: Optional[Decimal] = Field(None, description="Most recent HRV")
    latest_resting_hr: Optional[Decimal] = Field(None, description="Most recent resting HR")

    # Latest sleep (from most recent sleep record)
    latest_sleep_score: Optional[Decimal] = Field(None, description="Most recent sleep score")
    latest_sleep_hours: Optional[float] = Field(None, description="Most recent sleep duration")

    # Aggregates (last 7 days)
    avg_recovery_7d: Optional[Decimal] = Field(None, description="7-day average recovery")
    avg_strain_7d: Optional[Decimal] = Field(None, description="7-day average strain")
    avg_sleep_hours_7d: Optional[float] = Field(None, description="7-day average sleep hours")
    total_workouts_7d: int = Field(0, description="Workouts in last 7 days")


# =============================================================================
# List Response Schemas
# =============================================================================


class WhoopCycleListResponse(BaseModel):
    """Paginated list of cycles."""

    data: list[WhoopCycleResponse] = Field(default_factory=list)
    total: int = Field(0, description="Total records available")
    page: int = Field(1, description="Current page")
    page_size: int = Field(10, description="Records per page")


class WhoopRecoveryListResponse(BaseModel):
    """Paginated list of recovery records."""

    data: list[WhoopRecoveryResponse] = Field(default_factory=list)
    total: int = Field(0, description="Total records available")
    page: int = Field(1, description="Current page")
    page_size: int = Field(10, description="Records per page")


class WhoopSleepListResponse(BaseModel):
    """Paginated list of sleep records."""

    data: list[WhoopSleepResponse] = Field(default_factory=list)
    total: int = Field(0, description="Total records available")
    page: int = Field(1, description="Current page")
    page_size: int = Field(10, description="Records per page")


class WhoopWorkoutListResponse(BaseModel):
    """Paginated list of workouts."""

    data: list[WhoopWorkoutResponse] = Field(default_factory=list)
    total: int = Field(0, description="Total records available")
    page: int = Field(1, description="Current page")
    page_size: int = Field(10, description="Records per page")
