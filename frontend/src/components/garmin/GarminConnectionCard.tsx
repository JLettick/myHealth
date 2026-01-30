/**
 * Garmin connection status and control card.
 *
 * Displays connection status and provides buttons to connect,
 * disconnect, and sync Garmin data.
 */

import React from 'react';
import { useGarmin } from '../../contexts/GarminContext';
import { LoadingSpinner } from '../common/LoadingSpinner';

export function GarminConnectionCard(): JSX.Element {
  const {
    connectionStatus,
    isConnected,
    isSyncing,
    error,
    connect,
    disconnect,
    sync,
    clearError,
  } = useGarmin();

  const handleSync = async () => {
    await sync();
  };

  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString();
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-md">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Garmin Connect</h3>
        <div className="flex items-center">
          <span
            className={`w-3 h-3 rounded-full mr-2 ${
              isConnected ? 'bg-green-500' : 'bg-gray-300'
            }`}
          />
          <span className="text-sm text-gray-600">
            {isConnected ? 'Connected' : 'Not Connected'}
          </span>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center justify-between">
            <p className="text-sm text-red-700">{error}</p>
            <button
              onClick={clearError}
              className="text-red-500 hover:text-red-700"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      )}

      {isConnected ? (
        <>
          <div className="space-y-2 mb-4 text-sm text-gray-600">
            <p>
              <span className="font-medium">User ID:</span>{' '}
              {connectionStatus?.garmin_user_id || 'N/A'}
            </p>
            <p>
              <span className="font-medium">Connected:</span>{' '}
              {formatDate(connectionStatus?.connected_at || null)}
            </p>
            <p>
              <span className="font-medium">Last Sync:</span>{' '}
              {formatDate(connectionStatus?.last_sync_at || null)}
            </p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleSync}
              disabled={isSyncing}
              className="flex-1 flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSyncing ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Syncing...
                </>
              ) : (
                'Sync Data'
              )}
            </button>
            <button
              onClick={disconnect}
              className="px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
            >
              Disconnect
            </button>
          </div>
        </>
      ) : (
        <button
          onClick={connect}
          className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          Connect Garmin
        </button>
      )}
    </div>
  );
}

export default GarminConnectionCard;
