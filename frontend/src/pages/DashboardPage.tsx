/**
 * Dashboard page component (protected).
 */

import { useAuth } from '../contexts/AuthContext';
import { useWhoop } from '../contexts/WhoopContext';
import {
  WhoopConnectionCard,
  WhoopRecoveryCard,
  WhoopSleepCard,
  WhoopStrainCard,
} from '../components/whoop';

/**
 * Protected dashboard page for authenticated users.
 */
export function DashboardPage(): JSX.Element {
  const { user } = useAuth();
  const { isConnected, dashboardSummary } = useWhoop();

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome{user?.full_name ? `, ${user.full_name}` : ''}!
        </h1>
        <p className="text-gray-600 mt-2">
          Here's an overview of your health dashboard.
        </p>
      </div>

      {/* Data Sources Section */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Connected Services
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <WhoopConnectionCard />
        </div>
      </div>

      {/* Whoop Data Section - Only show if connected */}
      {isConnected && (
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

      {/* General Health Cards - Placeholders for future integrations */}
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
              {isConnected && dashboardSummary?.total_workouts_7d !== undefined
                ? dashboardSummary.total_workouts_7d
                : '--'}
            </p>
            <p className="text-sm text-gray-500 mt-1">Workouts this week</p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Heart Rate
            </h3>
            <p className="text-3xl font-bold text-red-500">
              {isConnected && dashboardSummary?.latest_resting_hr != null
                ? Math.round(dashboardSummary.latest_resting_hr)
                : '--'}
            </p>
            <p className="text-sm text-gray-500 mt-1">Resting BPM</p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Sleep
            </h3>
            <p className="text-3xl font-bold text-purple-600">
              {isConnected && dashboardSummary?.latest_sleep_hours != null
                ? `${Number(dashboardSummary.latest_sleep_hours).toFixed(1)}h`
                : '--'}
            </p>
            <p className="text-sm text-gray-500 mt-1">Hours last night</p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              HRV
            </h3>
            <p className="text-3xl font-bold text-cyan-600">
              {isConnected && dashboardSummary?.latest_hrv != null
                ? Math.round(dashboardSummary.latest_hrv)
                : '--'}
            </p>
            <p className="text-sm text-gray-500 mt-1">Milliseconds</p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Recovery
            </h3>
            <p className="text-3xl font-bold text-green-600">
              {isConnected && dashboardSummary?.latest_recovery_score != null
                ? `${Math.round(dashboardSummary.latest_recovery_score)}%`
                : '--'}
            </p>
            <p className="text-sm text-gray-500 mt-1">Today's score</p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Strain
            </h3>
            <p className="text-3xl font-bold text-orange-500">
              {isConnected && dashboardSummary?.latest_strain_score != null
                ? Number(dashboardSummary.latest_strain_score).toFixed(1)
                : '--'}
            </p>
            <p className="text-sm text-gray-500 mt-1">Day strain (0-21)</p>
          </div>
        </div>
      </div>

      {/* Account info */}
      <div className="mt-8 bg-white p-6 rounded-xl shadow-md">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Account Information
        </h3>
        <div className="space-y-2">
          <p className="text-gray-600">
            <span className="font-medium">Email:</span> {user?.email}
          </p>
          {user?.full_name && (
            <p className="text-gray-600">
              <span className="font-medium">Name:</span> {user.full_name}
            </p>
          )}
          <p className="text-gray-600">
            <span className="font-medium">Member since:</span>{' '}
            {user?.created_at
              ? new Date(user.created_at).toLocaleDateString()
              : 'N/A'}
          </p>
        </div>
      </div>
    </div>
  );
}
