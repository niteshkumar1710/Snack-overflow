import { apiClient } from './client';
import { LoginCredentials, TokenResponse, User } from '../types';

export const authApi = {
  /**
   * Authenticate user credentials and receive access token.
   */
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/auth/login', credentials);
    return response.data;
  },

  /**
   * Fetch current authenticated user's profile using bearer token.
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  /**
   * Verify whether the authenticated user has administrator privileges.
   */
  async checkAdmin(): Promise<{ is_admin: boolean; user_id: number; email: string }> {
    const response = await apiClient.get<{ is_admin: boolean; user_id: number; email: string }>(
      '/auth/admin-check'
    );
    return response.data;
  },
};
