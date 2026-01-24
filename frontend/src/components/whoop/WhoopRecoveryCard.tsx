/**
 * Component for displaying Whoop recovery metrics.
 */

import React from 'react';
import { useWhoop } from '../../contexts/WhoopContext';
import { getRecoveryColor } from '../../types/whoop';

export function WhoopRecoveryCard() {
  const { dashboardSummary, isConnected, isLoading } = useWhoop();

  if (!isConnected || isLoading) {
    return null;
  }

  const recoveryScore = dashboardSummary?.latest_recovery_score;
  const hrv = dashboardSummary?.latest_hrv;
  const restingHr = dashboardSummary?.latest_resting_hr;
  const avgRecovery = dashboardSummary?.avg_recovery_7d;

  const getRecoveryBgColor = (score: number | null) => {
    const color = getRecoveryColor(score);
    switch (color) {
      case 'green':
        return 'bg-green-500';
      case 'yellow':
        return 'bg-yellow-500';
      case 'red':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getRecoveryTextColor = (score: number | null) => {
    const color = getRecoveryColor(score);
    switch (color) {
      case 'green':
        return 'text-green-600';
      case 'yellow':
        return 'text-yellow-600';
      case 'red':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Recovery</h3>

      {/* Main recovery score */}
      <div className="flex items-center justify-center mb-6">
        <div className="relative">
          <div
            className={`w-24 h-24 rounded-full ${getRecoveryBgColor(
              recoveryScore ?? null
            )} flex items-center justify-center`}
          >
            <span className="text-3xl font-bold text-white">
              {recoveryScore !== null && recoveryScore !== undefined
                ? `${Math.round(recoveryScore)}%`
                : '--'}
            </span>
          </div>
        </div>
      </div>

      {/* Recovery metrics */}
      <div className="grid grid-cols-2 gap-4">
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className="text-2xl font-semibold text-gray-900">
            {hrv !== null && hrv !== undefined ? Math.round(hrv) : '--'}
          </div>
          <div className="text-sm text-gray-500">HRV (ms)</div>
        </div>

        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className="text-2xl font-semibold text-gray-900">
            {restingHr !== null && restingHr !== undefined
              ? Math.round(restingHr)
              : '--'}
          </div>
          <div className="text-sm text-gray-500">Resting HR</div>
        </div>
      </div>

      {/* 7-day average */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">7-Day Average</span>
          <span className={`font-semibold ${getRecoveryTextColor(avgRecovery ?? null)}`}>
            {avgRecovery !== null && avgRecovery !== undefined
              ? `${Math.round(avgRecovery)}%`
              : '--'}
          </span>
        </div>
      </div>
    </div>
  );
}
