/**
 * Garmin integration types.
 *
 * Types for Garmin Connect API integration.
 */

// ============ Connection Types ============

export interface GarminConnectResponse {
  authorization_url: string;
  state: string;
}

export interface GarminConnectionStatus {
  is_connected: boolean;
  garmin_user_id: string | null;
  connected_at: string | null;
  last_sync_at: string | null;
  scopes: string[];
}

export interface GarminDisconnectResponse {
  success: boolean;
  message: string;
}

export interface GarminSyncResponse {
  success: boolean;
  activities_synced: number;
  sleep_synced: number;
  heart_rate_synced: number;
  daily_stats_synced: number;
  sync_completed_at: string;
}

// ============ Activity Types ============

export interface GarminActivity {
  id: string;
  garmin_activity_id: string;
  activity_type: string;
  activity_name: string | null;
  start_time: string;
  end_time: string | null;
  duration_seconds: number | null;
  distance_meters: number | null;
  calories: number | null;
  average_hr: number | null;
  max_hr: number | null;
  average_speed: number | null;
  max_speed: number | null;
  elevation_gain_meters: number | null;
}

export interface GarminActivityList {
  data: GarminActivity[];
  total: number;
  page: number;
  page_size: number;
}

// ============ Sleep Types ============

export interface GarminSleep {
  id: string;
  garmin_sleep_id: string;
  start_time: string;
  end_time: string;
  total_sleep_seconds: number | null;
  deep_sleep_seconds: number | null;
  light_sleep_seconds: number | null;
  rem_sleep_seconds: number | null;
  awake_seconds: number | null;
  sleep_score: number | null;
  sleep_quality: string | null;
}

export interface GarminSleepList {
  data: GarminSleep[];
  total: number;
  page: number;
  page_size: number;
}

// ============ Heart Rate Types ============

export interface GarminHeartRate {
  id: string;
  date: string;
  resting_hr: number | null;
  max_hr: number | null;
  min_hr: number | null;
  average_hr: number | null;
  hrv_value: number | null;
}

export interface GarminHeartRateList {
  data: GarminHeartRate[];
  total: number;
  page: number;
  page_size: number;
}

// ============ Daily Stats Types ============

export interface GarminDailyStats {
  id: string;
  date: string;
  total_steps: number | null;
  distance_meters: number | null;
  calories_burned: number | null;
  active_calories: number | null;
  active_minutes: number | null;
  sedentary_minutes: number | null;
  floors_climbed: number | null;
  intensity_minutes: number | null;
  stress_level: number | null;
  body_battery_high: number | null;
  body_battery_low: number | null;
}

export interface GarminDailyStatsList {
  data: GarminDailyStats[];
  total: number;
  page: number;
  page_size: number;
}

// ============ Dashboard Summary ============

export interface GarminDashboardSummary {
  is_connected: boolean;
  last_sync_at: string | null;

  // Latest metrics
  latest_resting_hr: number | null;
  latest_hrv: number | null;
  latest_sleep_score: number | null;
  latest_sleep_hours: number | null;
  latest_steps: number | null;
  latest_calories: number | null;
  latest_active_minutes: number | null;
  latest_body_battery: number | null;

  // 7-day aggregates
  avg_resting_hr_7d: number | null;
  avg_sleep_hours_7d: number | null;
  avg_steps_7d: number | null;
  total_activities_7d: number;
  total_active_minutes_7d: number;
}

// ============ Utility Functions ============

/**
 * Format duration in seconds to human-readable string.
 */
export function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return '--';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}

/**
 * Format distance in meters to kilometers.
 */
export function formatDistance(meters: number | null): string {
  if (meters === null || meters === undefined) return '--';
  const km = meters / 1000;
  return `${km.toFixed(2)} km`;
}

/**
 * Format steps with thousands separator.
 */
export function formatSteps(steps: number | null): string {
  if (steps === null || steps === undefined) return '--';
  return steps.toLocaleString();
}

/**
 * Get color based on sleep score.
 */
export function getSleepScoreColor(score: number | null): string {
  if (score === null) return 'gray';
  if (score >= 80) return 'green';
  if (score >= 60) return 'blue';
  if (score >= 40) return 'yellow';
  return 'red';
}

/**
 * Get color based on body battery level.
 */
export function getBodyBatteryColor(level: number | null): string {
  if (level === null) return 'gray';
  if (level >= 75) return 'green';
  if (level >= 50) return 'blue';
  if (level >= 25) return 'yellow';
  return 'red';
}

/**
 * Get activity type display name.
 */
export function getActivityTypeName(type: string): string {
  const typeMap: Record<string, string> = {
    running: 'Running',
    cycling: 'Cycling',
    swimming: 'Swimming',
    walking: 'Walking',
    hiking: 'Hiking',
    strength_training: 'Strength Training',
    yoga: 'Yoga',
    elliptical: 'Elliptical',
    stair_climbing: 'Stair Climbing',
    indoor_cycling: 'Indoor Cycling',
    treadmill_running: 'Treadmill Running',
    other: 'Other',
  };
  return typeMap[type.toLowerCase()] || type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}
