import { apiClient } from './api';
import type {
  Session,
  CreateSessionRequest,
  UpdateSessionRequest,
  PaginatedResponse,
  PaginationParams,
} from '@/types/session';
import type { Message } from '@/types/chat';

/**
 * 会话API服务
 *
 * 封装会话相关的API调用。
 */
export const sessionApi = {
  /**
   * 获取会话列表
   */
  async getSessions(
    params?: PaginationParams
  ): Promise<PaginatedResponse<Session>> {
    return apiClient.get<PaginatedResponse<Session>>('/v1/chat/sessions', {
      params,
    });
  },

  /**
   * 获取单个会话
   */
  async getSession(sessionId: string): Promise<Session> {
    return apiClient.get<Session>(`/v1/chat/sessions/${sessionId}`);
  },

  /**
   * 创建会话
   */
  async createSession(request: CreateSessionRequest): Promise<Session> {
    return apiClient.post<Session>('/v1/chat/sessions', request);
  },

  /**
   * 更新会话
   */
  async updateSession(
    sessionId: string,
    request: UpdateSessionRequest
  ): Promise<Session> {
    return apiClient.put<Session>(`/v1/chat/sessions/${sessionId}`, request);
  },

  /**
   * 删除会话
   */
  async deleteSession(sessionId: string): Promise<void> {
    return apiClient.delete(`/v1/chat/sessions/${sessionId}`);
  },

  /**
   * 获取会话消息
   */
  async getSessionMessages(
    sessionId: string,
    params?: PaginationParams
  ): Promise<PaginatedResponse<Message>> {
    return apiClient.get<PaginatedResponse<Message>>(
      `/v1/chat/sessions/${sessionId}/messages`,
      { params }
    );
  },
};

