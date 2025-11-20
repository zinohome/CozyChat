import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuth } from './useAuth';
import { authApi } from '@/services/auth';
// authStoreModule 未使用，已移除

// Mock authApi
vi.mock('@/services/auth', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    refreshToken: vi.fn(),
  },
}));

// Mock useAuthStore
const mockSetUser = vi.fn();
const mockSetLoading = vi.fn();
const mockSetError = vi.fn();
const mockLogout = vi.fn();

vi.mock('@/store/slices/authSlice', () => ({
  useAuthStore: vi.fn((selector?: any) => {
    if (selector) {
      return selector({
        user: null,
        setUser: mockSetUser,
        setLoading: mockSetLoading,
        setError: mockSetError,
        logout: mockLogout,
      });
    }
    return {
      user: null,
      setUser: mockSetUser,
      setLoading: mockSetLoading,
      setError: mockSetError,
      logout: mockLogout,
    };
  }),
}));

const createWrapper = () => {
  const testQueryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const Wrapper = ({ children }: { children: React.ReactNode }) => {
    return React.createElement(QueryClientProvider, { client: testQueryClient }, children);
  };
  
  return Wrapper;
};

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该获取当前用户', async () => {
    const mockUser = {
      id: 'user-1',
      username: 'testuser',
      email: 'test@example.com',
      role: 'user' as const,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    // Mock localStorage to have access_token (required by enabled condition)
    Storage.prototype.getItem = vi.fn((key) => {
      if (key === 'access_token') return 'test-token';
      return null;
    });

    vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    // 等待加载完成
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // 验证用户数据可用（不依赖onSuccess回调，因为React Query v5已废弃）
    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });
  });

  it('应该登录用户', async () => {
    const loginRequest = {
      username: 'testuser',
      password: 'password123',
    };

    const loginResponse = {
      access_token: 'token',
      refresh_token: 'refresh',
      token_type: 'Bearer',
      expires_in: 3600,
      user: {
        id: 'user-1',
        username: 'testuser',
        email: 'test@example.com',
        role: 'user' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    };

    vi.mocked(authApi.login).mockResolvedValue(loginResponse);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await result.current.login(loginRequest);

    expect(authApi.login).toHaveBeenCalledWith(loginRequest);
    expect(mockSetUser).toHaveBeenCalledWith(loginResponse.user);
  });

  it('应该注册用户', async () => {
    const registerRequest = {
      username: 'newuser',
      email: 'new@example.com',
      password: 'password123',
    };

    const registerResponse = {
      access_token: 'token',
      refresh_token: 'refresh',
      token_type: 'Bearer',
      expires_in: 3600,
      user: {
        id: 'user-2',
        username: 'newuser',
        email: 'new@example.com',
        role: 'user' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    };

    vi.mocked(authApi.register).mockResolvedValue(registerResponse);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await result.current.register(registerRequest);

    expect(authApi.register).toHaveBeenCalledWith(registerRequest);
    expect(mockSetUser).toHaveBeenCalledWith(registerResponse.user);
  });

  it('应该登出用户', async () => {
    vi.mocked(authApi.logout).mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await result.current.logout();

    expect(authApi.logout).toHaveBeenCalled();
    expect(mockLogout).toHaveBeenCalled();
  });
});

