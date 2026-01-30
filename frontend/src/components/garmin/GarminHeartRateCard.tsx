/**
 * Garmin heart rate card.
 *
 * Displays resting heart rate and HRV metrics.
 */

import React from 'react';
import { useGarmin } from '../../contexts/GarminContext';

export function GarminHeartRateCard(): JSX.Element {
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

  const restingHR = dashboardSummary.latest_resting_hr;
  const hrv = dashboardSummary.latest_hrv;
  const avgRestingHR = dashboardSummary.avg_resting_hr_7d;

  // Get color based on resting HR
  const getHRColor = (hr: number | null): string => {
    if (hr === null) return 'text-gray-400';
    if (hr < 60) return 'text-green-600';
    if (hr < 70) return 'text-blue-600';
    if (hr < 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-md">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Heart Rate</h3>

      <div className="flex items-center justify-between mb-6">
        {/* Resting HR */}
        <div className="text-center">
          <p className={`text-4xl font-bold ${getHRColor(restingHR)}`}>
            {restingHR != null ? restingHR : '--'}
          </p>
          <p className="text-sm text-gray-500 mt-1">Resting BPM</p>
        </div>

        {/* HRV */}
        <div className="text-center">
          <p className="text-4xl font-bold text-cyan-600">
            {hrv != null ? Math.round(Number(hrv)) : '--'}
          </p>
          <p className="text-sm text-gray-500 mt-1">HRV (ms)</p>
        </div>
      </div>

      {/* 7-day average */}
      <div className="pt-4 border-t border-gray-100">
        <p className="text-sm text-gray-500">
          7-day avg resting HR:{' '}
          <span className="font-medium text-gray-700">
            {avgRestingHR != null ? `${Math.round(avgRestingHR)} BPM` : '--'}
          </span>
        </p>
      </div>
    </div>
  );
}

export default GarminHeartRateCard;
