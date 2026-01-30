/**
 * Garmin activity summary card.
 *
 * Displays activity count and total active minutes.
 */

import React from 'react';
import { useGarmin } from '../../contexts/GarminContext';

export function GarminActivityCard(): JSX.Element {
  const { dashboardSummary, isLoading } = useGarmin();

  if (isLoading || !dashboardSummary) {
    return (
      <div className="bg-white p-6 rounded-xl shadow-md animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/2 mb-4" />
        <div className="h-12 bg-gray-200 rounded mb-2" />
        <div className="h-4 bg-gray-200 rounded w-3/4" />
      </div>
    );
  }

  const totalActivities = dashboardSummary.total_activities_7d;
  const totalActiveMinutes = dashboardSummary.total_active_minutes_7d;

  // Format minutes as hours and minutes
  const formatActiveMinutes = (minutes: number): string => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-md">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Activity (7 Days)
      </h3>

      <div className="flex items-center justify-between">
        {/* Total Activities */}
        <div className="text-center flex-1">
          <p className="text-4xl font-bold text-blue-600">{totalActivities}</p>
          <p className="text-sm text-gray-500 mt-1">Workouts</p>
        </div>

        {/* Divider */}
        <div className="w-px h-16 bg-gray-200 mx-4" />

        {/* Total Active Minutes */}
        <div className="text-center flex-1">
          <p className="text-4xl font-bold text-green-600">
            {formatActiveMinutes(totalActiveMinutes)}
          </p>
          <p className="text-sm text-gray-500 mt-1">Active Time</p>
        </div>
      </div>

      {/* Encouragement message */}
      <div className="mt-6 pt-4 border-t border-gray-100">
        <p className="text-sm text-gray-600 text-center">
          {totalActivities >= 5 ? (
            <span className="text-green-600">Great week! Keep it up!</span>
          ) : totalActivities >= 3 ? (
            <span className="text-blue-600">Good progress this week!</span>
          ) : (
            <span>Stay active to reach your goals!</span>
          )}
        </p>
      </div>
    </div>
  );
}

export default GarminActivityCard;
