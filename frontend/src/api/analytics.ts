/**
 * Analytics API functions for the frontend.
 */

import apiClient from './client';
import type {
  ExerciseHistoryResponse,
  CardioHistoryResponse,
  WorkoutTrendsResponse,
} from '../types/analytics';
import type { ExerciseSearchResponse } from '../types/workout';
import { logger } from '../utils/logger';

export async function getLoggedExercises(
  query: string = '',
  setType?: string
): Promise<ExerciseSearchResponse> {
  logger.debug('Getting logged exercises', { query, setType });
  const params = new URLSearchParams({ q: query });
  if (setType) {
    params.set('set_type', setType);
  }
  const response = await apiClient.get<ExerciseSearchResponse>(
    `/workout/analytics/exercises?${params}`
  );
  return response.data;
}

export async function getExerciseHistory(
  exerciseId: string,
  startDate: string,
  endDate: string
): Promise<ExerciseHistoryResponse> {
  logger.debug('Getting exercise history', { exerciseId, startDate, endDate });
  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
  });
  const response = await apiClient.get<ExerciseHistoryResponse>(
    `/workout/analytics/exercise/${exerciseId}?${params}`
  );
  return response.data;
}

export async function getCardioHistory(
  exerciseId: string,
  startDate: string,
  endDate: string
): Promise<CardioHistoryResponse> {
  logger.debug('Getting cardio history', { exerciseId, startDate, endDate });
  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
  });
  const response = await apiClient.get<CardioHistoryResponse>(
    `/workout/analytics/cardio/${exerciseId}?${params}`
  );
  return response.data;
}

export async function getWorkoutTrends(
  startDate: string,
  endDate: string
): Promise<WorkoutTrendsResponse> {
  logger.debug('Getting workout trends', { startDate, endDate });
  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
  });
  const response = await apiClient.get<WorkoutTrendsResponse>(
    `/workout/analytics/trends?${params}`
  );
  return response.data;
}
