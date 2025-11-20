import { useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/slices/authSlice';
import { authApi } from '@/services/auth';
import type { LoginRequest, RegisterRequest } from '@/types/user';

/**
 * 认证Hook
 *
 * 使用React Query管理认证相关的服务端状态。
 */
export const useAuth = () => {
  const queryClient = useQueryClient();
  const { setUser, setError, logout: logoutStore } = useAuthStore();

  // 获取当前用户
  const { data: user, isLoading, error } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: () => authApi.getCurrentUser(),
    enabled: !!localStorage.getItem('access_token'),
    retry: false,
  });

  // React Query v5: 使用 useEffect 替代 onSuccess/onError
  useEffect(() => {
    if (user) {
      setUser(user);
    }
  }, [user, setUser]);

  useEffect(() => {
    if (error) {
      setUser(null);
    }
  }, [error, setUser]);

  // 登录
  const loginMutation = useMutation({
    mutationFn: (request: LoginRequest) => authApi.login(request),
    onSuccess: (response) => {
      setUser(response.user);
      queryClient.setQueryData(['auth', 'me'], response.user);
    },
    onError: (error: any) => {
      setError(error.message || '登录失败');
    },
  });

  // 注册
  const registerMutation = useMutation({
    mutationFn: (request: RegisterRequest) => authApi.register(request),
    onSuccess: (response) => {
      setUser(response.user);
      queryClient.setQueryData(['auth', 'me'], response.user);
    },
    onError: (error: any) => {
      setError(error.message || '注册失败');
    },
  });

  // 登出
  const logoutMutation = useMutation({
    mutationFn: () => authApi.logout(),
    onSuccess: () => {
      logoutStore();
      queryClient.clear();
    },
  });

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    login: loginMutation.mutateAsync,
    register: registerMutation.mutateAsync,
    logout: logoutMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
    isLoggingOut: logoutMutation.isPending,
  };
};

