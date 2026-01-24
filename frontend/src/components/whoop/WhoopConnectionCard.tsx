/**
 * Component for managing Whoop connection status.
 */

import React from 'react';
import { useWhoop } from '../../contexts/WhoopContext';
import { Button } from '../common/Button';
import { LoadingSpinner } from '../common/LoadingSpinner';

export function WhoopConnectionCard() {
  const {
    connectionStatus,
    isConnected,
    isLoading,
    isSyncing,
    error,
    connect,
    disconnect,
    sync,
    clearError,
  } = useWhoop();

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center py-4">
          <LoadingSpinner size="md" />
          <span className="ml-2 text-gray-600">Loading Whoop status...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <div className="w-10 h-10 bg-black rounded-full flex items-center justify-center mr-3">
            <span className="text-white font-bold text-sm">W</span>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Whoop</h3>
            <p className="text-sm text-gray-500">
              {isConnected ? 'Connected' : 'Not connected'}
            </p>
          </div>
        </div>
        <div
          className={`w-3 h-3 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-gray-300'
          }`}
        />
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex justify-between items-start">
            <p className="text-sm text-red-700">{error}</p>
            <button
              onClick={clearError}
              className="text-red-500 hover:text-red-700 ml-2"
            >
              &times;
            </button>
          </div>
        </div>
      )}

      {isConnected && connectionStatus && (
        <div className="mb-4 space-y-2 text-sm text-gray-600">
          <div className="flex justify-between">
            <span>Whoop User ID:</span>
            <span className="font-mono">{connectionStatus.whoop_user_id}</span>
          </div>
          <div className="flex justify-between">
            <span>Connected:</span>
            <span>{formatDate(connectionStatus.connected_at)}</span>
          </div>
          <div className="flex justify-between">
            <span>Last Sync:</span>
            <span>{formatDate(connectionStatus.last_sync_at)}</span>
          </div>
        </div>
      )}

      <div className="flex gap-2">
        {isConnected ? (
          <>
            <Button
              onClick={() => sync()}
              disabled={isSyncing}
              variant="primary"
              className="flex-1"
            >
              {isSyncing ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Syncing...
                </>
              ) : (
                'Sync Data'
              )}
            </Button>
            <Button onClick={disconnect} variant="secondary">
              Disconnect
            </Button>
          </>
        ) : (
          <Button onClick={connect} variant="primary" className="w-full">
            Connect Whoop
          </Button>
        )}
      </div>
    </div>
  );
}
