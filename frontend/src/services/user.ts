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
   * 获取用户偏好
   */
  async getUserPreferences(userId: string): Promise<UserPreferences> {
    return apiClient.get<UserPreferences>(`/v1/users/${userId}/preferences`);
  },

  /**
   * 更新用户偏好
   */
  async updateUserPreferences(
    userId: string,
    preferences: UserPreferences
  ): Promise<UserPreferences> {
    return apiClient.put<UserPreferences>(
      `/v1/users/${userId}/preferences`,
      preferences
    );
  },
};

