/**
 * Garmin daily stats card.
 *
 * Displays steps, calories, active minutes, and body battery.
 */

import React from 'react';
import { useGarmin } from '../../contexts/GarminContext';
import { formatSteps, getBodyBatteryColor } from '../../types/garmin';

export function GarminDailyCard(): JSX.Element {
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

  const steps = dashboardSummary.latest_steps;
  const calories = dashboardSummary.latest_calories;
  const activeMinutes = dashboardSummary.latest_active_minutes;
  const bodyBattery = dashboardSummary.latest_body_battery;
  const avgSteps = dashboardSummary.avg_steps_7d;

  const batteryColorClass = {
    green: 'text-green-600',
    blue: 'text-blue-600',
    yellow: 'text-yellow-600',
    red: 'text-red-600',
    gray: 'text-gray-400',
  }[getBodyBatteryColor(bodyBattery)];

  return (
    <div className="bg-white p-6 rounded-xl shadow-md">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Activity</h3>

      <div className="grid grid-cols-2 gap-4">
        {/* Steps */}
        <div>
          <p className="text-sm text-gray-500">Steps</p>
          <p className="text-2xl font-bold text-blue-600">
            {formatSteps(steps)}
          </p>
        </div>

        {/* Calories */}
        <div>
          <p className="text-sm text-gray-500">Calories</p>
          <p className="text-2xl font-bold text-orange-500">
            {calories != null ? calories.toLocaleString() : '--'}
          </p>
        </div>

        {/* Active Minutes */}
        <div>
          <p className="text-sm text-gray-500">Active Minutes</p>
          <p className="text-2xl font-bold text-green-600">
            {activeMinutes != null ? `${activeMinutes}m` : '--'}
          </p>
        </div>

        {/* Body Battery */}
        <div>
          <p className="text-sm text-gray-500">Body Battery</p>
          <p className={`text-2xl font-bold ${batteryColorClass}`}>
            {bodyBattery != null ? `${bodyBattery}%` : '--'}
          </p>
        </div>
      </div>

      {/* 7-day average */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <p className="text-sm text-gray-500">
          7-day avg steps:{' '}
          <span className="font-medium text-gray-700">
            {avgSteps != null ? formatSteps(Math.round(avgSteps)) : '--'}
          </span>
        </p>
      </div>
    </div>
  );
}

export default GarminDailyCard;
