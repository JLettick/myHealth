/**
 * Dashboard page component (protected).
 *
 * Displays fitness data from the selected source (Whoop or Garmin)
 * with a dropdown selector to switch between sources.
 */

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useWhoop } from '../contexts/WhoopContext';
import { useGarmin } from '../contexts/GarminContext';
import { FitnessSourceSelector } from '../components/fitness';
import type { FitnessSource } from '../components/fitness';
import {
  WhoopConnectionCard,
  WhoopRecoveryCard,
  WhoopSleepCard,
  WhoopStrainCard,
} from '../components/whoop';
import {
  GarminConnectionCard,
  GarminDailyCard,
  GarminHeartRateCard,
  GarminSleepCard,
  GarminActivityCard,
} from '../components/garmin';

const STORAGE_KEY = 'fitness_source';

/**
 * Protected dashboard page for authenticated users.
 */
export function DashboardPage(): JSX.Element {
  const { user, isAuthenticated } = useAuth();
  const {
    isConnected: whoopConnected,
    dashboardSummary: whoopData,
    refresh: refreshWhoop,
  } = useWhoop();
  const {
    isConnected: garminConnected,
    dashboardSummary: garminData,
  } = useGarmin();

  // Load Whoop data on mount
  const hasLoadedRef = useRef(false);
  useEffect(() => {
    if (isAuthenticated && !hasLoadedRef.current) {
      hasLoadedRef.current = true;
      refreshWhoop();
    }
  }, [isAuthenticated]); // eslint-disable-line react-hooks/exhaustive-deps

  // Initialize selected source from localStorage or default to whoop
  // Note: Garmin is currently disabled, so always default to whoop
  const [selectedSource, setSelectedSource] = useState<FitnessSource>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'whoop') {
      return saved;
    }
    // Default to whoop (Garmin disabled - API not public)
    return 'whoop';
  });

  // Persist selection to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, selectedSource);
  }, [selectedSource]);

  /**
   * Render the dashboard for Whoop source.
   */
  const renderWhoopDashboard = () => (
    <>
      {/* Whoop Connection Card */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Whoop Connection
        </h2>
        <div className="max-w-md">
          <WhoopConnectionCard />
        </div>
      </div>

      {/* Whoop Metrics - Only show if connected */}
      {whoopConnected && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Whoop Metrics
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <WhoopRecoveryCard />
            <WhoopStrainCard />
            <WhoopSleepCard />
          </div>
        </div>
      )}

      {/* Whoop Health Overview - Only show if connected */}
      {whoopConnected && whoopData && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Health Overview
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-xl shadow-md">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Activity
              </h3>
              <p className="text-3xl font-bold text-blue-600">
                {whoopData.total_workouts_7d ?? '--'}
              </p>
              <p className="text-sm text-gray-500 mt-1">Workouts this week</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-md">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Heart Rate
              </h3>
              <p className="text-3xl font-bold text-red-500">
                {whoopData.latest_resting_hr != null
                  ? Math.round(whoopData.latest_resting_hr)
                  : '--'}
              </p>
              <p className="text-sm text-gray-500 mt-1">Resting BPM</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-md">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Sleep
              </h3>
              <p className="text-3xl font-bold text-purple-600">
                {whoopData.latest_sleep_hours != null
                  ? `${Number(whoopData.latest_sleep_hours).toFixed(1)}h`
                  : '--'}
              </p>
              <p className="text-sm text-gray-500 mt-1">Hours last night</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-md">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">HRV</h3>
              <p className="text-3xl font-bold text-cyan-600">
                {whoopData.latest_hrv != null
                  ? Math.round(whoopData.latest_hrv)
                  : '--'}
              </p>
              <p className="text-sm text-gray-500 mt-1">Milliseconds</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-md">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Recovery
              </h3>
              <p className="text-3xl font-bold text-green-600">
                {whoopData.latest_recovery_score != null
                  ? `${Math.round(whoopData.latest_recovery_score)}%`
                  : '--'}
              </p>
              <p className="text-sm text-gray-500 mt-1">Today's score</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-md">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Strain
              </h3>
              <p className="text-3xl font-bold text-orange-500">
                {whoopData.latest_strain_score != null
                  ? Number(whoopData.latest_strain_score).toFixed(1)
                  : '--'}
              </p>
              <p className="text-sm text-gray-500 mt-1">Day strain (0-21)</p>
            </div>
          </div>
        </div>
      )}
    </>
  );

  /**
   * Render the dashboard for Garmin source.
   */
  const renderGarminDashboard = () => (
    <>
      {/* Garmin Connection Card */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Garmin Connection
        </h2>
        <div className="max-w-md">
          <GarminConnectionCard />
        </div>
      </div>

      {/* Garmin Metrics - Only show if connected */}
      {garminConnected && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Garmin Metrics
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <GarminDailyCard />
            <GarminHeartRateCard />
            <GarminSleepCard />
            <GarminActivityCard />
          </div>
        </div>
      )}
    </>
  );

  return (
    <div>
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome{user?.full_name ? `, ${user.full_name}` : ''}!
        </h1>
        <p className="text-gray-600 mt-2">
          Here's an overview of your health dashboard.
        </p>
      </div>

      {/* Source Selector */}
      <FitnessSourceSelector
        selectedSource={selectedSource}
        onSourceChange={setSelectedSource}
        whoopConnected={whoopConnected}
        garminConnected={garminConnected}
      />

      {/* Source-specific Dashboard */}
      {selectedSource === 'whoop' ? renderWhoopDashboard() : renderGarminDashboard()}
    </div>
  );
}
