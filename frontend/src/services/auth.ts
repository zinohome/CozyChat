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
      '/v1/auth/login',
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
      '/v1/auth/register',
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
   */
  async refreshToken(): Promise<{ access_token: string; expires_in: number }> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    const response = await apiClient.post<{
      access_token: string;
      expires_in: number;
    }>('/v1/auth/refresh', null, {
      headers: {
        Authorization: `Bearer ${refreshToken}`,
      },
    });
    // 更新token
    if (response.access_token) {
      localStorage.setItem('access_token', response.access_token);
    }
    return response;
  },

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>('/v1/auth/me');
  },

  /**
   * 用户登出
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post('/v1/auth/logout');
    } finally {
      // 清除本地token
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },
};

