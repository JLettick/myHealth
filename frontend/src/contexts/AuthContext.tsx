/**
 * Authentication Context Provider.
 *
 * Manages global authentication state and provides auth methods
 * to all components in the application.
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { AxiosError } from 'axios';
import * as authApi from '../api/auth';
import { tokenStorage } from '../utils/storage';
import { logger } from '../utils/logger';
import type {
  AuthContextType,
  AuthState,
  LoginData,
  SignupData,
  User,
  ApiError,
} from '../types/auth';

/**
 * Initial auth state.
 */
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

/**
 * Auth context.
 */
const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Auth context provider props.
 */
interface AuthProviderProps {
  children: React.ReactNode;
}

/**
 * Auth context provider component.
 */
export function AuthProvider({ children }: AuthProviderProps): JSX.Element {
  const [state, setState] = useState<AuthState>(initialState);

  /**
   * Set user and update state.
   */
  const setUser = useCallback((user: User | null) => {
    setState((prev) => ({
      ...prev,
      user,
      isAuthenticated: !!user,
      isLoading: false,
      error: null,
    }));
  }, []);

  /**
   * Set error state.
   */
  const setError = useCallback((error: string) => {
    setState((prev) => ({
      ...prev,
      error,
      isLoading: false,
    }));
  }, []);

  /**
   * Clear error state.
   */
  const clearError = useCallback(() => {
    setState((prev) => ({
      ...prev,
      error: null,
    }));
  }, []);

  /**
   * Extract error message from API error.
   */
  const getErrorMessage = (error: unknown): string => {
    if (error instanceof AxiosError) {
      const apiError = error.response?.data as ApiError | undefined;
      return apiError?.message || error.message || 'An error occurred';
    }
    if (error instanceof Error) {
      return error.message;
    }
    return 'An unexpected error occurred';
  };

  /**
   * Login handler.
   */
  const login = useCallback(
    async (data: LoginData): Promise<void> => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        const response = await authApi.login(data);

        // Store tokens
        tokenStorage.setAccessToken(response.session.access_token);
        tokenStorage.setRefreshToken(response.session.refresh_token);

        // Update state
        setUser(response.user);

        logger.info('Login successful', { userId: response.user.id });
      } catch (error) {
        const message = getErrorMessage(error);
        logger.error('Login failed', { error: message });
        setError(message);
        throw error;
      }
    },
    [setUser, setError]
  );

  /**
   * Signup handler.
   */
  const signup = useCallback(
    async (data: SignupData): Promise<void> => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        const response = await authApi.signup(data);

        // Check if email confirmation is required
        if (!response.session.access_token) {
          setState((prev) => ({
            ...prev,
            isLoading: false,
            error: null,
          }));
          logger.info('Signup successful, email confirmation required');
          return;
        }

        // Store tokens
        tokenStorage.setAccessToken(response.session.access_token);
        tokenStorage.setRefreshToken(response.session.refresh_token);

        // Update state
        setUser(response.user);

        logger.info('Signup successful', { userId: response.user.id });
      } catch (error) {
        const message = getErrorMessage(error);
        logger.error('Signup failed', { error: message });
        setError(message);
        throw error;
      }
    },
    [setUser, setError]
  );

  /**
   * Logout handler.
   */
  const logout = useCallback(async (): Promise<void> => {
    try {
      await authApi.logout();
    } catch (error) {
      // Log but don't throw - we still want to clear local state
      logger.warn('Logout API call failed', {
        error: getErrorMessage(error),
      });
    } finally {
      // Always clear tokens and state
      tokenStorage.clearTokens();
      setUser(null);
      logger.info('User logged out');
    }
  }, [setUser]);

  /**
   * Check authentication status on mount.
   */
  useEffect(() => {
    const checkAuth = async () => {
      const accessToken = tokenStorage.getAccessToken();
      const refreshToken = tokenStorage.getRefreshToken();

      if (!accessToken && !refreshToken) {
        setState((prev) => ({ ...prev, isLoading: false }));
        return;
      }

      try {
        // Try to get current user
        const user = await authApi.getCurrentUser();
        setUser(user);
        logger.info('Auth check successful', { userId: user.id });
      } catch (error) {
        logger.warn('Auth check failed, clearing tokens');
        tokenStorage.clearTokens();
        setState((prev) => ({ ...prev, isLoading: false }));
      }
    };

    checkAuth();
  }, [setUser]);

  /**
   * Context value.
   */
  const value = useMemo<AuthContextType>(
    () => ({
      ...state,
      login,
      signup,
      logout,
      clearError,
    }),
    [state, login, signup, logout, clearError]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access auth context.
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
