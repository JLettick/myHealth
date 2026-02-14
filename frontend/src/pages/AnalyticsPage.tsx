/**
 * Workout Analytics page component (protected).
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { TimeRangeSelector } from '../components/analytics/TimeRangeSelector';
import { AnalyticsTabNav } from '../components/analytics/AnalyticsTabNav';
import { ExerciseSelector } from '../components/analytics/ExerciseSelector';
import { ExerciseProgressionChart } from '../components/analytics/ExerciseProgressionChart';
import { CardioPerformanceChart } from '../components/analytics/CardioPerformanceChart';
import { OverallTrendsChart } from '../components/analytics/OverallTrendsChart';
import { EmptyAnalyticsState } from '../components/analytics/EmptyAnalyticsState';
import { getExerciseHistory, getCardioHistory, getWorkoutTrends } from '../api/analytics';
import type {
  AnalyticsTab,
  TimeRange,
  ExerciseHistoryDataPoint,
  CardioHistoryDataPoint,
  WeeklyTrendDataPoint,
} from '../types/analytics';
import { getTimeRangeFromPreset } from '../types/analytics';
import type { Exercise } from '../types/workout';

export function AnalyticsPage(): JSX.Element {
  const { isAuthenticated } = useAuth();

  // State
  const [activeTab, setActiveTab] = useState<AnalyticsTab>('exercise');
  const [timeRange, setTimeRange] = useState<TimeRange>(() => getTimeRangeFromPreset('90d'));
  const [selectedExercise, setSelectedExercise] = useState<Exercise | null>(null);

  // Chart data
  const [exerciseHistory, setExerciseHistory] = useState<ExerciseHistoryDataPoint[]>([]);
  const [cardioHistory, setCardioHistory] = useState<CardioHistoryDataPoint[]>([]);
  const [workoutTrends, setWorkoutTrends] = useState<WeeklyTrendDataPoint[]>([]);
  const [trendsGoals, setTrendsGoals] = useState<{
    workouts_per_week_target: number | null;
    minutes_per_week_target: number | null;
  }>({ workouts_per_week_target: null, minutes_per_week_target: null });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Stale request guard
  const fetchIdRef = useRef(0);

  // Fetch exercise history
  const fetchExerciseHistory = useCallback(
    async (exerciseId: string, range: TimeRange) => {
      const fetchId = ++fetchIdRef.current;
      setIsLoading(true);
      setError(null);
      try {
        const result = await getExerciseHistory(exerciseId, range.start_date, range.end_date);
        if (fetchId === fetchIdRef.current) {
          setExerciseHistory(result.data);
        }
      } catch {
        if (fetchId === fetchIdRef.current) {
          setError('Failed to load exercise history.');
        }
      } finally {
        if (fetchId === fetchIdRef.current) {
          setIsLoading(false);
        }
      }
    },
    []
  );

  // Fetch cardio history
  const fetchCardioHistory = useCallback(
    async (exerciseId: string, range: TimeRange) => {
      const fetchId = ++fetchIdRef.current;
      setIsLoading(true);
      setError(null);
      try {
        const result = await getCardioHistory(exerciseId, range.start_date, range.end_date);
        if (fetchId === fetchIdRef.current) {
          setCardioHistory(result.data);
        }
      } catch {
        if (fetchId === fetchIdRef.current) {
          setError('Failed to load cardio history.');
        }
      } finally {
        if (fetchId === fetchIdRef.current) {
          setIsLoading(false);
        }
      }
    },
    []
  );

  // Fetch workout trends
  const fetchWorkoutTrends = useCallback(
    async (range: TimeRange) => {
      const fetchId = ++fetchIdRef.current;
      setIsLoading(true);
      setError(null);
      try {
        const result = await getWorkoutTrends(range.start_date, range.end_date);
        if (fetchId === fetchIdRef.current) {
          setWorkoutTrends(result.data);
          setTrendsGoals({
            workouts_per_week_target: result.workouts_per_week_target,
            minutes_per_week_target: result.minutes_per_week_target,
          });
        }
      } catch {
        if (fetchId === fetchIdRef.current) {
          setError('Failed to load workout trends.');
        }
      } finally {
        if (fetchId === fetchIdRef.current) {
          setIsLoading(false);
        }
      }
    },
    []
  );

  // Fetch data when tab, exercise, or time range changes
  useEffect(() => {
    if (!isAuthenticated) return;

    if (activeTab === 'trends') {
      fetchWorkoutTrends(timeRange);
    } else if (selectedExercise) {
      if (activeTab === 'exercise') {
        fetchExerciseHistory(selectedExercise.id, timeRange);
      } else if (activeTab === 'cardio') {
        fetchCardioHistory(selectedExercise.id, timeRange);
      }
    }
  }, [activeTab, selectedExercise, timeRange, isAuthenticated, fetchExerciseHistory, fetchCardioHistory, fetchWorkoutTrends]);

  // Handle tab change
  const handleTabChange = (tab: AnalyticsTab) => {
    setActiveTab(tab);
    setSelectedExercise(null);
    setExerciseHistory([]);
    setCardioHistory([]);
    setError(null);
  };

  // Handle exercise selection
  const handleExerciseSelect = (exercise: Exercise) => {
    setSelectedExercise(exercise);
  };

  // Determine whether to show exercise selector
  const showExerciseSelector = activeTab === 'exercise' || activeTab === 'cardio';

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-1">
            Track your workout progress over time.
          </p>
        </div>
        <Link
          to="/workout"
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          Back to Workouts
        </Link>
      </div>

      {/* Time Range Selector */}
      <div className="mb-4">
        <TimeRangeSelector value={timeRange} onChange={setTimeRange} />
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <AnalyticsTabNav activeTab={activeTab} onChange={handleTabChange} />

        <div className="p-6">
          {/* Exercise Selector */}
          {showExerciseSelector && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Exercise
              </label>
              <ExerciseSelector
                selectedExerciseId={selectedExercise?.id ?? null}
                onSelect={handleExerciseSelect}
                activeTab={activeTab}
              />
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Loading */}
          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            </div>
          ) : (
            <>
              {/* Exercise Progression Chart */}
              {activeTab === 'exercise' && (
                selectedExercise ? (
                  <ExerciseProgressionChart
                    data={exerciseHistory}
                    exerciseName={selectedExercise.name}
                  />
                ) : (
                  <EmptyAnalyticsState message="Select an exercise to view progression data." />
                )
              )}

              {/* Cardio Performance Chart */}
              {activeTab === 'cardio' && (
                selectedExercise ? (
                  <CardioPerformanceChart
                    data={cardioHistory}
                    exerciseName={selectedExercise.name}
                  />
                ) : (
                  <EmptyAnalyticsState message="Select a cardio exercise to view performance data." />
                )
              )}

              {/* Overall Trends Chart */}
              {activeTab === 'trends' && (
                <OverallTrendsChart
                  data={workoutTrends}
                  workoutsPerWeekTarget={trendsGoals.workouts_per_week_target}
                  minutesPerWeekTarget={trendsGoals.minutes_per_week_target}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
