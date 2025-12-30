import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { User } from '@/types/user';

/**
 * 认证状态
 */
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

/**
 * 认证Actions
 */
interface AuthActions {
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  logout: () => void;
}

/**
 * 认证Store
 */
type AuthStore = AuthState & AuthActions;

/**
 * 初始状态
 */
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
};

/**
 * 认证状态管理Store
 *
 * 使用Zustand管理认证相关的全局状态。
 */
export const useAuthStore = create<AuthStore>()(
  devtools(
    persist(
      (set) => ({
        ...initialState,

        setUser: (user) =>
          set({
            user,
            isAuthenticated: !!user,
            error: null,
          }),

        setLoading: (loading) =>
          set({
            isLoading: loading,
          }),

        setError: (error) =>
          set({
            error,
          }),

        logout: () =>
          set({
            ...initialState,
          }),
      }),
      {
        name: 'auth-storage',
        partialize: (state) => ({
          user: state.user,
          isAuthenticated: state.isAuthenticated,
        }),
      }
    ),
    { name: 'AuthStore' }
  )
);

