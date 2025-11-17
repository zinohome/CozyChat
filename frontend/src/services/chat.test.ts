/**
 * 聊天服务测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { chatApi } from './chat';
import { apiClient } from './api';

// Mock dependencies
vi.mock('./api', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

// Mock fetch for streamChat
global.fetch = vi.fn();

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(() => 'test-token'),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};
global.localStorage = localStorageMock as any;

describe('chatApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('send', () => {
    it('应该发送聊天消息', async () => {
      const request = {
        messages: [{ role: 'user', content: 'Hello' }],
        personality_id: 'personality-1',
        stream: false,
      };

      const response = {
        id: 'response-1',
        created: Date.now() / 1000,
        choices: [
          {
            message: {
              role: 'assistant',
              content: 'Hi there',
            },
          },
        ],
      };

      (apiClient.post as any).mockResolvedValue(response);

      const result = await chatApi.send(request);

      expect(apiClient.post).toHaveBeenCalledWith('/v1/chat/completions', {
        ...request,
        stream: false,
      });
      expect(result).toEqual(response);
    });
  });

  describe('streamChat', () => {
    it('应该处理流式响应', async () => {
      const request = {
        messages: [{ role: 'user', content: 'Hello' }],
        personality_id: 'personality-1',
        stream: true,
      };

      // Mock ReadableStream
      const mockReader = {
        read: vi.fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode('data: {"content":"Hello"}\n\n'),
          })
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode('data: {"content":" World"}\n\n'),
          })
          .mockResolvedValueOnce({
            done: true,
            value: undefined,
          }),
        releaseLock: vi.fn(),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      };

      (global.fetch as any).mockResolvedValue(mockResponse);

      const chunks: any[] = [];
      for await (const chunk of chatApi.streamChat(request)) {
        chunks.push(chunk);
      }

      expect(chunks.length).toBeGreaterThan(0);
      expect(mockReader.releaseLock).toHaveBeenCalled();
    });

    it('应该处理流式响应结束标记', async () => {
      const request = {
        messages: [{ role: 'user', content: 'Hello' }],
        personality_id: 'personality-1',
        stream: true,
      };

      const mockReader = {
        read: vi.fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode('data: [DONE]\n\n'),
          })
          .mockResolvedValueOnce({
            done: true,
            value: undefined,
          }),
        releaseLock: vi.fn(),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      };

      (global.fetch as any).mockResolvedValue(mockResponse);

      const chunks: any[] = [];
      for await (const chunk of chatApi.streamChat(request)) {
        chunks.push(chunk);
      }

      // [DONE] 标记应该结束流
      expect(chunks.length).toBe(0);
    });

    it('应该处理HTTP错误', async () => {
      const request = {
        messages: [{ role: 'user', content: 'Hello' }],
        personality_id: 'personality-1',
        stream: true,
      };

      const mockResponse = {
        ok: false,
        status: 500,
      };

      (global.fetch as any).mockResolvedValue(mockResponse);

      await expect(async () => {
        for await (const chunk of chatApi.streamChat(request)) {
          // Should not reach here
        }
      }).rejects.toThrow();
    });
  });

  describe('getHistory', () => {
    it('应该获取历史消息', async () => {
      const sessionId = 'session-1';
      const messages = [
        { id: '1', role: 'user', content: 'Hello', timestamp: new Date() },
        { id: '2', role: 'assistant', content: 'Hi', timestamp: new Date() },
      ];

      (apiClient.get as any).mockResolvedValue(messages);

      const result = await chatApi.getHistory(sessionId);

      expect(apiClient.get).toHaveBeenCalledWith(`/v1/sessions/${sessionId}/messages`);
      expect(result).toEqual(messages);
    });

    it('应该处理空sessionId', async () => {
      const result = await chatApi.getHistory('');
      expect(result).toEqual([]);
      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('应该处理default sessionId', async () => {
      const result = await chatApi.getHistory('default');
      expect(result).toEqual([]);
      expect(apiClient.get).not.toHaveBeenCalled();
    });
  });
});

