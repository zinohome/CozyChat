/**
 * 会话相关类型定义
 */

/**
 * 会话
 */
export interface Session {
  id: string;
  user_id: string;
  title: string;
  personality_id?: string;
  personality_name?: string;
  message_count: number;
  created_at: Date | string;
  updated_at: Date | string;
  last_message_at?: Date | string;
  is_archived?: boolean;
}

/**
 * 创建会话请求
 */
export interface CreateSessionRequest {
  title?: string;
  personality_id?: string;
}

/**
 * 更新会话请求
 */
export interface UpdateSessionRequest {
  title?: string;
  personality_id?: string;
  is_archived?: boolean;
}

