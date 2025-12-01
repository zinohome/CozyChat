import { apiClient } from './api';
import type { User, UserProfile, UserPreferences } from '@/types/user';
import { logger } from '@/utils/logger';

const log = logger.withTag('userApi');

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
    // 使用 /me/profile 端点，更安全（只能更新自己的资料）
    return apiClient.put<UserProfile>('/v1/users/me/profile', data);
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
    // 后端返回格式：{ "preferences": {...} }
    // 使用原始客户端直接获取，避免 handleResponse 处理
    const rawClient = apiClient.getRawClient();
    const response = await rawClient.get<{ preferences: UserPreferences }>('/v1/users/me/preferences');
    log.debug('获取偏好设置, 响应数据:', response.data);
    // 直接返回 preferences 字段
    const result = response.data.preferences || {};
    log.debug('返回偏好设置:', result);
    return result;
  },

  /**
   * 更新当前用户偏好
   */
  async updateCurrentUserPreferences(
    preferences: UserPreferences
  ): Promise<UserPreferences> {
    // 后端返回格式：{ "message": "...", "preferences": {...} }
    // 使用原始客户端直接获取，避免 handleResponse 处理
    const rawClient = apiClient.getRawClient();
    log.debug('更新偏好设置, 请求数据:', preferences);
    const response = await rawClient.put<{ preferences: UserPreferences }>('/v1/users/me/preferences', preferences);
    log.debug('更新偏好设置, 响应数据:', response.data);
    // 直接返回 preferences 字段
    const result = response.data.preferences || preferences;
    log.debug('返回偏好设置:', result);
    return result;
  },

  /**
   * 获取当前用户统计
   */
  async getCurrentUserStats(): Promise<any> {
    return apiClient.get<any>('/v1/users/me/stats');
  },
};

