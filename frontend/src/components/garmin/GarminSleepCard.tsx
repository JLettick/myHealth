/**
 * Garmin sleep card.
 *
 * Displays sleep duration and sleep score.
 */

import React from 'react';
import { useGarmin } from '../../contexts/GarminContext';
import { getSleepScoreColor } from '../../types/garmin';

export function GarminSleepCard(): JSX.Element {
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

  const sleepHours = dashboardSummary.latest_sleep_hours;
  const sleepScore = dashboardSummary.latest_sleep_score;
  const avgSleepHours = dashboardSummary.avg_sleep_hours_7d;

  // Format hours as "Xh Ym"
  const formatSleepHours = (hours: number | null): string => {
    if (hours === null) return '--';
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return `${h}h ${m}m`;
  };

  // Get sleep quality label
  const getSleepQualityLabel = (score: number | null): string => {
    if (score === null) return '--';
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Poor';
  };

  const scoreColorClass = {
    green: 'bg-green-500',
    blue: 'bg-blue-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500',
    gray: 'bg-gray-400',
  }[getSleepScoreColor(sleepScore)];

  return (
    <div className="bg-white p-6 rounded-xl shadow-md">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Sleep</h3>

      <div className="flex items-center justify-between mb-6">
        {/* Sleep Duration */}
        <div>
          <p className="text-4xl font-bold text-purple-600">
            {formatSleepHours(sleepHours)}
          </p>
          <p className="text-sm text-gray-500 mt-1">Last Night</p>
        </div>

        {/* Sleep Score */}
        <div className="text-center">
          <div
            className={`w-16 h-16 rounded-full ${scoreColorClass} flex items-center justify-center`}
          >
            <span className="text-xl font-bold text-white">
              {sleepScore != null ? sleepScore : '--'}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            {getSleepQualityLabel(sleepScore)}
          </p>
        </div>
      </div>

      {/* 7-day average */}
      <div className="pt-4 border-t border-gray-100">
        <p className="text-sm text-gray-500">
          7-day avg sleep:{' '}
          <span className="font-medium text-gray-700">
            {avgSleepHours != null ? formatSleepHours(avgSleepHours) : '--'}
          </span>
        </p>
      </div>
    </div>
  );
}

export default GarminSleepCard;
