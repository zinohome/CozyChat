import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from './authSlice';
import type { User } from '@/types/user';

describe('authSlice', () => {
  beforeEach(() => {
    // 重置store状态
    useAuthStore.setState({
      user: null,
      loading: false,
      error: null,
    });
  });

  it('应该初始化空状态', () => {
    const state = useAuthStore.getState();
    expect(state.user).toBe(null);
    expect(state.loading).toBe(false);
    expect(state.error).toBe(null);
  });

  it('应该设置用户', () => {
    const user: User = {
      id: 'user-1',
      username: 'testuser',
      email: 'test@example.com',
    };

    useAuthStore.getState().setUser(user);
    const state = useAuthStore.getState();

    expect(state.user).toEqual(user);
  });

  it('应该设置加载状态', () => {
    useAuthStore.getState().setLoading(true);
    expect(useAuthStore.getState().loading).toBe(true);
  });

  it('应该设置错误', () => {
    useAuthStore.getState().setError('Test error');
    expect(useAuthStore.getState().error).toBe('Test error');
  });

  it('应该登出', () => {
    const user: User = {
      id: 'user-1',
      username: 'testuser',
      email: 'test@example.com',
    };

    useAuthStore.getState().setUser(user);
    useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.user).toBe(null);
    expect(state.isAuthenticated).toBe(false);
    expect(state.error).toBe(null);
  });
});

