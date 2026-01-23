/**
 * Dashboard page component (protected).
 */

import { useAuth } from '../contexts/AuthContext';

/**
 * Protected dashboard page for authenticated users.
 */
export function DashboardPage(): JSX.Element {
  const { user } = useAuth();

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

      {/* Dashboard cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            &#128170; Activity
          </h3>
          <p className="text-3xl font-bold text-blue-600">--</p>
          <p className="text-sm text-gray-500 mt-1">Steps today</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            &#128151; Heart Rate
          </h3>
          <p className="text-3xl font-bold text-red-500">--</p>
          <p className="text-sm text-gray-500 mt-1">BPM average</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            &#128164; Sleep
          </h3>
          <p className="text-3xl font-bold text-purple-600">--</p>
          <p className="text-sm text-gray-500 mt-1">Hours last night</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            &#128167; Hydration
          </h3>
          <p className="text-3xl font-bold text-cyan-600">--</p>
          <p className="text-sm text-gray-500 mt-1">Glasses today</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            &#127829; Nutrition
          </h3>
          <p className="text-3xl font-bold text-orange-500">--</p>
          <p className="text-sm text-gray-500 mt-1">Calories today</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            &#129504; Mindfulness
          </h3>
          <p className="text-3xl font-bold text-green-600">--</p>
          <p className="text-sm text-gray-500 mt-1">Minutes today</p>
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
