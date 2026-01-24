/**
 * Whoop Context for managing Whoop connection and data state.
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import type {
  WhoopConnectionStatus,
  WhoopDashboardSummary,
  WhoopSyncResponse,
} from '../types/whoop';
import {
  getWhoopStatus,
  getWhoopDashboard,
  syncWhoopData,
  connectWhoop,
  disconnectWhoop,
} from '../api/whoop';
import { useAuth } from './AuthContext';
import { logger } from '../utils/logger';

interface WhoopContextValue {
  // Connection state
  connectionStatus: WhoopConnectionStatus | null;
  isConnected: boolean;

  // Dashboard data
  dashboardSummary: WhoopDashboardSummary | null;

  // Loading states
  isLoading: boolean;
  isSyncing: boolean;

  // Error state
  error: string | null;

  // Actions
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  sync: (startDate?: Date, endDate?: Date) => Promise<WhoopSyncResponse | null>;
  refresh: () => Promise<void>;
  clearError: () => void;
}

const WhoopContext = createContext<WhoopContextValue | null>(null);

interface WhoopProviderProps {
  children: React.ReactNode;
}

export function WhoopProvider({ children }: WhoopProviderProps) {
  const { isAuthenticated } = useAuth();

  // State
  const [connectionStatus, setConnectionStatus] = useState<WhoopConnectionStatus | null>(null);
  const [dashboardSummary, setDashboardSummary] = useState<WhoopDashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Derived state
  const isConnected = connectionStatus?.is_connected ?? false;

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Fetch connection status and dashboard data
  const refresh = useCallback(async () => {
    if (!isAuthenticated) {
      setConnectionStatus(null);
      setDashboardSummary(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      console.log('[WhoopContext] Starting refresh...');
      logger.debug('Refreshing Whoop data');

      // Fetch status and dashboard in parallel
      const [status, dashboard] = await Promise.all([
        getWhoopStatus().catch(err => {
          console.error('[WhoopContext] getWhoopStatus failed:', err);
          throw err;
        }),
        getWhoopDashboard().catch(err => {
          console.error('[WhoopContext] getWhoopDashboard failed:', err);
          throw err;
        }),
      ]);

      console.log('[WhoopContext] Status:', status);
      console.log('[WhoopContext] Dashboard:', dashboard);

      setConnectionStatus(status);
      setDashboardSummary(dashboard);

      logger.info('Whoop data refreshed', { isConnected: status.is_connected });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load Whoop data';
      console.error('[WhoopContext] Refresh failed:', err);
      logger.error('Failed to refresh Whoop data', { error: message });
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  // Connect Whoop account (redirects to OAuth)
  const connect = useCallback(async () => {
    setError(null);
    try {
      logger.info('Initiating Whoop connection');
      await connectWhoop();
      // Page will redirect, no need to update state
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to connect Whoop';
      logger.error('Failed to initiate Whoop connection', { error: message });
      setError(message);
    }
  }, []);

  // Disconnect Whoop account
  const disconnect = useCallback(async () => {
    setError(null);
    try {
      logger.info('Disconnecting Whoop');
      const result = await disconnectWhoop();

      if (result.success) {
        // Update local state
        setConnectionStatus((prev) =>
          prev ? { ...prev, is_connected: false } : null
        );
        setDashboardSummary((prev) =>
          prev ? { ...prev, is_connected: false } : null
        );
        logger.info('Whoop disconnected successfully');
      } else {
        setError(result.message);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to disconnect Whoop';
      logger.error('Failed to disconnect Whoop', { error: message });
      setError(message);
    }
  }, []);

  // Sync Whoop data
  const sync = useCallback(
    async (startDate?: Date, endDate?: Date): Promise<WhoopSyncResponse | null> => {
      if (!isConnected) {
        setError('Whoop is not connected');
        return null;
      }

      setIsSyncing(true);
      setError(null);

      try {
        logger.info('Syncing Whoop data', { startDate, endDate });
        const result = await syncWhoopData(startDate, endDate);

        if (result.success) {
          // Refresh dashboard data after sync
          await refresh();
          logger.info('Whoop sync completed', {
            cycles: result.cycles_synced,
            recovery: result.recovery_synced,
            sleep: result.sleep_synced,
            workouts: result.workouts_synced,
          });
        }

        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to sync Whoop data';
        logger.error('Whoop sync failed', { error: message });
        setError(message);
        return null;
      } finally {
        setIsSyncing(false);
      }
    },
    [isConnected, refresh]
  );

  // Load data on mount and when auth changes
  useEffect(() => {
    if (isAuthenticated) {
      refresh();
    } else {
      setConnectionStatus(null);
      setDashboardSummary(null);
      setError(null);
    }
  }, [isAuthenticated, refresh]);

  // Check for OAuth callback result in URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const whoopConnected = params.get('whoop_connected');
    const whoopError = params.get('whoop_error');

    console.log('[WhoopContext] URL params check:', {
      whoopConnected,
      whoopError,
      fullSearch: window.location.search
    });

    if (whoopConnected === 'true') {
      console.log('[WhoopContext] Success! Refreshing data...');
      logger.info('Whoop connected via OAuth callback');
      // Clear URL params and refresh
      window.history.replaceState({}, '', window.location.pathname);
      refresh();
    } else if (whoopError) {
      console.error('[WhoopContext] OAuth error:', whoopError);
      logger.error('Whoop OAuth error', { error: whoopError });
      setError(`Whoop connection failed: ${whoopError}`);
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [refresh]);

  const value: WhoopContextValue = {
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

  return <WhoopContext.Provider value={value}>{children}</WhoopContext.Provider>;
}

/**
 * Hook to use Whoop context.
 */
export function useWhoop(): WhoopContextValue {
  const context = useContext(WhoopContext);
  if (!context) {
    throw new Error('useWhoop must be used within a WhoopProvider');
  }
  return context;
}
