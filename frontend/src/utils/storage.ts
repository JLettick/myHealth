/**
 * Token storage utilities.
 *
 * Access tokens are stored in memory only (not persisted to storage).
 * Refresh tokens are managed as httpOnly cookies by the backend —
 * they are never accessible from JavaScript.
 */

/**
 * Token storage manager.
 *
 * Stores the access token in memory only. On page refresh the token is lost
 * and re-acquired via the /auth/refresh endpoint (cookie sent automatically).
 */
class TokenStorage {
  private accessToken: string | null = null;

  /**
   * Set the access token (memory only).
   */
  setAccessToken(token: string): void {
    this.accessToken = token;
  }

  /**
   * Get the access token from memory.
   */
  getAccessToken(): string | null {
    return this.accessToken;
  }

  /**
   * Clear all tokens.
   * Should be called on logout.
   * Also cleans up any legacy localStorage/sessionStorage entries.
   */
  clearTokens(): void {
    this.accessToken = null;
    try {
      sessionStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } catch {
      // Ignore storage errors during cleanup
    }
  }

  /**
   * Check if there is an access token stored.
   */
  hasTokens(): boolean {
    return !!this.accessToken;
  }
}

export const tokenStorage = new TokenStorage();
