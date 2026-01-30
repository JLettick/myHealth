/**
 * Garmin API client functions.
 */

import apiClient from './client';
import type {
  GarminConnectResponse,
  GarminConnectionStatus,
  GarminDisconnectResponse,
  GarminSyncResponse,
  GarminDashboardSummary,
  GarminActivityList,
  GarminSleepList,
  GarminHeartRateList,
  GarminDailyStatsList,
} from '../types/garmin';

/**
 * Get Garmin OAuth authorization URL.
 */
export async function getGarminConnectUrl(): Promise<GarminConnectResponse> {
  const response = await apiClient.get<GarminConnectResponse>('/garmin/connect');
  return response.data;
}

/**
 * Initiate Garmin OAuth flow by redirecting to authorization URL.
 */
export async function connectGarmin(): Promise<void> {
  const { authorization_url } = await getGarminConnectUrl();
  window.location.href = authorization_url;
}

/**
 * Disconnect Garmin account.
 */
export async function disconnectGarmin(): Promise<GarminDisconnectResponse> {
  const response = await apiClient.delete<GarminDisconnectResponse>('/garmin/disconnect');
  return response.data;
}

/**
 * Get Garmin connection status.
 */
export async function getGarminStatus(): Promise<GarminConnectionStatus> {
  const response = await apiClient.get<GarminConnectionStatus>('/garmin/status');
  return response.data;
}

/**
 * Sync Garmin data.
 */
export async function syncGarmin(
  startDate?: Date,
  endDate?: Date
): Promise<GarminSyncResponse> {
  const response = await apiClient.post<GarminSyncResponse>('/garmin/sync', {
    start_date: startDate?.toISOString().split('T')[0],
    end_date: endDate?.toISOString().split('T')[0],
  });
  return response.data;
}

/**
 * Get Garmin dashboard summary.
 */
export async function getGarminDashboard(): Promise<GarminDashboardSummary> {
  const response = await apiClient.get<GarminDashboardSummary>('/garmin/dashboard');
  return response.data;
}

/**
 * Get Garmin activities.
 */
export async function getGarminActivities(
  page = 1,
  pageSize = 10
): Promise<GarminActivityList> {
  const response = await apiClient.get<GarminActivityList>('/garmin/activities', {
    params: { page, page_size: pageSize },
  });
  return response.data;
}

/**
 * Get Garmin sleep records.
 */
export async function getGarminSleep(
  page = 1,
  pageSize = 10
): Promise<GarminSleepList> {
  const response = await apiClient.get<GarminSleepList>('/garmin/sleep', {
    params: { page, page_size: pageSize },
  });
  return response.data;
}

/**
 * Get Garmin heart rate records.
 */
export async function getGarminHeartRate(
  page = 1,
  pageSize = 10
): Promise<GarminHeartRateList> {
  const response = await apiClient.get<GarminHeartRateList>('/garmin/heart-rate', {
    params: { page, page_size: pageSize },
  });
  return response.data;
}

/**
 * Get Garmin daily stats.
 */
export async function getGarminDailyStats(
  page = 1,
  pageSize = 10
): Promise<GarminDailyStatsList> {
  const response = await apiClient.get<GarminDailyStatsList>('/garmin/daily', {
    params: { page, page_size: pageSize },
  });
  return response.data;
}
