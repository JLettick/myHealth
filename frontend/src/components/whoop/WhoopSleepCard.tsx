/**
 * Component for displaying Whoop sleep metrics.
 */

import React from 'react';
import { useWhoop } from '../../contexts/WhoopContext';

export function WhoopSleepCard() {
  const { dashboardSummary, isConnected, isLoading } = useWhoop();

  if (!isConnected || isLoading) {
    return null;
  }

  const sleepScore = dashboardSummary?.latest_sleep_score;
  const sleepHours = dashboardSummary?.latest_sleep_hours;
  const avgSleepHours = dashboardSummary?.avg_sleep_hours_7d;

  const formatHours = (hours: number | null): string => {
    if (hours === null || hours === undefined) return '--';
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return `${h}h ${m}m`;
  };

  const getSleepScoreColor = (score: number | null): string => {
    if (score === null) return 'text-gray-600';
    if (score >= 85) return 'text-green-600';
    if (score >= 70) return 'text-blue-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getSleepScoreBg = (score: number | null): string => {
    if (score === null) return 'bg-gray-400';
    if (score >= 85) return 'bg-green-500';
    if (score >= 70) return 'bg-blue-500';
    if (score >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Sleep</h3>

      {/* Main sleep display */}
      <div className="flex items-center justify-between mb-6">
        {/* Sleep duration */}
        <div className="text-center flex-1">
          <div className="text-3xl font-bold text-gray-900">
            {formatHours(sleepHours ?? null)}
          </div>
          <div className="text-sm text-gray-500">Last Night</div>
        </div>

        {/* Divider */}
        <div className="w-px h-12 bg-gray-200 mx-4" />

        {/* Sleep score */}
        <div className="text-center flex-1">
          <div
            className={`w-16 h-16 rounded-full ${getSleepScoreBg(
              sleepScore ?? null
            )} flex items-center justify-center mx-auto`}
          >
            <span className="text-xl font-bold text-white">
              {sleepScore !== null && sleepScore !== undefined
                ? Math.round(sleepScore)
                : '--'}
            </span>
          </div>
          <div className="text-sm text-gray-500 mt-1">Score</div>
        </div>
      </div>

      {/* Sleep metrics */}
      <div className="space-y-3">
        <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
          <span className="text-sm text-gray-600">7-Day Average</span>
          <span className="font-semibold text-gray-900">
            {formatHours(avgSleepHours ?? null)}
          </span>
        </div>

        {/* Sleep quality indicator */}
        <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
          <span className="text-sm text-gray-600">Sleep Performance</span>
          <span className={`font-semibold ${getSleepScoreColor(sleepScore ?? null)}`}>
            {sleepScore !== null && sleepScore !== undefined
              ? sleepScore >= 85
                ? 'Optimal'
                : sleepScore >= 70
                ? 'Good'
                : sleepScore >= 50
                ? 'Fair'
                : 'Poor'
              : '--'}
          </span>
        </div>
      </div>
    </div>
  );
}
