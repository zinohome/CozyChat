/**
 * 会话相关类型定义
 */

/**
 * 消息信息
 */
export interface MessageInfo {
  id: string;
  role: string;
  content: string;
  created_at: string;
  metadata?: Record<string, any>;
}

/**
 * 会话
 */
export interface Session {
  id?: string; // 列表接口可能使用 session_id
  session_id?: string; // 详情接口使用 session_id
  user_id?: string;
  title: string;
  personality_id?: string;
  personality_name?: string;
  message_count?: number;
  total_messages?: number; // 详情接口返回
  messages?: MessageInfo[]; // 详情接口返回的消息列表
  created_at: Date | string;
  updated_at?: Date | string;
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

