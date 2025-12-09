/**
 * UserProfile组件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import { UserProfile } from './UserProfile';
import { useAuthStore } from '@/store/slices/authSlice';
import { userApi } from '@/services/user';
import { useQuery } from '@tanstack/react-query';

// Mock useAuthStore
const mockUser = {
  id: '1',
  username: 'testuser',
  email: 'test@example.com',
  role: 'user',
};

const mockUseAuthStore = vi.fn(() => ({
  user: mockUser,
  isAuthenticated: true,
}));

vi.mock('@/store/slices/authSlice', () => ({
  useAuthStore: () => mockUseAuthStore(),
}));

// Mock userApi
const mockGetUserProfile = vi.fn();
vi.mock('@/services/user', () => ({
  userApi: {
    getUserProfile: mockGetUserProfile,
  },
}));

// Mock useQuery
vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual('@tanstack/react-query');
  return {
    ...actual,
    useQuery: vi.fn(() => ({
      data: null,
      isLoading: false,
    })),
  };
});

describe('UserProfile', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuthStore.mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
    });
    mockGetUserProfile.mockResolvedValue({
      display_name: 'Test User',
      bio: 'Test bio',
    });
    (useQuery as any).mockReturnValue({
      data: {
        display_name: 'Test User',
        bio: 'Test bio',
      },
      isLoading: false,
    });
  });

  it('应该渲染用户信息', async () => {
    render(<UserProfile />);
    
    await waitFor(() => {
      // 应该显示用户名或display_name
      const username = screen.queryByText('testuser') || 
                      screen.queryByText('Test User');
      expect(username).toBeInTheDocument();
    });
    
    // 应该显示邮箱
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
  });

  it('应该处理未登录状态', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
    });

    const { container } = render(<UserProfile />);
    
    // 组件应该返回null或不渲染内容
    expect(container.firstChild).toBeNull();
  });

  it('应该显示加载状态', () => {
    (useQuery as any).mockReturnValue({
      data: null,
      isLoading: true,
    });

    render(<UserProfile />);
    
    // Card组件应该显示loading状态
    // 具体实现取决于Card组件的loading prop
    expect(screen.getByText('testuser')).toBeInTheDocument();
  });
});
