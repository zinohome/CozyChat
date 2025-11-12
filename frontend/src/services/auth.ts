import { apiClient } from './api';
import type {
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  User,
} from '@/types/user';

/**
 * 认证API服务
 *
 * 封装认证相关的API调用。
 */
export const authApi = {
  /**
   * 用户登录
   */
  async login(request: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>(
      '/v1/users/login',
      request
    );
    // 保存token
    if (response.access_token) {
      localStorage.setItem('access_token', response.access_token);
      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token);
      }
    }
    return response;
  },

  /**
   * 用户注册
   */
  async register(request: RegisterRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>(
      '/v1/users/register',
      request
    );
    // 保存token
    if (response.access_token) {
      localStorage.setItem('access_token', response.access_token);
      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token);
      }
    }
    return response;
  },

  /**
   * 刷新Token
   * 
   * 注意：此方法通常不需要手动调用，API拦截器会自动处理Token刷新。
   * 仅在需要主动刷新时使用。
   */
  async refreshToken(): Promise<{ access_token: string; expires_in: number }> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    // 使用原始axios，避免拦截器循环
    const axios = (await import('axios')).default;
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const response = await axios.post<{
      access_token: string;
      expires_in: number;
    }>(
      `${API_BASE_URL}/v1/auth/refresh`,
      { refresh_token: refreshToken },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    // 更新token
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }
    return response.data;
  },

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>('/v1/users/me');
  },

  /**
   * 用户登出
   * 
   * 注意：后端没有专门的登出接口，这里只是清除本地token
   */
  async logout(): Promise<void> {
    // 清除本地token
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};

