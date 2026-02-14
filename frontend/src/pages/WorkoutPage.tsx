/**
 * Workout tracking page component (protected).
 */

import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useWorkout } from '../contexts/WorkoutContext';
import type { WorkoutType } from '../types/workout';
import {
  WorkoutSummaryCard,
  SessionList,
  AddSessionModal,
  SessionDetailModal,
  DateSelector,
} from '../components/workout';

export function WorkoutPage(): JSX.Element {
  const { isAuthenticated } = useAuth();
  const {
    dailySummary,
    selectedDate,
    setSelectedDate,
    currentSession,
    isLoading,
    error,
    loadSession,
    clearCurrentSession,
    refresh,
    refreshGoals,
    loadExercises,
  } = useWorkout();

  // Load workout data, goals, and exercises on mount
  const hasLoadedRef = useRef(false);
  useEffect(() => {
    if (isAuthenticated && !hasLoadedRef.current) {
      hasLoadedRef.current = true;
      refresh();
      refreshGoals();
      loadExercises();
    }
  }, [isAuthenticated]); // eslint-disable-line react-hooks/exhaustive-deps

  const [isAddSessionModalOpen, setIsAddSessionModalOpen] = useState(false);

  const handleSessionClick = async (sessionId: string) => {
    await loadSession(sessionId);
  };

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Workout Tracker</h1>
          <p className="text-gray-600 mt-2">
            Log your workouts and track your progress.
          </p>
        </div>
        <Link
          to="/analytics"
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          View Analytics
        </Link>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">{error}</div>
      )}

      {/* Date Selector */}
      <div className="mb-6">
        <DateSelector value={selectedDate} onChange={setSelectedDate} />
      </div>

      {/* Daily Workout Summary */}
      <div className="mb-8">
        <WorkoutSummaryCard />
      </div>

      {/* Sessions */}
      {isLoading ? (
        <div className="bg-white rounded-lg shadow p-4 animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Workouts
            </h2>
            <button
              onClick={() => setIsAddSessionModalOpen(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              Add Workout
            </button>
          </div>

          <SessionList
            sessions={dailySummary?.sessions || []}
            onSessionClick={handleSessionClick}
          />
        </div>
      )}

      {/* Add Session Modal */}
      <AddSessionModal
        isOpen={isAddSessionModalOpen}
        onClose={() => setIsAddSessionModalOpen(false)}
        selectedDate={selectedDate}
      />

      {/* Session Detail Modal */}
      {currentSession && (
        <SessionDetailModal
          session={currentSession}
          onClose={clearCurrentSession}
        />
      )}
    </div>
  );
}
