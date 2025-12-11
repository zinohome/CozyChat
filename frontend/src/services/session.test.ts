/**
 * sessionApi服务测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { sessionApi } from './session';
import { apiClient } from './api';

// Mock apiClient
vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('sessionApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该获取会话列表', async () => {
    const sessionId = '123e4567-e89b-12d3-a456-426614174000';
    const mockResponse = {
      sessions: [
        {
          session_id: sessionId,
          personality_id: 'personality-1',
          title: 'Test Session',
          message_count: 10,
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 10,
    };
    (apiClient.get as any).mockResolvedValue(mockResponse);

    const result = await sessionApi.getSessions();
    
    expect(apiClient.get).toHaveBeenCalledWith('/v1/sessions', {
      params: {
        sort: 'last_message_at',
        order: 'desc',
      },
    });
    expect(result.items).toHaveLength(1);
    expect(result.items[0].id).toBe(sessionId);
  });

  it('应该获取单个会话', async () => {
    const mockSession = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      session_id: '123e4567-e89b-12d3-a456-426614174000',
      title: 'Test Session',
      personality_id: 'personality-1',
      created_at: '2024-01-01T00:00:00Z',
    };
    (apiClient.get as any).mockResolvedValue(mockSession);

    const sessionId = '123e4567-e89b-12d3-a456-426614174000';
    const result = await sessionApi.getSession(sessionId);
    
    expect(apiClient.get).toHaveBeenCalledWith(`/v1/sessions/${sessionId}`);
    expect(result).toEqual(mockSession);
  });

  it('应该创建会话', async () => {
    const sessionId = '123e4567-e89b-12d3-a456-426614174000';
    // 后端返回格式
    const mockResponse = {
      session_id: sessionId,
      personality_id: 'personality-1',
      title: 'New Session',
      created_at: '2024-01-01T00:00:00Z',
    };
    (apiClient.post as any).mockResolvedValue(mockResponse);

    const result = await sessionApi.createSession({
      title: 'New Session',
      personality_id: 'personality-1',
    });
    
    expect(apiClient.post).toHaveBeenCalledWith('/v1/sessions', {
      title: 'New Session',
      personality_id: 'personality-1',
    });
    // 验证返回的会话包含必要字段（前端会转换格式）
    expect(result.id).toBe(sessionId);
    expect(result.session_id).toBe(sessionId);
    expect(result.title).toBe('New Session');
  });

  it('应该更新会话', async () => {
    const sessionId = '123e4567-e89b-12d3-a456-426614174000';
    // 后端返回格式
    const mockResponse = {
      session_id: sessionId,
      title: 'Updated Session',
      updated_at: '2024-01-01T00:00:00Z',
    };
    // Mock getSession（updateSession会调用它）
    const mockExistingSession = {
      id: sessionId,
      session_id: sessionId,
      title: 'Old Session',
      personality_id: 'personality-1',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      message_count: 0,
    };
    (apiClient.put as any).mockResolvedValue(mockResponse);
    (apiClient.get as any).mockResolvedValue(mockExistingSession);

    const result = await sessionApi.updateSession(sessionId, {
      title: 'Updated Session',
    });
    
    expect(apiClient.put).toHaveBeenCalledWith(`/v1/sessions/${sessionId}`, {
      title: 'Updated Session',
    });
    // 验证返回的会话包含更新后的字段
    expect(result.id).toBe(sessionId);
    expect(result.title).toBe('Updated Session');
  });

  it('应该删除会话', async () => {
    const sessionId = '123e4567-e89b-12d3-a456-426614174000';
    (apiClient.delete as any).mockResolvedValue({});

    await sessionApi.deleteSession(sessionId);
    
    expect(apiClient.delete).toHaveBeenCalledWith(`/v1/sessions/${sessionId}`);
  });

  it('应该生成会话标题', async () => {
    const sessionId = '123e4567-e89b-12d3-a456-426614174000';
    // 后端返回格式
    const mockResponse = {
      session_id: sessionId,
      title: 'Generated Title',
      generated_at: '2024-01-01T00:00:00Z',
      used_message_count: 10,
    };
    (apiClient.post as any).mockResolvedValue(mockResponse);

    const result = await sessionApi.generateTitle(sessionId);
    
    expect(apiClient.post).toHaveBeenCalledWith(`/v1/sessions/${sessionId}/title`, {
      force: false,
      max_messages: undefined,
    });
    expect(result).toEqual(mockResponse);
  });
});
