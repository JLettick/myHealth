/**
 * Daily workout summary card component.
 */

import { useWorkout } from '../../contexts/WorkoutContext';
import { formatWeight, formatDistance, formatDuration } from '../../types/workout';

export function WorkoutSummaryCard() {
  const { dailySummary, goals } = useWorkout();

  if (!dailySummary) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  const stats = [
    {
      label: 'Workouts',
      value: dailySummary.total_sessions.toString(),
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      label: 'Total Sets',
      value: dailySummary.total_sets.toString(),
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      label: 'Duration',
      value: dailySummary.total_duration_minutes
        ? `${dailySummary.total_duration_minutes} min`
        : '--',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      label: 'Volume',
      value: dailySummary.total_volume_kg
        ? formatWeight(dailySummary.total_volume_kg)
        : '--',
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
  ];

  // Add distance if available
  if (dailySummary.total_distance_meters && dailySummary.total_distance_meters > 0) {
    stats.push({
      label: 'Distance',
      value: formatDistance(dailySummary.total_distance_meters),
      color: 'text-teal-600',
      bgColor: 'bg-teal-50',
    });
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Daily Summary</h2>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className={`${stat.bgColor} rounded-lg p-4 text-center`}
          >
            <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
            <div className="text-sm text-gray-600 mt-1">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Weekly Goal Progress */}
      {goals && (goals.workouts_per_week_target || goals.minutes_per_week_target) && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-600 mb-3">Weekly Goals</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {goals.workouts_per_week_target && (
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Workouts</span>
                  <span className="font-medium">
                    ? / {goals.workouts_per_week_target}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: '0%' }}
                  />
                </div>
              </div>
            )}
            {goals.minutes_per_week_target && (
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Minutes</span>
                  <span className="font-medium">
                    ? / {goals.minutes_per_week_target}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-purple-600 h-2 rounded-full"
                    style={{ width: '0%' }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Exercise Summary */}
      {dailySummary.exercises.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-600 mb-3">Exercises Today</h3>
          <div className="flex flex-wrap gap-2">
            {dailySummary.exercises.map((ex) => (
              <span
                key={ex.exercise_id}
                className="px-3 py-1 bg-gray-100 rounded-full text-sm text-gray-700"
              >
                {ex.exercise_name}
                {ex.total_sets > 0 && ` (${ex.total_sets} sets)`}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
