"""
Pydantic schemas for Garmin API requests and responses.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, computed_field


# ============ Connection Schemas ============

class GarminConnectResponse(BaseModel):
    """Response when initiating OAuth connection."""
    authorization_url: str
    state: str


class GarminConnectionStatus(BaseModel):
    """Current Garmin connection status."""
    is_connected: bool
    garmin_user_id: Optional[str] = None
    connected_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    scopes: List[str] = []


class GarminDisconnectResponse(BaseModel):
    """Response when disconnecting Garmin."""
    success: bool
    message: str


class GarminSyncRequest(BaseModel):
    """Request to sync Garmin data."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class GarminSyncResponse(BaseModel):
    """Response after syncing Garmin data."""
    success: bool
    activities_synced: int
    sleep_synced: int
    heart_rate_synced: int
    daily_stats_synced: int
    sync_completed_at: datetime


# ============ Activity Schemas ============

class GarminActivityBase(BaseModel):
    """Base activity schema."""
    garmin_activity_id: str
    activity_type: str
    activity_name: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    distance_meters: Optional[Decimal] = None
    calories: Optional[int] = None
    average_hr: Optional[int] = None
    max_hr: Optional[int] = None
    average_speed: Optional[Decimal] = None
    max_speed: Optional[Decimal] = None
    elevation_gain_meters: Optional[Decimal] = None


class GarminActivityResponse(GarminActivityBase):
    """Activity response with computed fields."""
    id: str

    @computed_field
    @property
    def duration_minutes(self) -> Optional[float]:
        """Duration in minutes."""
        if self.duration_seconds:
            return self.duration_seconds / 60
        return None

    @computed_field
    @property
    def distance_km(self) -> Optional[float]:
        """Distance in kilometers."""
        if self.distance_meters:
            return float(self.distance_meters) / 1000
        return None


class GarminActivityListResponse(BaseModel):
    """Paginated list of activities."""
    data: List[GarminActivityResponse]
    total: int
    page: int
    page_size: int


# ============ Sleep Schemas ============

class GarminSleepBase(BaseModel):
    """Base sleep schema."""
    garmin_sleep_id: str
    start_time: datetime
    end_time: datetime
    total_sleep_seconds: Optional[int] = None
    deep_sleep_seconds: Optional[int] = None
    light_sleep_seconds: Optional[int] = None
    rem_sleep_seconds: Optional[int] = None
    awake_seconds: Optional[int] = None
    sleep_score: Optional[int] = None
    sleep_quality: Optional[str] = None


class GarminSleepResponse(GarminSleepBase):
    """Sleep response with computed fields."""
    id: str

    @computed_field
    @property
    def total_sleep_hours(self) -> Optional[float]:
        """Total sleep in hours."""
        if self.total_sleep_seconds:
            return self.total_sleep_seconds / 3600
        return None


class GarminSleepListResponse(BaseModel):
    """Paginated list of sleep records."""
    data: List[GarminSleepResponse]
    total: int
    page: int
    page_size: int


# ============ Heart Rate Schemas ============

class GarminHeartRateBase(BaseModel):
    """Base heart rate schema."""
    date: date
    resting_hr: Optional[int] = None
    max_hr: Optional[int] = None
    min_hr: Optional[int] = None
    average_hr: Optional[int] = None
    hrv_value: Optional[Decimal] = None


class GarminHeartRateResponse(GarminHeartRateBase):
    """Heart rate response."""
    id: str


class GarminHeartRateListResponse(BaseModel):
    """Paginated list of heart rate records."""
    data: List[GarminHeartRateResponse]
    total: int
    page: int
    page_size: int


# ============ Daily Stats Schemas ============

class GarminDailyStatsBase(BaseModel):
    """Base daily stats schema."""
    date: date
    total_steps: Optional[int] = None
    distance_meters: Optional[Decimal] = None
    calories_burned: Optional[int] = None
    active_calories: Optional[int] = None
    active_minutes: Optional[int] = None
    sedentary_minutes: Optional[int] = None
    floors_climbed: Optional[int] = None
    intensity_minutes: Optional[int] = None
    stress_level: Optional[int] = None
    body_battery_high: Optional[int] = None
    body_battery_low: Optional[int] = None


class GarminDailyStatsResponse(GarminDailyStatsBase):
    """Daily stats response."""
    id: str

    @computed_field
    @property
    def distance_km(self) -> Optional[float]:
        """Distance in kilometers."""
        if self.distance_meters:
            return float(self.distance_meters) / 1000
        return None


class GarminDailyStatsListResponse(BaseModel):
    """Paginated list of daily stats."""
    data: List[GarminDailyStatsResponse]
    total: int
    page: int
    page_size: int


# ============ Dashboard Summary ============

class GarminDashboardSummary(BaseModel):
    """Dashboard summary with latest and aggregated metrics."""
    is_connected: bool
    last_sync_at: Optional[datetime] = None

    # Latest metrics
    latest_resting_hr: Optional[int] = None
    latest_hrv: Optional[Decimal] = None
    latest_sleep_score: Optional[int] = None
    latest_sleep_hours: Optional[float] = None
    latest_steps: Optional[int] = None
    latest_calories: Optional[int] = None
    latest_active_minutes: Optional[int] = None
    latest_body_battery: Optional[int] = None

    # 7-day aggregates
    avg_resting_hr_7d: Optional[float] = None
    avg_sleep_hours_7d: Optional[float] = None
    avg_steps_7d: Optional[float] = None
    total_activities_7d: int = 0
    total_active_minutes_7d: int = 0
