import { apiClient } from './api';
import type {
  ChatRequest,
  ChatResponse,
  Message,
  StreamChunk,
} from '@/types/chat';

/**
 * 聊天API服务
 *
 * 封装聊天相关的API调用。
 */
export const chatApi = {
  /**
   * 发送聊天消息（非流式）
   */
  async send(request: ChatRequest): Promise<ChatResponse> {
    return apiClient.post<ChatResponse>('/v1/chat/completions', {
      ...request,
      stream: false,
    });
  },

  /**
   * 流式聊天（SSE）
   */
  async *streamChat(
    request: ChatRequest
  ): AsyncGenerator<StreamChunk, void, unknown> {
    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/v1/chat/completions`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: JSON.stringify({
          ...request,
          stream: true,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is not readable');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim() === '') continue;
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              return;
            }
            try {
              const chunk: StreamChunk = JSON.parse(data);
              yield chunk;
            } catch (e) {
              console.warn('Failed to parse SSE chunk:', e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },

  /**
   * 获取历史消息
   */
  async getHistory(sessionId: string): Promise<Message[]> {
    return apiClient.get<Message[]>(
      `/v1/chat/sessions/${sessionId}/messages`
    );
  },
};

