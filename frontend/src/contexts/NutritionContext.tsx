/**
 * Nutrition Context for managing nutrition tracking state.
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
  type DailySummary,
  type NutritionGoals,
  type FoodEntry,
  type FoodEntryCreate,
  type FoodEntryUpdate,
  type NutritionGoalsCreate,
} from '../types/nutrition';
import {
  getDailySummary,
  getGoals,
  createEntry,
  updateEntry as updateEntryApi,
  deleteEntry as deleteEntryApi,
  setGoals as setGoalsApi,
} from '../api/nutrition';
import { useAuth } from './AuthContext';
import { logger } from '../utils/logger';

interface NutritionContextValue {
  // Data
  dailySummary: DailySummary | null;
  goals: NutritionGoals | null;
  selectedDate: string;

  // Loading states
  isLoading: boolean;
  error: string | null;

  // Actions
  setSelectedDate: (date: string) => void;
  refresh: () => Promise<void>;
  addEntry: (entry: FoodEntryCreate) => Promise<FoodEntry | null>;
  updateEntry: (entryId: string, updates: FoodEntryUpdate) => Promise<void>;
  removeEntry: (entryId: string) => Promise<void>;
  updateGoals: (goals: NutritionGoalsCreate) => Promise<void>;
  clearError: () => void;
}

const NutritionContext = createContext<NutritionContextValue | null>(null);

interface NutritionProviderProps {
  children: React.ReactNode;
}

export function NutritionProvider({ children }: NutritionProviderProps) {
  const { isAuthenticated } = useAuth();

  // State
  const [dailySummary, setDailySummary] = useState<DailySummary | null>(null);
  const [goals, setGoals] = useState<NutritionGoals | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(getLocalDateString());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Fetch goals (only on mount, not on date change)
  const refreshGoals = useCallback(async () => {
    if (!isAuthenticated) {
      setGoals(null);
      return;
    }

    try {
      logger.debug('[NutritionContext] Fetching goals');
      const goalsResult = await getGoals();
      setGoals(goalsResult);
    } catch (err) {
      logger.debug('[NutritionContext] Goals not set or fetch failed');
      setGoals(null);
    }
  }, [isAuthenticated]);

  // Fetch daily summary (on date change)
  const refresh = useCallback(async () => {
    if (!isAuthenticated) {
      setDailySummary(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      logger.debug('[NutritionContext] Refreshing daily summary', { date: selectedDate });
      const summaryResult = await getDailySummary(selectedDate);
      setDailySummary(summaryResult);
      logger.info('[NutritionContext] Daily summary refreshed');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load nutrition data';
      logger.error('[NutritionContext] Refresh failed', { error: message });
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, selectedDate]);

  // Add entry
  const addEntry = useCallback(
    async (entry: FoodEntryCreate): Promise<FoodEntry | null> => {
      try {
        const result = await createEntry(entry);
        await refresh();
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to add entry';
        setError(message);
        return null;
      }
    },
    [refresh]
  );

  // Update entry
  const updateEntryFn = useCallback(
    async (entryId: string, updates: FoodEntryUpdate): Promise<void> => {
      try {
        await updateEntryApi(entryId, updates);
        await refresh();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to update entry';
        setError(message);
      }
    },
    [refresh]
  );

  // Remove entry
  const removeEntry = useCallback(
    async (entryId: string): Promise<void> => {
      try {
        await deleteEntryApi(entryId);
        await refresh();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to delete entry';
        setError(message);
      }
    },
    [refresh]
  );

  // Update goals
  const updateGoalsFn = useCallback(
    async (newGoals: NutritionGoalsCreate): Promise<void> => {
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

  // Load goals on mount and when auth changes (not on date change)
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

  const value: NutritionContextValue = {
    dailySummary,
    goals,
    selectedDate,
    isLoading,
    error,
    setSelectedDate,
    refresh,
    addEntry,
    updateEntry: updateEntryFn,
    removeEntry,
    updateGoals: updateGoalsFn,
    clearError,
  };

  return (
    <NutritionContext.Provider value={value}>
      {children}
    </NutritionContext.Provider>
  );
}

export function useNutrition(): NutritionContextValue {
  const context = useContext(NutritionContext);
  if (!context) {
    throw new Error('useNutrition must be used within a NutritionProvider');
  }
  return context;
}
