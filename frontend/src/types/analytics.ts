/**
 * TypeScript types for Workout Analytics.
 */

import { getLocalDateString } from './workout';

// =============================================================================
// Time Range Types
// =============================================================================

export type TimeRangePreset = '30d' | '90d' | '6mo' | '1yr' | 'custom';

export interface TimeRange {
  start_date: string;
  end_date: string;
  preset: TimeRangePreset;
}

export type AnalyticsTab = 'exercise' | 'cardio' | 'trends';

// =============================================================================
// Exercise History Types
// =============================================================================

export interface ExerciseHistoryDataPoint {
  date: string;
  max_weight_kg: number | null;
  total_volume_kg: number | null;
  total_reps: number;
  avg_rpe: number | null;
  total_sets: number;
}

export interface ExerciseHistoryResponse {
  exercise_id: string;
  exercise_name: string;
  data: ExerciseHistoryDataPoint[];
}

// =============================================================================
// Cardio History Types
// =============================================================================

export interface CardioHistoryDataPoint {
  date: string;
  total_distance_meters: number | null;
  total_duration_seconds: number | null;
  avg_pace_seconds_per_km: number | null;
  avg_heart_rate: number | null;
  total_calories: number | null;
  total_sets: number;
}

export interface CardioHistoryResponse {
  exercise_id: string;
  exercise_name: string;
  data: CardioHistoryDataPoint[];
}

// =============================================================================
// Workout Trends Types
// =============================================================================

export interface WeeklyTrendDataPoint {
  week: string;
  week_start: string;
  total_sessions: number;
  total_sets: number;
  total_volume_kg: number | null;
  total_distance_meters: number | null;
  total_duration_minutes: number | null;
}

export interface WorkoutTrendsResponse {
  data: WeeklyTrendDataPoint[];
  workouts_per_week_target: number | null;
  minutes_per_week_target: number | null;
}

// =============================================================================
// Metric Types
// =============================================================================

export type ExerciseMetric = 'max_weight_kg' | 'total_volume_kg' | 'total_reps' | 'avg_rpe';

export const EXERCISE_METRIC_LABELS: Record<ExerciseMetric, string> = {
  max_weight_kg: 'Max Weight (kg)',
  total_volume_kg: 'Total Volume (kg)',
  total_reps: 'Total Reps',
  avg_rpe: 'Avg RPE',
};

export type CardioMetric = 'total_distance_meters' | 'total_duration_seconds' | 'avg_pace_seconds_per_km' | 'avg_heart_rate';

export const CARDIO_METRIC_LABELS: Record<CardioMetric, string> = {
  total_distance_meters: 'Distance (m)',
  total_duration_seconds: 'Duration (s)',
  avg_pace_seconds_per_km: 'Pace (s/km)',
  avg_heart_rate: 'Avg HR (bpm)',
};

export type TrendsMetric = 'total_sessions' | 'total_sets' | 'total_volume_kg' | 'total_distance_meters' | 'total_duration_minutes';

export const TRENDS_METRIC_LABELS: Record<TrendsMetric, string> = {
  total_sessions: 'Sessions',
  total_sets: 'Sets',
  total_volume_kg: 'Volume (kg)',
  total_distance_meters: 'Distance (m)',
  total_duration_minutes: 'Duration (min)',
};

// =============================================================================
// Utility Functions
// =============================================================================

export function getTimeRangeFromPreset(preset: TimeRangePreset): TimeRange {
  const now = new Date();
  const end_date = getLocalDateString(now);
  let start: Date;

  switch (preset) {
    case '30d':
      start = new Date(now);
      start.setDate(start.getDate() - 30);
      break;
    case '90d':
      start = new Date(now);
      start.setDate(start.getDate() - 90);
      break;
    case '6mo':
      start = new Date(now);
      start.setMonth(start.getMonth() - 6);
      break;
    case '1yr':
      start = new Date(now);
      start.setFullYear(start.getFullYear() - 1);
      break;
    case 'custom':
      // Default to 90 days for custom initial value
      start = new Date(now);
      start.setDate(start.getDate() - 90);
      break;
  }

  return {
    start_date: getLocalDateString(start),
    end_date,
    preset,
  };
}
