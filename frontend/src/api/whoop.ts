/**
 * Whoop API functions for the frontend.
 */

import apiClient from './client';
import type {
  WhoopConnectResponse,
  WhoopConnectionStatus,
  WhoopDashboardSummary,
  WhoopDisconnectResponse,
  WhoopRecoveryListResponse,
  WhoopSleepListResponse,
  WhoopSyncResponse,
  WhoopWorkoutListResponse,
} from '../types/whoop';
import { logger } from '../utils/logger';

/**
 * Get the OAuth authorization URL for connecting Whoop.
 * Redirects user to Whoop to authorize the connection.
 */
export async function getWhoopConnectUrl(): Promise<WhoopConnectResponse> {
  logger.info('Getting Whoop connect URL');
  const response = await apiClient.get<WhoopConnectResponse>('/whoop/connect');
  return response.data;
}

/**
 * Initiate Whoop connection by redirecting to authorization URL.
 */
export async function connectWhoop(): Promise<void> {
  const { authorization_url } = await getWhoopConnectUrl();
  logger.info('Redirecting to Whoop authorization');
  window.location.href = authorization_url;
}

/**
 * Disconnect the user's Whoop account.
 * Historical data is retained.
 */
export async function disconnectWhoop(): Promise<WhoopDisconnectResponse> {
  logger.info('Disconnecting Whoop');
  const response = await apiClient.delete<WhoopDisconnectResponse>('/whoop/disconnect');
  return response.data;
}

/**
 * Get the current Whoop connection status.
 */
export async function getWhoopStatus(): Promise<WhoopConnectionStatus> {
  logger.debug('Getting Whoop connection status');
  const response = await apiClient.get<WhoopConnectionStatus>('/whoop/status');
  return response.data;
}

/**
 * Trigger a sync of Whoop data.
 */
export async function syncWhoopData(
  startDate?: Date,
  endDate?: Date
): Promise<WhoopSyncResponse> {
  logger.info('Syncing Whoop data');

  const params = new URLSearchParams();
  if (startDate) {
    params.append('start_date', startDate.toISOString());
  }
  if (endDate) {
    params.append('end_date', endDate.toISOString());
  }

  const url = params.toString() ? `/whoop/sync?${params}` : '/whoop/sync';
  const response = await apiClient.post<WhoopSyncResponse>(url);
  return response.data;
}

/**
 * Get dashboard summary data.
 */
export async function getWhoopDashboard(): Promise<WhoopDashboardSummary> {
  logger.debug('Getting Whoop dashboard data');
  const response = await apiClient.get<WhoopDashboardSummary>('/whoop/dashboard');
  return response.data;
}

/**
 * Get paginated sleep records.
 */
export async function getWhoopSleep(
  page: number = 1,
  pageSize: number = 10,
  includeNaps: boolean = false
): Promise<WhoopSleepListResponse> {
  logger.debug('Getting Whoop sleep records', { page, pageSize, includeNaps });

  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
    include_naps: includeNaps.toString(),
  });

  const response = await apiClient.get<WhoopSleepListResponse>(`/whoop/sleep?${params}`);
  return response.data;
}

/**
 * Get paginated workout records.
 */
export async function getWhoopWorkouts(
  page: number = 1,
  pageSize: number = 10
): Promise<WhoopWorkoutListResponse> {
  logger.debug('Getting Whoop workout records', { page, pageSize });

  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });

  const response = await apiClient.get<WhoopWorkoutListResponse>(`/whoop/workouts?${params}`);
  return response.data;
}

/**
 * Get paginated recovery records.
 */
export async function getWhoopRecovery(
  page: number = 1,
  pageSize: number = 10
): Promise<WhoopRecoveryListResponse> {
  logger.debug('Getting Whoop recovery records', { page, pageSize });

  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });

  const response = await apiClient.get<WhoopRecoveryListResponse>(`/whoop/recovery?${params}`);
  return response.data;
}
