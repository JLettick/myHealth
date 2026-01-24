/**
 * Component for displaying Whoop strain metrics.
 */

import React from 'react';
import { useWhoop } from '../../contexts/WhoopContext';
import { getStrainColor } from '../../types/whoop';

export function WhoopStrainCard() {
  const { dashboardSummary, isConnected, isLoading } = useWhoop();

  if (!isConnected || isLoading) {
    return null;
  }

  const strainScore = dashboardSummary?.latest_strain_score;
  const avgStrain = dashboardSummary?.avg_strain_7d;
  const totalWorkouts = dashboardSummary?.total_workouts_7d ?? 0;

  const getStrainBgColor = (score: number | null): string => {
    const color = getStrainColor(score);
    switch (color) {
      case 'red':
        return 'bg-red-500';
      case 'orange':
        return 'bg-orange-500';
      case 'yellow':
        return 'bg-yellow-500';
      case 'blue':
        return 'bg-blue-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getStrainTextColor = (score: number | null): string => {
    const color = getStrainColor(score);
    switch (color) {
      case 'red':
        return 'text-red-600';
      case 'orange':
        return 'text-orange-600';
      case 'yellow':
        return 'text-yellow-600';
      case 'blue':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStrainLevel = (score: number | null): string => {
    if (score === null) return '--';
    if (score >= 18) return 'All Out';
    if (score >= 14) return 'Strenuous';
    if (score >= 10) return 'Moderate';
    return 'Light';
  };

  // Calculate strain percentage for visual gauge (0-21 scale)
  const strainPercentage =
    strainScore !== null && strainScore !== undefined
      ? Math.min((Number(strainScore) / 21) * 100, 100)
      : 0;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Strain</h3>

      {/* Main strain display */}
      <div className="flex items-center justify-center mb-6">
        <div className="relative w-32 h-32">
          {/* Background circle */}
          <svg className="w-32 h-32 transform -rotate-90">
            <circle
              cx="64"
              cy="64"
              r="56"
              stroke="#e5e7eb"
              strokeWidth="12"
              fill="none"
            />
            <circle
              cx="64"
              cy="64"
              r="56"
              stroke={
                getStrainColor(strainScore ?? null) === 'red'
                  ? '#ef4444'
                  : getStrainColor(strainScore ?? null) === 'orange'
                  ? '#f97316'
                  : getStrainColor(strainScore ?? null) === 'yellow'
                  ? '#eab308'
                  : getStrainColor(strainScore ?? null) === 'blue'
                  ? '#3b82f6'
                  : '#9ca3af'
              }
              strokeWidth="12"
              fill="none"
              strokeLinecap="round"
              strokeDasharray={`${(strainPercentage / 100) * 352} 352`}
            />
          </svg>
          {/* Center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span
              className={`text-3xl font-bold ${getStrainTextColor(
                strainScore ?? null
              )}`}
            >
              {strainScore !== null && strainScore !== undefined
                ? Number(strainScore).toFixed(1)
                : '--'}
            </span>
            <span className="text-sm text-gray-500">
              {getStrainLevel(strainScore ?? null)}
            </span>
          </div>
        </div>
      </div>

      {/* Strain metrics */}
      <div className="grid grid-cols-2 gap-4">
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className={`text-xl font-semibold ${getStrainTextColor(avgStrain ?? null)}`}>
            {avgStrain !== null && avgStrain !== undefined
              ? Number(avgStrain).toFixed(1)
              : '--'}
          </div>
          <div className="text-sm text-gray-500">7-Day Avg</div>
        </div>

        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className="text-xl font-semibold text-gray-900">{totalWorkouts}</div>
          <div className="text-sm text-gray-500">Workouts (7d)</div>
        </div>
      </div>
    </div>
  );
}
