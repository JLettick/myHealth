/**
 * Authentication API functions.
 *
 * Provides typed functions for all authentication-related API calls.
 */

import apiClient from './client';
import type {
  AuthResponse,
  LoginData,
  MessageResponse,
  SignupData,
  User,
} from '../types/auth';
import { logger } from '../utils/logger';

/**
 * Register a new user account.
 */
export async function signup(data: SignupData): Promise<AuthResponse> {
  logger.info('Signing up user', { email: data.email });
  const response = await apiClient.post<AuthResponse>('/auth/signup', data);
  return response.data;
}

/**
 * Authenticate with email and password.
 */
export async function login(data: LoginData): Promise<AuthResponse> {
  logger.info('Logging in user', { email: data.email });
  const response = await apiClient.post<AuthResponse>('/auth/login', data);
  return response.data;
}

/**
 * Sign out and invalidate session.
 */
export async function logout(): Promise<MessageResponse> {
  logger.info('Logging out user');
  const response = await apiClient.post<MessageResponse>('/auth/logout');
  return response.data;
}

/**
 * Refresh access token using refresh token.
 */
export async function refreshToken(refreshToken: string): Promise<AuthResponse> {
  logger.info('Refreshing token');
  const response = await apiClient.post<AuthResponse>('/auth/refresh', {
    refresh_token: refreshToken,
  });
  return response.data;
}

/**
 * Get current authenticated user.
 */
export async function getCurrentUser(): Promise<User> {
  logger.debug('Getting current user');
  const response = await apiClient.get<User>('/auth/me');
  return response.data;
}
