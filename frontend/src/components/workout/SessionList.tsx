/**
 * List of workout sessions for a day.
 */

import type { WorkoutSessionListItem } from '../../types/workout';
import { WORKOUT_TYPE_LABELS } from '../../types/workout';

interface SessionListProps {
  sessions: WorkoutSessionListItem[];
  onSessionClick: (sessionId: string) => void;
}

export function SessionList({ sessions, onSessionClick }: SessionListProps) {
  if (sessions.length === 0) {
    return (
      <div className="p-8 text-center">
        <div className="text-gray-400 mb-2">
          <svg
            className="mx-auto h-12 w-12"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 6h16M4 10h16M4 14h16M4 18h16"
            />
          </svg>
        </div>
        <p className="text-gray-500">No workouts logged today</p>
        <p className="text-sm text-gray-400 mt-1">
          Click "Add Workout" to get started
        </p>
      </div>
    );
  }

  return (
    <ul className="divide-y divide-gray-100">
      {sessions.map((session) => (
        <li key={session.id}>
          <button
            onClick={() => onSessionClick(session.id)}
            className="w-full px-4 py-4 text-left hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900">
                    {session.name || WORKOUT_TYPE_LABELS[session.workout_type]}
                  </span>
                  <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100 text-gray-600">
                    {WORKOUT_TYPE_LABELS[session.workout_type]}
                  </span>
                </div>
                <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                  <span>{session.total_sets} sets</span>
                  {session.total_duration_minutes && (
                    <span>{session.total_duration_minutes} min</span>
                  )}
                  {session.rating && (
                    <span className="flex items-center gap-1">
                      <svg
                        className="h-4 w-4 text-yellow-400"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      {session.rating}
                    </span>
                  )}
                </div>
              </div>
              <svg
                className="h-5 w-5 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </div>
          </button>
        </li>
      ))}
    </ul>
  );
}
