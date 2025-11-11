import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuth } from './useAuth';
import { authApi } from '@/services/auth';
import * as authStoreModule from '@/store/slices/authSlice';

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
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
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
    };

    vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockSetUser).toHaveBeenCalledWith(mockUser);
  });

  it('应该登录用户', async () => {
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
      expires_in: 3600,
      user: {
        id: 'user-2',
        username: 'newuser',
        email: 'new@example.com',
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

