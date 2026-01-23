/**
 * User-related TypeScript types.
 */

/**
 * User profile data.
 */
export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  created_at: string;
  updated_at: string | null;
}

/**
 * Profile update request data.
 */
export interface UpdateProfileData {
  full_name?: string;
  avatar_url?: string;
}

/**
 * Account deletion confirmation.
 */
export interface DeleteAccountData {
  confirm: boolean;
}
