/**
 * Token storage utilities.
 *
 * Provides secure storage and retrieval of authentication tokens.
 * Uses sessionStorage for access tokens and localStorage for refresh tokens.
 */

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

/**
 * Token storage manager.
 *
 * Handles token storage with a combination of memory and browser storage
 * for better security.
 */
class TokenStorage {
  private accessToken: string | null = null;

  /**
   * Set the access token.
   * Stored in memory and sessionStorage for persistence across page refreshes.
   */
  setAccessToken(token: string): void {
    this.accessToken = token;
    try {
      sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
    } catch (e) {
      console.warn('Failed to store access token in sessionStorage:', e);
    }
  }

  /**
   * Get the access token.
   * First checks memory, then falls back to sessionStorage.
   */
  getAccessToken(): string | null {
    if (this.accessToken) {
      return this.accessToken;
    }
    try {
      const token = sessionStorage.getItem(ACCESS_TOKEN_KEY);
      if (token) {
        this.accessToken = token;
      }
      return token;
    } catch (e) {
      console.warn('Failed to get access token from sessionStorage:', e);
      return null;
    }
  }

  /**
   * Set the refresh token.
   * Stored in localStorage for persistence across browser sessions.
   */
  setRefreshToken(token: string): void {
    try {
      localStorage.setItem(REFRESH_TOKEN_KEY, token);
    } catch (e) {
      console.warn('Failed to store refresh token in localStorage:', e);
    }
  }

  /**
   * Get the refresh token.
   */
  getRefreshToken(): string | null {
    try {
      return localStorage.getItem(REFRESH_TOKEN_KEY);
    } catch (e) {
      console.warn('Failed to get refresh token from localStorage:', e);
      return null;
    }
  }

  /**
   * Clear all tokens.
   * Should be called on logout.
   */
  clearTokens(): void {
    this.accessToken = null;
    try {
      sessionStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
    } catch (e) {
      console.warn('Failed to clear tokens from storage:', e);
    }
  }

  /**
   * Check if there are any tokens stored.
   */
  hasTokens(): boolean {
    return !!(this.getAccessToken() || this.getRefreshToken());
  }
}

export const tokenStorage = new TokenStorage();
