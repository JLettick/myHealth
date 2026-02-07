/**
 * Workout Context for managing workout tracking state.
 */

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from 'react';
import {
  getLocalDateString,
  type DailyWorkoutSummary,
  type WorkoutGoals,
  type WorkoutSession,
  type WorkoutSessionCreate,
  type WorkoutSessionUpdate,
  type WorkoutSet,
  type WorkoutSetCreate,
  type WorkoutSetUpdate,
  type WorkoutGoalsCreate,
  type Exercise,
  type ExerciseCreate,
} from '../types/workout';
import {
  getDailySummary,
  getGoals,
  getSession,
  createSession as createSessionApi,
  updateSession as updateSessionApi,
  deleteSession as deleteSessionApi,
  createSet as createSetApi,
  updateSet as updateSetApi,
  deleteSet as deleteSetApi,
  setGoals as setGoalsApi,
  searchExercises,
  createExercise as createExerciseApi,
} from '../api/workout';
import { useAuth } from './AuthContext';
import { logger } from '../utils/logger';

interface WorkoutContextValue {
  // Data
  dailySummary: DailyWorkoutSummary | null;
  goals: WorkoutGoals | null;
  selectedDate: string;
  currentSession: WorkoutSession | null;
  exercises: Exercise[];

  // Loading states
  isLoading: boolean;
  error: string | null;

  // Date navigation
  setSelectedDate: (date: string) => void;

  // Session actions
  refresh: () => Promise<void>;
  addSession: (session: WorkoutSessionCreate) => Promise<WorkoutSession | null>;
  editSession: (sessionId: string, updates: WorkoutSessionUpdate) => Promise<void>;
  removeSession: (sessionId: string) => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  clearCurrentSession: () => void;

  // Set actions
  addSet: (sessionId: string, workoutSet: WorkoutSetCreate) => Promise<WorkoutSet | null>;
  editSet: (setId: string, updates: WorkoutSetUpdate) => Promise<void>;
  removeSet: (setId: string) => Promise<void>;

  // Goals actions
  updateGoals: (goals: WorkoutGoalsCreate) => Promise<void>;

  // Exercise actions
  loadExercises: (query?: string, category?: string) => Promise<void>;
  createExercise: (exercise: ExerciseCreate) => Promise<Exercise | null>;

  // Utility
  clearError: () => void;
}

const WorkoutContext = createContext<WorkoutContextValue | null>(null);

interface WorkoutProviderProps {
  children: React.ReactNode;
}

export function WorkoutProvider({ children }: WorkoutProviderProps) {
  const { isAuthenticated } = useAuth();

  // State
  const [dailySummary, setDailySummary] = useState<DailyWorkoutSummary | null>(null);
  const [goals, setGoals] = useState<WorkoutGoals | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(getLocalDateString());
  const [currentSession, setCurrentSession] = useState<WorkoutSession | null>(null);
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearCurrentSession = useCallback(() => {
    setCurrentSession(null);
  }, []);

  // Fetch goals
  const refreshGoals = useCallback(async () => {
    if (!isAuthenticated) {
      setGoals(null);
      return;
    }

    try {
      logger.debug('[WorkoutContext] Fetching goals');
      const goalsResult = await getGoals();
      setGoals(goalsResult);
    } catch (err) {
      logger.debug('[WorkoutContext] Goals not set or fetch failed');
      setGoals(null);
    }
  }, [isAuthenticated]);

  // Fetch daily summary
  const refresh = useCallback(async () => {
    if (!isAuthenticated) {
      setDailySummary(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      logger.debug('[WorkoutContext] Refreshing daily summary', { date: selectedDate });
      const summaryResult = await getDailySummary(selectedDate);
      setDailySummary(summaryResult);
      logger.info('[WorkoutContext] Daily summary refreshed');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load workout data';
      logger.error('[WorkoutContext] Refresh failed', { error: message });
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, selectedDate]);

  // Load exercises
  const loadExercises = useCallback(
    async (query: string = '', category?: string) => {
      if (!isAuthenticated) return;

      try {
        const result = await searchExercises(query, category);
        setExercises(result.results);
      } catch (err) {
        logger.error('[WorkoutContext] Failed to load exercises', { error: err });
      }
    },
    [isAuthenticated]
  );

  // Create custom exercise
  const createExercise = useCallback(
    async (exercise: ExerciseCreate): Promise<Exercise | null> => {
      try {
        const result = await createExerciseApi(exercise);
        // Reload exercises to include the new one
        await loadExercises();
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to create exercise';
        setError(message);
        return null;
      }
    },
    [loadExercises]
  );

  // Load session with sets
  const loadSession = useCallback(
    async (sessionId: string) => {
      if (!isAuthenticated) return;

      try {
        setIsLoading(true);
        const session = await getSession(sessionId);
        setCurrentSession(session);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load session';
        setError(message);
      } finally {
        setIsLoading(false);
      }
    },
    [isAuthenticated]
  );

  // Add session
  const addSession = useCallback(
    async (session: WorkoutSessionCreate): Promise<WorkoutSession | null> => {
      try {
        const result = await createSessionApi(session);
        await refresh();
        setCurrentSession(result);
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to create session';
        setError(message);
        return null;
      }
    },
    [refresh]
  );

  // Edit session
  const editSession = useCallback(
    async (sessionId: string, updates: WorkoutSessionUpdate): Promise<void> => {
      try {
        const result = await updateSessionApi(sessionId, updates);
        setCurrentSession(result);
        await refresh();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to update session';
        setError(message);
      }
    },
    [refresh]
  );

  // Remove session
  const removeSession = useCallback(
    async (sessionId: string): Promise<void> => {
      try {
        await deleteSessionApi(sessionId);
        if (currentSession?.id === sessionId) {
          setCurrentSession(null);
        }
        await refresh();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to delete session';
        setError(message);
      }
    },
    [currentSession, refresh]
  );

  // Add set
  const addSet = useCallback(
    async (sessionId: string, workoutSet: WorkoutSetCreate): Promise<WorkoutSet | null> => {
      try {
        const result = await createSetApi(sessionId, workoutSet);
        // Reload current session to get updated sets
        if (currentSession?.id === sessionId) {
          await loadSession(sessionId);
        }
        await refresh();
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to add set';
        setError(message);
        return null;
      }
    },
    [currentSession, loadSession, refresh]
  );

  // Edit set
  const editSet = useCallback(
    async (setId: string, updates: WorkoutSetUpdate): Promise<void> => {
      try {
        await updateSetApi(setId, updates);
        // Reload current session to get updated sets
        if (currentSession) {
          await loadSession(currentSession.id);
        }
        await refresh();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to update set';
        setError(message);
      }
    },
    [currentSession, loadSession, refresh]
  );

  // Remove set
  const removeSet = useCallback(
    async (setId: string): Promise<void> => {
      try {
        await deleteSetApi(setId);
        // Reload current session to get updated sets
        if (currentSession) {
          await loadSession(currentSession.id);
        }
        await refresh();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to delete set';
        setError(message);
      }
    },
    [currentSession, loadSession, refresh]
  );

  // Update goals
  const updateGoalsFn = useCallback(
    async (newGoals: WorkoutGoalsCreate): Promise<void> => {
      try {
        const result = await setGoalsApi(newGoals);
        setGoals(result);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to update goals';
        setError(message);
      }
    },
    []
  );

  // Load goals on mount and when auth changes
  useEffect(() => {
    if (isAuthenticated) {
      refreshGoals();
    } else {
      setGoals(null);
    }
  }, [isAuthenticated, refreshGoals]);

  // Load daily summary when auth or date changes
  useEffect(() => {
    if (isAuthenticated) {
      refresh();
    } else {
      setDailySummary(null);
      setError(null);
    }
  }, [isAuthenticated, selectedDate, refresh]);

  // Load exercises on mount
  useEffect(() => {
    if (isAuthenticated) {
      loadExercises();
    }
  }, [isAuthenticated, loadExercises]);

  const value: WorkoutContextValue = {
    dailySummary,
    goals,
    selectedDate,
    currentSession,
    exercises,
    isLoading,
    error,
    setSelectedDate,
    refresh,
    addSession,
    editSession,
    removeSession,
    loadSession,
    clearCurrentSession,
    addSet,
    editSet,
    removeSet,
    updateGoals: updateGoalsFn,
    loadExercises,
    createExercise,
    clearError,
  };

  return (
    <WorkoutContext.Provider value={value}>
      {children}
    </WorkoutContext.Provider>
  );
}

export function useWorkout(): WorkoutContextValue {
  const context = useContext(WorkoutContext);
  if (!context) {
    throw new Error('useWorkout must be used within a WorkoutProvider');
  }
  return context;
}
