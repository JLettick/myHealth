/**
 * TypeScript types for Workout Tracking.
 */

// =============================================================================
// Type Definitions
// =============================================================================

export type ExerciseCategory =
  | 'strength'
  | 'cardio'
  | 'flexibility'
  | 'sports'
  | 'other';

export type WorkoutType =
  | 'strength'
  | 'cardio'
  | 'mixed'
  | 'flexibility'
  | 'sports'
  | 'other';

export type SetType = 'strength' | 'cardio';

// =============================================================================
// Exercise Types
// =============================================================================

export interface Exercise {
  id: string;
  user_id: string | null;
  name: string;
  category: ExerciseCategory;
  muscle_groups: string[];
  equipment: string | null;
  description: string | null;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExerciseCreate {
  name: string;
  category: ExerciseCategory;
  muscle_groups?: string[];
  equipment?: string;
  description?: string;
}

export type ExerciseUpdate = Partial<ExerciseCreate>;

// =============================================================================
// Workout Set Types
// =============================================================================

export interface WorkoutSet {
  id: string;
  user_id: string;
  session_id: string;
  exercise_id: string;
  set_type: SetType;
  set_order: number;
  notes: string | null;

  // Strength fields
  reps: number | null;
  weight_kg: number | null;
  rpe: number | null;
  is_warmup: boolean;
  is_failure: boolean;

  // Cardio fields
  duration_seconds: number | null;
  distance_meters: number | null;
  pace_seconds_per_km: number | null;
  calories_burned: number | null;
  avg_heart_rate: number | null;
  max_heart_rate: number | null;
  elevation_gain_meters: number | null;

  created_at: string;
  updated_at: string;
  exercise?: Exercise;
}

export interface WorkoutSetCreate {
  exercise_id: string;
  set_type: SetType;
  set_order?: number;
  notes?: string;

  // Strength fields
  reps?: number;
  weight_kg?: number;
  rpe?: number;
  is_warmup?: boolean;
  is_failure?: boolean;

  // Cardio fields
  duration_seconds?: number;
  distance_meters?: number;
  pace_seconds_per_km?: number;
  calories_burned?: number;
  avg_heart_rate?: number;
  max_heart_rate?: number;
  elevation_gain_meters?: number;
}

export type WorkoutSetUpdate = Partial<WorkoutSetCreate>;

// =============================================================================
// Workout Session Types
// =============================================================================

export interface WorkoutSession {
  id: string;
  user_id: string;
  whoop_workout_id: string | null;
  session_date: string;
  start_time: string | null;
  end_time: string | null;
  workout_type: WorkoutType;
  name: string | null;
  notes: string | null;
  rating: number | null;
  created_at: string;
  updated_at: string;
  sets: WorkoutSet[];
  total_sets: number;
  total_duration_minutes: number | null;
}

export interface WorkoutSessionListItem {
  id: string;
  user_id: string;
  whoop_workout_id: string | null;
  session_date: string;
  start_time: string | null;
  end_time: string | null;
  workout_type: WorkoutType;
  name: string | null;
  notes: string | null;
  rating: number | null;
  created_at: string;
  updated_at: string;
  total_sets: number;
  total_duration_minutes: number | null;
}

export interface WorkoutSessionCreate {
  session_date: string;
  workout_type: WorkoutType;
  name?: string;
  start_time?: string;
  end_time?: string;
  notes?: string;
  rating?: number;
  whoop_workout_id?: string;
}

export type WorkoutSessionUpdate = Partial<WorkoutSessionCreate>;

// =============================================================================
// Workout Goals Types
// =============================================================================

export interface WorkoutGoals {
  id: string;
  user_id: string;
  workouts_per_week_target: number | null;
  minutes_per_week_target: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkoutGoalsCreate {
  workouts_per_week_target?: number;
  minutes_per_week_target?: number;
}

// =============================================================================
// Summary Types
// =============================================================================

export interface ExerciseSummary {
  exercise_id: string;
  exercise_name: string;
  category: ExerciseCategory;
  total_sets: number;
  total_reps: number | null;
  max_weight_kg: number | null;
  total_volume_kg: number | null;
  total_duration_seconds: number | null;
  total_distance_meters: number | null;
}

export interface DailyWorkoutSummary {
  date: string;
  sessions: WorkoutSessionListItem[];
  exercises: ExerciseSummary[];
  total_sessions: number;
  total_sets: number;
  total_duration_minutes: number;
  total_volume_kg: number | null;
  total_distance_meters: number | null;
  workouts_per_week_target: number | null;
  minutes_per_week_target: number | null;
}

export interface WeeklyWorkoutSummary {
  start_date: string;
  end_date: string;
  daily_summaries: DailyWorkoutSummary[];
  total_sessions: number;
  total_duration_minutes: number;
  total_volume_kg: number | null;
  total_distance_meters: number | null;
  workouts_per_week_target: number | null;
  workouts_completed: number;
  minutes_per_week_target: number | null;
  minutes_completed: number;
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

export type ExerciseListResponse = PaginatedResponse<Exercise>;
export type WorkoutSessionListResponse = PaginatedResponse<WorkoutSessionListItem>;

export interface ExerciseSearchResponse {
  results: Exercise[];
  total: number;
  query: string;
}

// =============================================================================
// Utility Constants
// =============================================================================

export const WORKOUT_TYPE_LABELS: Record<WorkoutType, string> = {
  strength: 'Strength',
  cardio: 'Cardio',
  mixed: 'Mixed',
  flexibility: 'Flexibility',
  sports: 'Sports',
  other: 'Other',
};

export const EXERCISE_CATEGORY_LABELS: Record<ExerciseCategory, string> = {
  strength: 'Strength',
  cardio: 'Cardio',
  flexibility: 'Flexibility',
  sports: 'Sports',
  other: 'Other',
};

export const SET_TYPE_LABELS: Record<SetType, string> = {
  strength: 'Strength',
  cardio: 'Cardio',
};

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Get today's date as YYYY-MM-DD string in local timezone.
 */
export function getLocalDateString(date: Date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Format weight value with unit.
 */
export function formatWeight(kg: number | null): string {
  if (kg === null) return '--';
  return `${Math.round(kg * 10) / 10} kg`;
}

/**
 * Format distance in meters to appropriate unit.
 */
export function formatDistance(meters: number | null): string {
  if (meters === null) return '--';
  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(2)} km`;
  }
  return `${Math.round(meters)} m`;
}

/**
 * Format duration in seconds to mm:ss or hh:mm:ss.
 */
export function formatDuration(seconds: number | null): string {
  if (seconds === null) return '--';
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${mins}:${String(secs).padStart(2, '0')}`;
}

/**
 * Format pace (seconds per km) to min:sec/km.
 */
export function formatPace(secondsPerKm: number | null): string {
  if (secondsPerKm === null) return '--';
  const mins = Math.floor(secondsPerKm / 60);
  const secs = secondsPerKm % 60;
  return `${mins}:${String(secs).padStart(2, '0')}/km`;
}

/**
 * Calculate volume (total weight lifted).
 */
export function calculateVolume(sets: WorkoutSet[]): number {
  return sets.reduce((total, set) => {
    if (set.weight_kg && set.reps) {
      return total + set.weight_kg * set.reps;
    }
    return total;
  }, 0);
}
