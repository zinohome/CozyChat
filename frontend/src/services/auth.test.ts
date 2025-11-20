/**
 * 认证服务测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { authApi } from './auth';
import { apiClient } from './api';

// Mock apiClient
vi.mock('./api', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe('authApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('login', () => {
    it('应该成功登录', async () => {
      const loginRequest = {
        username: 'testuser',
        password: 'password123',
      };

      const loginResponse = {
        access_token: 'token',
        refresh_token: 'refresh',
        expires_in: 3600,
        user: {
          id: 'user-1',
          username: 'testuser',
          email: 'test@example.com',
        },
      };

      (apiClient.post as any).mockResolvedValue(loginResponse);

      const result = await authApi.login(loginRequest);

      expect(apiClient.post).toHaveBeenCalledWith('/v1/users/login', loginRequest);
      expect(result).toEqual(loginResponse);
    });

    it('应该处理登录错误', async () => {
      const loginRequest = {
        username: 'testuser',
        password: 'wrongpassword',
      };

      const error = new Error('Invalid credentials');
      (apiClient.post as any).mockRejectedValue(error);

      await expect(authApi.login(loginRequest)).rejects.toThrow();
    });
  });

  describe('register', () => {
    it('应该成功注册', async () => {
      const registerRequest = {
        username: 'newuser',
        email: 'new@example.com',
        password: 'password123',
      };

      const registerResponse = {
        access_token: 'token',
        refresh_token: 'refresh',
        expires_in: 3600,
        user: {
          id: 'user-2',
          username: 'newuser',
          email: 'new@example.com',
        },
      };

      (apiClient.post as any).mockResolvedValue(registerResponse);

      const result = await authApi.register(registerRequest);

      expect(apiClient.post).toHaveBeenCalledWith('/v1/users/register', registerRequest);
      expect(result).toEqual(registerResponse);
    });
  });

  describe('logout', () => {
    it('应该成功登出', async () => {
      // authApi.logout只是清除本地存储，不调用API
      const localStorageMock = {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      };
      global.localStorage = localStorageMock as any;

      await authApi.logout();

      // logout只清除本地存储
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
    });
  });

  describe('getCurrentUser', () => {
    it('应该获取当前用户', async () => {
      const user = {
        id: 'user-1',
        username: 'testuser',
        email: 'test@example.com',
      };

      (apiClient.get as any).mockResolvedValue(user);

      const result = await authApi.getCurrentUser();

      expect(apiClient.get).toHaveBeenCalledWith('/v1/users/me');
      expect(result).toEqual(user);
    });
  });

  describe('refreshToken', () => {
    it('应该成功刷新Token', async () => {
      // Mock localStorage
      const localStorageMock = {
        getItem: vi.fn((key: string) => {
          if (key === 'refresh_token') return 'refresh-token';
          return null;
        }),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      };
      global.localStorage = localStorageMock as any;

      const refreshResponse = {
        access_token: 'new-token',
        expires_in: 3600,
      };

      // Mock axios.default.post (authApi.refreshToken使用原始axios)
      const axiosModule = await import('axios');
      const mockPost = vi.fn().mockResolvedValue({ data: refreshResponse });
      (axiosModule.default as any).post = mockPost;

      const result = await authApi.refreshToken();

      expect(mockPost).toHaveBeenCalled();
      expect(result).toEqual(refreshResponse);
    });
  });
});

