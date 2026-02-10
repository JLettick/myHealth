/**
 * Axios HTTP client with authentication interceptors.
 *
 * Automatically handles:
 * - Adding Authorization header to requests
 * - Refreshing expired tokens
 * - Redirecting to login on auth failure
 */

import axios, { AxiosError } from 'axios';
import { tokenStorage } from '../utils/storage';
import { logger } from '../utils/logger';
import type { AuthResponse, ApiError } from '../types/auth';

// API base URL from environment
const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

/**
 * Axios instance configured for API requests.
 */
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Flag to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let refreshSubscribers: {
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}[] = [];

/**
 * Subscribe to token refresh completion.
 * Returns a promise that resolves with the new token or rejects on failure.
 */
function subscribeTokenRefresh(): Promise<string> {
  return new Promise<string>((resolve, reject) => {
    refreshSubscribers.push({ resolve, reject });
  });
}

/**
 * Notify all subscribers that token refresh is complete.
 */
function onTokenRefreshed(token: string): void {
  refreshSubscribers.forEach((subscriber) => subscriber.resolve(token));
  refreshSubscribers = [];
}

/**
 * Reject all subscribers when token refresh fails.
 */
function onTokenRefreshFailed(error: unknown): void {
  refreshSubscribers.forEach((subscriber) => subscriber.reject(error));
  refreshSubscribers = [];
}

/**
 * Request interceptor: Add Authorization header.
 */
apiClient.interceptors.request.use(
  (config) => {
    const token = tokenStorage.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    logger.debug('API Request', {
      method: config.method?.toUpperCase(),
      url: config.url,
    });
    return config;
  },
  (error) => {
    logger.error('Request interceptor error', { error: error.message });
    return Promise.reject(error);
  }
);

/**
 * Response interceptor: Handle 401 errors and token refresh.
 */
apiClient.interceptors.response.use(
  (response) => {
    logger.debug('API Response', {
      status: response.status,
      url: response.config.url,
    });
    return response;
  },
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as typeof error.config & {
      _retry?: boolean;
    };

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = tokenStorage.getRefreshToken();

      if (!refreshToken) {
        // No refresh token, redirect to login
        logger.info('No refresh token, redirecting to login');
        tokenStorage.clearTokens();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Wait for the ongoing refresh to complete
        const token = await subscribeTokenRefresh();
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
        }
        return apiClient(originalRequest);
      }

      isRefreshing = true;

      try {
        logger.info('Attempting token refresh');

        // Call refresh endpoint
        const response = await axios.post<AuthResponse>(
          `${API_URL}/auth/refresh`,
          { refresh_token: refreshToken },
          { headers: { 'Content-Type': 'application/json' } }
        );

        const { session } = response.data;

        // Store new tokens
        tokenStorage.setAccessToken(session.access_token);
        tokenStorage.setRefreshToken(session.refresh_token);

        logger.info('Token refresh successful');

        // Notify subscribers and retry original request
        onTokenRefreshed(session.access_token);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${session.access_token}`;
        }

        return apiClient(originalRequest);
      } catch (refreshError) {
        logger.error('Token refresh failed', {
          error: refreshError instanceof Error ? refreshError.message : 'Unknown error',
        });

        // Reject all pending subscribers before clearing tokens
        onTokenRefreshFailed(refreshError);

        // Refresh failed, clear tokens and redirect to login
        tokenStorage.clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Log other errors
    logger.error('API Error', {
      status: error.response?.status,
      message: error.response?.data?.message || error.message,
      url: error.config?.url,
    });

    return Promise.reject(error);
  }
);

export default apiClient;
