import apiClient from './client';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface UpdateProfileData {
  full_name?: string;
  avatar_url?: string;
}

export async function getProfile(): Promise<UserProfile> {
  const response = await apiClient.get<UserProfile>('/users/profile');
  return response.data;
}

export async function updateProfile(data: UpdateProfileData): Promise<UserProfile> {
  const response = await apiClient.patch<UserProfile>('/users/profile', data);
  return response.data;
}
