/**
 * Authentication-related TypeScript types.
 *
 * These types mirror the backend Pydantic schemas for type safety
 * across the full stack.
 */

/**
 * User data returned from the API.
 */
export interface User {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  created_at: string;
  email_confirmed_at: string | null;
}

/**
 * Session token data.
 */
export interface Session {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  expires_at: string;
}

/**
 * Authentication response from login/signup.
 */
export interface AuthResponse {
  user: User;
  session: Session;
  message: string;
}

/**
 * Generic message response.
 */
export interface MessageResponse {
  message: string;
  success: boolean;
}

/**
 * Signup request data.
 */
export interface SignupData {
  email: string;
  password: string;
  full_name?: string;
}

/**
 * Login request data.
 */
export interface LoginData {
  email: string;
  password: string;
}

/**
 * API error response.
 */
export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, unknown>;
  request_id?: string;
}

/**
 * Authentication state for the context.
 */
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

/**
 * Authentication context type with methods.
 */
export interface AuthContextType extends AuthState {
  login: (data: LoginData) => Promise<void>;
  signup: (data: SignupData) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}
