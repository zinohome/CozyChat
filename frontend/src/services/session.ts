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
    // 后端返回格式: { sessions: SessionListItem[], total, page, page_size }
    // SessionListItem: { session_id, personality_id, personality_name, title, message_count, last_message_at, created_at }
    // 前端期望格式: { items: Session[], total, page, page_size, has_next, has_prev }
    // 默认按 last_message_at 降序排列，最新的在最上面
    const response = await apiClient.get<{
      sessions: Array<{
        session_id: string;
        personality_id: string;
        personality_name?: string;
        title: string;
        message_count: number;
        last_message_at?: string;
        created_at: string;
      }>;
      total: number;
      page: number;
      page_size: number;
    }>('/v1/sessions', {
      params: {
        ...params,
        sort: 'last_message_at',  // 按最后消息时间排序
        order: 'desc',  // 降序，最新的在最上面
      },
    });
    
    // 转换数据格式：将 session_id 映射为 id
    const sessions: Session[] = (response.sessions || []).map((item) => ({
      id: item.session_id,
      session_id: item.session_id,
      title: item.title,
      personality_id: item.personality_id,
      personality_name: item.personality_name,
      message_count: item.message_count,
      last_message_at: item.last_message_at,
      created_at: item.created_at,
    }));
    
    // 计算分页信息
    const page = response.page || 1;
    const pageSize = response.page_size || 10;
    const total = response.total || 0;
    
    return {
      items: sessions,
      total,
      page,
      page_size: pageSize,
      has_next: page * pageSize < total,
      has_prev: page > 1,
    };
  },

  /**
   * 获取单个会话
   */
  async getSession(sessionId: string): Promise<Session> {
    try {
      // 验证 UUID 格式
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
      if (!uuidRegex.test(sessionId)) {
        console.warn(`Invalid session ID format: ${sessionId}`);
        throw new Error(`Invalid session ID format: ${sessionId}`);
      }
      
      return await apiClient.get<Session>(`/v1/sessions/${sessionId}`);
    } catch (error: any) {
      // 如果是404错误（会话不存在或已删除），返回一个默认的会话对象，避免抛出错误
      if (error?.response?.status === 404) {
        console.warn(`Session ${sessionId} not found, returning empty session`);
        return {
          id: sessionId,
          session_id: sessionId,
          title: '会话不存在',
          personality_id: 'default',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          message_count: 0,
          total_messages: 0,
          messages: [],
          metadata: {},
        } as Session;
      }
      // 如果是400错误（无效的session ID格式），返回一个默认的会话对象
      if (error?.response?.status === 400) {
        console.warn(`Invalid session ID format: ${sessionId}, returning empty session`);
        return {
          id: sessionId,
          session_id: sessionId,
          title: '会话不存在',
          personality_id: 'default',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          message_count: 0,
          total_messages: 0,
          messages: [],
          metadata: {},
        } as Session;
      }
      throw error;
    }
  },

  /**
   * 创建会话
   */
  async createSession(request: CreateSessionRequest): Promise<Session> {
    // 后端返回格式: { session_id, personality_id, title, created_at }
    // 前端期望格式: Session { id, session_id, title, personality_id, created_at, ... }
    const response = await apiClient.post<{
      session_id: string;
      personality_id: string;
      title: string;
      created_at: string;
    }>('/v1/sessions', request);
    
    // 转换为前端期望的格式
    return {
      id: response.session_id,
      session_id: response.session_id,
      title: response.title,
      personality_id: response.personality_id,
      created_at: response.created_at,
      message_count: 0,
    };
  },

  /**
   * 更新会话
   */
  async updateSession(
    sessionId: string,
    request: UpdateSessionRequest
  ): Promise<Session> {
    // 后端返回格式: { session_id, title, updated_at }
    // 前端期望格式: Session { id, session_id, title, personality_id, created_at, updated_at, ... }
    const response = await apiClient.put<{
      session_id: string;
      title: string;
      updated_at: string;
    }>(`/v1/sessions/${sessionId}`, request);
    
    // 尝试获取原有会话信息以保留其他字段，如果失败则只返回更新后的字段
    try {
      const existingSession = await this.getSession(sessionId);
      // 合并更新后的字段和原有字段
      return {
        ...existingSession,
        id: response.session_id,
        session_id: response.session_id,
        title: response.title,
        updated_at: response.updated_at,
      };
    } catch (error) {
      // 如果获取失败（如会话刚创建），只返回更新后的字段
      console.warn('Failed to get existing session, returning update response only:', error);
      return {
        id: response.session_id,
        session_id: response.session_id,
        title: response.title,
        updated_at: response.updated_at,
        created_at: new Date().toISOString(),
        message_count: 0,
      };
    }
  },

  /**
   * 删除会话
   */
  async deleteSession(sessionId: string): Promise<void> {
    return apiClient.delete(`/v1/sessions/${sessionId}`);
  },

  /**
   * 获取会话消息
   * 
   * 注意：后端会话详情接口会返回消息列表，这里直接获取会话详情
   */
  async getSessionMessages(
    sessionId: string,
    params?: PaginationParams
  ): Promise<PaginatedResponse<Message>> {
    // 后端会话详情接口返回的消息列表
    const session = await apiClient.get<Session>(`/v1/sessions/${sessionId}`);
    const messages = session.messages || [];
    const total = session.total_messages || 0;
    const page = params?.page || 1;
    const pageSize = params?.page_size || messages.length || 10;
    
    // 将 MessageInfo 转换为 Message 格式
    const messageItems: Message[] = messages.map((msg) => ({
      id: msg.id,
      role: msg.role as 'user' | 'assistant' | 'system',
      content: msg.content,
      created_at: msg.created_at,
      metadata: msg.metadata,
    }));
    
    // 转换为分页响应格式
    return {
      items: messageItems,
      total,
      page,
      page_size: pageSize,
      has_next: false, // 后端详情接口返回所有消息，不支持分页
      has_prev: false,
    };
  },
};

