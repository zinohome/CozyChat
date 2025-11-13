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
              // 忽略解析错误，继续处理下一个chunk
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
   * 
   * 注意：后端没有单独的消息列表接口，消息通过会话详情接口返回
   * 这里使用会话API获取消息
   */
  async getHistory(sessionId: string): Promise<Message[]> {
    try {
      // 验证 sessionId 格式（UUID）
      if (!sessionId || sessionId === 'default') {
        return [];
      }
      
      // 验证 UUID 格式
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
      if (!uuidRegex.test(sessionId)) {
        console.warn(`Invalid session ID format: ${sessionId}`);
        return [];
      }
      
      const { sessionApi } = await import('./session');
      const session = await sessionApi.getSession(sessionId);
      // 将 MessageInfo 转换为 Message 格式
      return (session.messages || []).map((msg) => ({
        id: msg.id,
        role: msg.role as 'user' | 'assistant' | 'system',
        content: msg.content,
        timestamp: msg.created_at, // 将 created_at 映射为 timestamp
        session_id: sessionId,
        metadata: msg.metadata,
      }));
    } catch (error: any) {
      // 如果是404错误（会话不存在或已删除），返回空数组，不抛出错误
      if (error?.response?.status === 404) {
        console.warn(`Session ${sessionId} not found, returning empty message list`);
        return [];
      }
      // 如果是400错误（无效的session ID格式），返回空数组，不抛出错误
      if (error?.response?.status === 400) {
        console.warn(`Invalid session ID format: ${sessionId}, returning empty message list`);
        return [];
      }
      console.error(`Failed to get history for session ${sessionId}:`, error);
      throw error;
    }
  },

  /**
   * 更新消息
   * 
   * 注意：后端暂未提供消息更新接口，此方法暂未实现
   */
  async updateMessage(
    sessionId: string,
    messageId: string,
    content: string
  ): Promise<Message> {
    throw new Error('Message update is not supported by the backend API');
  },

  /**
   * 删除消息
   * 
   * 注意：后端暂未提供消息删除接口，此方法暂未实现
   */
  async deleteMessage(sessionId: string, messageId: string): Promise<void> {
    throw new Error('Message deletion is not supported by the backend API');
  },

  /**
   * 保存语音通话消息
   */
  async saveVoiceCallMessages(
    sessionId: string,
    messages: Array<{
      role: 'user' | 'assistant';
      content: string;
      timestamp?: string;
    }>
  ): Promise<{ message: string; saved_count: number; session_id: string }> {
    return apiClient.post('/v1/chat/voice-call-messages', {
      session_id: sessionId,
      messages: messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || new Date().toISOString(),
      })),
    });
  },
};

