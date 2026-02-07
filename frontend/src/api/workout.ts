/**
 * Workout API functions for the frontend.
 */

import apiClient from './client';
import type {
  Exercise,
  ExerciseCreate,
  ExerciseUpdate,
  ExerciseListResponse,
  ExerciseSearchResponse,
  WorkoutSession,
  WorkoutSessionCreate,
  WorkoutSessionUpdate,
  WorkoutSessionListResponse,
  WorkoutSet,
  WorkoutSetCreate,
  WorkoutSetUpdate,
  DailyWorkoutSummary,
  WeeklyWorkoutSummary,
  WorkoutGoals,
  WorkoutGoalsCreate,
} from '../types/workout';
import { logger } from '../utils/logger';

// =============================================================================
// EXERCISES API
// =============================================================================

export async function createExercise(exercise: ExerciseCreate): Promise<Exercise> {
  logger.info('Creating custom exercise', { name: exercise.name });
  const response = await apiClient.post<Exercise>('/workout/exercises', exercise);
  return response.data;
}

export async function searchExercises(
  query: string = '',
  category?: string,
  page: number = 1,
  pageSize: number = 50
): Promise<ExerciseSearchResponse> {
  logger.debug('Searching exercises', { query, category, page });
  const params = new URLSearchParams({
    q: query,
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (category) {
    params.set('category', category);
  }
  const response = await apiClient.get<ExerciseSearchResponse>(
    `/workout/exercises/search?${params}`
  );
  return response.data;
}

export async function getMyExercises(
  page: number = 1,
  pageSize: number = 50
): Promise<ExerciseListResponse> {
  logger.debug('Getting my exercises', { page });
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  const response = await apiClient.get<ExerciseListResponse>(
    `/workout/exercises/my?${params}`
  );
  return response.data;
}

export async function getExercise(exerciseId: string): Promise<Exercise> {
  const response = await apiClient.get<Exercise>(
    `/workout/exercises/${exerciseId}`
  );
  return response.data;
}

export async function updateExercise(
  exerciseId: string,
  exercise: ExerciseUpdate
): Promise<Exercise> {
  logger.info('Updating exercise', { exerciseId });
  const response = await apiClient.put<Exercise>(
    `/workout/exercises/${exerciseId}`,
    exercise
  );
  return response.data;
}

export async function deleteExercise(exerciseId: string): Promise<void> {
  logger.info('Deleting exercise', { exerciseId });
  await apiClient.delete(`/workout/exercises/${exerciseId}`);
}

// =============================================================================
// WORKOUT SESSIONS API
// =============================================================================

export async function createSession(
  session: WorkoutSessionCreate
): Promise<WorkoutSession> {
  logger.info('Creating workout session');
  const response = await apiClient.post<WorkoutSession>(
    '/workout/sessions',
    session
  );
  return response.data;
}

export async function getSessions(
  sessionDate?: string,
  startDate?: string,
  endDate?: string,
  page: number = 1,
  pageSize: number = 20
): Promise<WorkoutSessionListResponse> {
  logger.debug('Getting workout sessions', { sessionDate, startDate, endDate });
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (sessionDate) {
    params.set('session_date', sessionDate);
  }
  if (startDate) {
    params.set('start_date', startDate);
  }
  if (endDate) {
    params.set('end_date', endDate);
  }
  const response = await apiClient.get<WorkoutSessionListResponse>(
    `/workout/sessions?${params}`
  );
  return response.data;
}

export async function getSession(sessionId: string): Promise<WorkoutSession> {
  const response = await apiClient.get<WorkoutSession>(
    `/workout/sessions/${sessionId}`
  );
  return response.data;
}

export async function updateSession(
  sessionId: string,
  session: WorkoutSessionUpdate
): Promise<WorkoutSession> {
  logger.info('Updating workout session', { sessionId });
  const response = await apiClient.put<WorkoutSession>(
    `/workout/sessions/${sessionId}`,
    session
  );
  return response.data;
}

export async function deleteSession(sessionId: string): Promise<void> {
  logger.info('Deleting workout session', { sessionId });
  await apiClient.delete(`/workout/sessions/${sessionId}`);
}

// =============================================================================
// WORKOUT SETS API
// =============================================================================

export async function createSet(
  sessionId: string,
  workoutSet: WorkoutSetCreate
): Promise<WorkoutSet> {
  logger.info('Creating workout set', { sessionId });
  const response = await apiClient.post<WorkoutSet>(
    `/workout/sessions/${sessionId}/sets`,
    workoutSet
  );
  return response.data;
}

export async function getSet(setId: string): Promise<WorkoutSet> {
  const response = await apiClient.get<WorkoutSet>(`/workout/sets/${setId}`);
  return response.data;
}

export async function updateSet(
  setId: string,
  workoutSet: WorkoutSetUpdate
): Promise<WorkoutSet> {
  logger.info('Updating workout set', { setId });
  const response = await apiClient.put<WorkoutSet>(
    `/workout/sets/${setId}`,
    workoutSet
  );
  return response.data;
}

export async function deleteSet(setId: string): Promise<void> {
  logger.info('Deleting workout set', { setId });
  await apiClient.delete(`/workout/sets/${setId}`);
}

// =============================================================================
// SUMMARIES API
// =============================================================================

export async function getDailySummary(
  date?: string
): Promise<DailyWorkoutSummary> {
  logger.debug('Getting daily workout summary', { date });
  const params = date ? `?summary_date=${date}` : '';
  const response = await apiClient.get<DailyWorkoutSummary>(
    `/workout/summary/daily${params}`
  );
  return response.data;
}

export async function getWeeklySummary(
  startDate?: string
): Promise<WeeklyWorkoutSummary> {
  logger.debug('Getting weekly workout summary', { startDate });
  const params = startDate ? `?start_date=${startDate}` : '';
  const response = await apiClient.get<WeeklyWorkoutSummary>(
    `/workout/summary/weekly${params}`
  );
  return response.data;
}

// =============================================================================
// GOALS API
// =============================================================================

export async function getGoals(): Promise<WorkoutGoals | null> {
  logger.debug('Getting workout goals');
  const response = await apiClient.get<WorkoutGoals | null>('/workout/goals');
  return response.data;
}

export async function setGoals(goals: WorkoutGoalsCreate): Promise<WorkoutGoals> {
  logger.info('Setting workout goals');
  const response = await apiClient.put<WorkoutGoals>('/workout/goals', goals);
  return response.data;
}
