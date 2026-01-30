/**
 * Garmin context for state management.
 *
 * Provides Garmin connection status, dashboard data, and actions
 * to connect, disconnect, and sync data.
 */

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from 'react';

import { useAuth } from './AuthContext';
import type {
  GarminConnectionStatus,
  GarminDashboardSummary,
  GarminSyncResponse,
} from '../types/garmin';
import {
  connectGarmin as apiConnect,
  disconnectGarmin as apiDisconnect,
  getGarminStatus,
  getGarminDashboard,
  syncGarmin as apiSync,
} from '../api/garmin';

interface GarminContextValue {
  /** Current connection status */
  connectionStatus: GarminConnectionStatus | null;
  /** Whether user is connected to Garmin */
  isConnected: boolean;
  /** Dashboard summary data */
  dashboardSummary: GarminDashboardSummary | null;
  /** Loading state for initial data fetch */
  isLoading: boolean;
  /** Syncing state for sync operation */
  isSyncing: boolean;
  /** Error message if any */
  error: string | null;
  /** Initiate Garmin OAuth connection */
  connect: () => Promise<void>;
  /** Disconnect Garmin account */
  disconnect: () => Promise<void>;
  /** Sync Garmin data */
  sync: (startDate?: Date, endDate?: Date) => Promise<GarminSyncResponse | null>;
  /** Refresh all data */
  refresh: () => Promise<void>;
  /** Clear error state */
  clearError: () => void;
}

const GarminContext = createContext<GarminContextValue | undefined>(undefined);

interface GarminProviderProps {
  children: ReactNode;
}

export function GarminProvider({ children }: GarminProviderProps): JSX.Element {
  const { isAuthenticated } = useAuth();

  const [connectionStatus, setConnectionStatus] = useState<GarminConnectionStatus | null>(null);
  const [dashboardSummary, setDashboardSummary] = useState<GarminDashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isConnected = connectionStatus?.is_connected ?? false;

  /**
   * Load connection status and dashboard data.
   */
  const loadData = useCallback(async () => {
    if (!isAuthenticated) return;

    setIsLoading(true);
    try {
      const [status, dashboard] = await Promise.all([
        getGarminStatus(),
        getGarminDashboard(),
      ]);
      setConnectionStatus(status);
      setDashboardSummary(dashboard);
    } catch (err) {
      console.error('Failed to load Garmin data:', err);
      // Don't set error for initial load failures
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  /**
   * Handle OAuth callback via URL parameters.
   */
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const connected = params.get('garmin_connected');
    const errorParam = params.get('garmin_error');

    if (connected === 'true') {
      // OAuth succeeded - refresh data
      loadData();
      // Clean up URL
      window.history.replaceState({}, '', window.location.pathname);
    } else if (errorParam) {
      // OAuth failed - show error
      setError(decodeURIComponent(errorParam));
      // Clean up URL
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [loadData]);

  /**
   * Load data on mount and when auth state changes.
   */
  useEffect(() => {
    loadData();
  }, [loadData]);

  /**
   * Initiate Garmin OAuth connection.
   */
  const connect = useCallback(async () => {
    try {
      setError(null);
      await apiConnect();
      // Note: This will redirect to Garmin, so the page will reload
    } catch (err) {
      console.error('Failed to initiate Garmin connection:', err);
      setError('Failed to initiate Garmin connection');
    }
  }, []);

  /**
   * Disconnect Garmin account.
   */
  const disconnect = useCallback(async () => {
    try {
      setError(null);
      await apiDisconnect();
      // Update local state immediately (optimistic update)
      setConnectionStatus((prev) =>
        prev ? { ...prev, is_connected: false } : null
      );
      setDashboardSummary((prev) =>
        prev ? { ...prev, is_connected: false } : null
      );
    } catch (err) {
      console.error('Failed to disconnect Garmin:', err);
      setError('Failed to disconnect Garmin');
    }
  }, []);

  /**
   * Sync Garmin data.
   */
  const sync = useCallback(
    async (startDate?: Date, endDate?: Date) => {
      if (!isConnected) return null;

      setIsSyncing(true);
      setError(null);
      try {
        const result = await apiSync(startDate, endDate);
        // Refresh data after sync
        await loadData();
        return result;
      } catch (err) {
        console.error('Failed to sync Garmin data:', err);
        setError('Failed to sync Garmin data');
        return null;
      } finally {
        setIsSyncing(false);
      }
    },
    [isConnected, loadData]
  );

  /**
   * Refresh all data.
   */
  const refresh = useCallback(async () => {
    await loadData();
  }, [loadData]);

  /**
   * Clear error state.
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const value: GarminContextValue = {
    connectionStatus,
    isConnected,
    dashboardSummary,
    isLoading,
    isSyncing,
    error,
    connect,
    disconnect,
    sync,
    refresh,
    clearError,
  };

  return (
    <GarminContext.Provider value={value}>{children}</GarminContext.Provider>
  );
}

/**
 * Hook to use Garmin context.
 */
export function useGarmin(): GarminContextValue {
  const context = useContext(GarminContext);
  if (!context) {
    throw new Error('useGarmin must be used within a GarminProvider');
  }
  return context;
}
