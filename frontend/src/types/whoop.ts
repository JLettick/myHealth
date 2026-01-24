/**
 * TypeScript types for Whoop API integration.
 */

// =============================================================================
// OAuth Types
// =============================================================================

export interface WhoopConnectResponse {
  authorization_url: string;
  state: string;
}

export interface WhoopConnectionStatus {
  is_connected: boolean;
  whoop_user_id: string | null;
  connected_at: string | null;
  last_sync_at: string | null;
  scopes: string[];
}

export interface WhoopDisconnectResponse {
  success: boolean;
  message: string;
}

// =============================================================================
// Sync Types
// =============================================================================

export interface WhoopSyncRequest {
  start_date?: string;
  end_date?: string;
}

export interface WhoopSyncResponse {
  success: boolean;
  cycles_synced: number;
  recovery_synced: number;
  sleep_synced: number;
  workouts_synced: number;
  sync_completed_at: string;
}

// =============================================================================
// Data Types
// =============================================================================

export interface WhoopCycle {
  id: string;
  whoop_cycle_id: string; // UUID in v2 API
  start_time: string;
  end_time: string | null;
  strain_score: number | null;
  kilojoules: number | null;
  average_heart_rate: number | null;
  max_heart_rate: number | null;
  created_at: string;
}

export interface WhoopRecovery {
  id: string;
  whoop_cycle_id: string; // UUID in v2 API
  recovery_score: number | null;
  resting_heart_rate: number | null;
  hrv_rmssd_milli: number | null;
  spo2_percentage: number | null;
  skin_temp_celsius: number | null;
  created_at: string;
}

export interface WhoopSleep {
  id: string;
  whoop_sleep_id: string; // UUID in v2 API
  whoop_cycle_id: string | null; // UUID in v2 API
  start_time: string;
  end_time: string;
  is_nap: boolean;
  sleep_score: number | null;
  total_in_bed_milli: number | null;
  total_awake_milli: number | null;
  total_light_sleep_milli: number | null;
  total_slow_wave_sleep_milli: number | null;
  total_rem_sleep_milli: number | null;
  sleep_efficiency: number | null;
  respiratory_rate: number | null;
  created_at: string;
}

export interface WhoopWorkout {
  id: string;
  whoop_workout_id: string; // UUID in v2 API
  whoop_cycle_id: string | null; // UUID in v2 API
  start_time: string;
  end_time: string;
  sport_id: number;
  sport_name: string | null;
  strain_score: number | null;
  kilojoules: number | null;
  average_heart_rate: number | null;
  max_heart_rate: number | null;
  distance_meter: number | null;
  altitude_gain_meter: number | null;
  created_at: string;
}

// =============================================================================
// Dashboard Types
// =============================================================================

export interface WhoopDashboardSummary {
  is_connected: boolean;
  last_sync_at: string | null;
  latest_recovery_score: number | null;
  latest_strain_score: number | null;
  latest_hrv: number | null;
  latest_resting_hr: number | null;
  latest_sleep_score: number | null;
  latest_sleep_hours: number | null;
  avg_recovery_7d: number | null;
  avg_strain_7d: number | null;
  avg_sleep_hours_7d: number | null;
  total_workouts_7d: number;
}

// =============================================================================
// List Response Types
// =============================================================================

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
}

export type WhoopSleepListResponse = PaginatedResponse<WhoopSleep>;
export type WhoopWorkoutListResponse = PaginatedResponse<WhoopWorkout>;
export type WhoopRecoveryListResponse = PaginatedResponse<WhoopRecovery>;
export type WhoopCycleListResponse = PaginatedResponse<WhoopCycle>;

// =============================================================================
// Helper Types
// =============================================================================

export type WhoopDataType = 'sleep' | 'workouts' | 'recovery' | 'cycles';

export interface WhoopContextState {
  connectionStatus: WhoopConnectionStatus | null;
  dashboardSummary: WhoopDashboardSummary | null;
  isLoading: boolean;
  isSyncing: boolean;
  error: string | null;
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Convert milliseconds to hours with 1 decimal place.
 */
export function millisToHours(milli: number | null): number | null {
  if (milli === null) return null;
  return Math.round((milli / 3600000) * 10) / 10;
}

/**
 * Format a recovery score with color indication.
 */
export function getRecoveryColor(score: number | null): string {
  if (score === null) return 'gray';
  if (score >= 67) return 'green';
  if (score >= 34) return 'yellow';
  return 'red';
}

/**
 * Format strain score with color indication.
 */
export function getStrainColor(score: number | null): string {
  if (score === null) return 'gray';
  if (score >= 18) return 'red';
  if (score >= 14) return 'orange';
  if (score >= 10) return 'yellow';
  return 'blue';
}

/**
 * Get human-readable sport name from sport_id.
 */
export function getSportName(sportId: number, sportName: string | null): string {
  if (sportName) return sportName;

  // Common Whoop sport IDs
  const sportMap: Record<number, string> = {
    0: 'Activity',
    1: 'Running',
    33: 'Cycling',
    44: 'Swimming',
    48: 'Yoga',
    52: 'Weightlifting',
    71: 'CrossFit',
    82: 'HIIT',
    // Add more as needed
  };

  return sportMap[sportId] || `Activity (${sportId})`;
}

/**
 * Format date for display.
 */
export function formatWhoopDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

/**
 * Format time for display.
 */
export function formatWhoopTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  });
}
