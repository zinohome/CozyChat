import { apiClient } from './api';
import type { User, UserProfile, UserPreferences } from '@/types/user';

/**
 * 用户API服务
 *
 * 封装用户相关的API调用。
 */
export const userApi = {
  /**
   * 获取用户信息
   */
  async getUser(userId: string): Promise<User> {
    return apiClient.get<User>(`/v1/users/${userId}`);
  },

  /**
   * 更新用户信息
   */
  async updateUser(userId: string, data: Partial<User>): Promise<User> {
    return apiClient.put<User>(`/v1/users/${userId}`, data);
  },

  /**
   * 获取用户资料
   */
  async getUserProfile(userId: string): Promise<UserProfile> {
    return apiClient.get<UserProfile>(`/v1/users/${userId}/profile`);
  },

  /**
   * 更新用户资料
   */
  async updateUserProfile(
    userId: string,
    data: Partial<UserProfile>
  ): Promise<UserProfile> {
    return apiClient.put<UserProfile>(`/v1/users/${userId}/profile`, data);
  },

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>('/v1/users/me');
  },

  /**
   * 更新当前用户信息
   */
  async updateCurrentUser(data: Partial<User>): Promise<User> {
    return apiClient.put<User>('/v1/users/me', data);
  },

  /**
   * 获取当前用户画像
   */
  async getCurrentUserProfile(): Promise<UserProfile> {
    return apiClient.get<UserProfile>('/v1/users/me/profile');
  },

  /**
   * 获取当前用户偏好
   */
  async getCurrentUserPreferences(): Promise<UserPreferences> {
    return apiClient.get<UserPreferences>('/v1/users/me/preferences');
  },

  /**
   * 更新当前用户偏好
   */
  async updateCurrentUserPreferences(
    preferences: UserPreferences
  ): Promise<UserPreferences> {
    return apiClient.put<UserPreferences>('/v1/users/me/preferences', preferences);
  },

  /**
   * 获取当前用户统计
   */
  async getCurrentUserStats(): Promise<any> {
    return apiClient.get<any>('/v1/users/me/stats');
  },
};

