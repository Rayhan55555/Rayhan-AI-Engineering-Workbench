import { apiClient, ApiResponse, setAccessToken } from './client';

export interface UserProfile {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export async function loginUser(email: string, password: string): Promise<ApiResponse<AuthTokens>> {
  const res = await apiClient<AuthTokens>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });

  if (res.data?.access_token) {
    setAccessToken(res.data.access_token);
  }

  return res;
}

export async function registerUser(
  email: string,
  username: string,
  password: string
): Promise<ApiResponse<UserProfile>> {
  return apiClient<UserProfile>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, username, password }),
  });
}

export async function refreshAuthToken(refreshToken: string): Promise<ApiResponse<{ access_token: string; expires_in: number }>> {
  const res = await apiClient<{ access_token: string; expires_in: number }>('/api/v1/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (res.data?.access_token) {
    setAccessToken(res.data.access_token);
  }

  return res;
}

export async function logoutUser(): Promise<ApiResponse<null>> {
  const res = await apiClient<null>('/api/v1/auth/logout', {
    method: 'POST',
  });
  setAccessToken(null);
  return res;
}

export async function fetchCurrentUser(): Promise<ApiResponse<UserProfile>> {
  return apiClient<UserProfile>('/api/v1/auth/me');
}
