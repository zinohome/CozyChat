/**
 * userApi服务测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { userApi } from './user';
import { apiClient } from './api';

// Mock apiClient
vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
    put: vi.fn(),
    getRawClient: vi.fn(() => ({
      get: vi.fn(),
      put: vi.fn(),
    })),
  },
}));

describe('userApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该获取用户信息', async () => {
    const mockUser = { id: '1', username: 'testuser' };
    (apiClient.get as any).mockResolvedValue(mockUser);

    const result = await userApi.getUser('1');
    
    expect(apiClient.get).toHaveBeenCalledWith('/v1/users/1');
    expect(result).toEqual(mockUser);
  });

  it('应该更新用户信息', async () => {
    const mockUser = { id: '1', username: 'testuser' };
    (apiClient.put as any).mockResolvedValue(mockUser);

    const result = await userApi.updateUser('1', { username: 'newuser' });
    
    expect(apiClient.put).toHaveBeenCalledWith('/v1/users/1', { username: 'newuser' });
    expect(result).toEqual(mockUser);
  });

  it('应该获取用户资料', async () => {
    const mockProfile = { id: '1', display_name: 'Test User' };
    (apiClient.get as any).mockResolvedValue(mockProfile);

    const result = await userApi.getUserProfile('1');
    
    expect(apiClient.get).toHaveBeenCalledWith('/v1/users/1/profile');
    expect(result).toEqual(mockProfile);
  });

  it('应该更新用户资料', async () => {
    const mockProfile = { id: '1', display_name: 'New Name' };
    (apiClient.put as any).mockResolvedValue(mockProfile);

    const result = await userApi.updateUserProfile('1', { display_name: 'New Name' });
    
    expect(apiClient.put).toHaveBeenCalledWith('/v1/users/me/profile', { display_name: 'New Name' });
    expect(result).toEqual(mockProfile);
  });

  it('应该获取当前用户信息', async () => {
    const mockUser = { id: '1', username: 'testuser' };
    (apiClient.get as any).mockResolvedValue(mockUser);

    const result = await userApi.getCurrentUser();
    
    expect(apiClient.get).toHaveBeenCalledWith('/v1/users/me');
    expect(result).toEqual(mockUser);
  });

  it('应该获取当前用户偏好', async () => {
    const mockPreferences = { auto_tts: true, theme: 'dark' };
    const mockRawClient = {
      get: vi.fn().mockResolvedValue({
        data: { preferences: mockPreferences },
      }),
    };
    (apiClient.getRawClient as any).mockReturnValue(mockRawClient);

    const result = await userApi.getCurrentUserPreferences();
    
    expect(mockRawClient.get).toHaveBeenCalledWith('/v1/users/me/preferences');
    expect(result).toEqual(mockPreferences);
  });

  it('应该更新当前用户偏好', async () => {
    const mockPreferences = { auto_tts: false, theme: 'light' };
    const mockRawClient = {
      put: vi.fn().mockResolvedValue({
        data: { preferences: mockPreferences },
      }),
    };
    (apiClient.getRawClient as any).mockReturnValue(mockRawClient);

    const result = await userApi.updateCurrentUserPreferences(mockPreferences);
    
    expect(mockRawClient.put).toHaveBeenCalledWith('/v1/users/me/preferences', mockPreferences);
    expect(result).toEqual(mockPreferences);
  });
});
