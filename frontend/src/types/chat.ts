/**
 * 聊天相关类型定义
 */

/**
 * 消息角色
 */
export type MessageRole = 'system' | 'user' | 'assistant' | 'tool';

/**
 * 消息内容
 */
export interface MessageContent {
  type: 'text' | 'image' | 'file' | 'tool_call';
  text?: string;
  image_url?: string;
  file_url?: string;
  tool_call_id?: string;
  tool_name?: string;
  tool_args?: Record<string, any>;
}

/**
 * 消息
 */
export interface Message {
  id: string;
  role: MessageRole;
  content: string | MessageContent;
  timestamp: Date | string;
  session_id?: string;
  user_id?: string;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
  /** 消息元数据（如 is_voice_call 等） */
  metadata?: Record<string, any>;
}

/**
 * 工具调用
 */
export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

/**
 * 聊天请求
 */
export interface ChatRequest {
  model?: string;
  messages: Array<{
    role: MessageRole;
    content: string;
  }>;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
  tools?: ToolDefinition[];
  personality_id?: string;
  session_id?: string;
  use_memory?: boolean;
  memory_options?: MemoryOptions;
}

/**
 * 工具定义
 */
export interface ToolDefinition {
  type: 'function';
  function: {
    name: string;
    description: string;
    parameters: Record<string, any>;
  };
}

/**
 * 记忆选项
 */
export interface MemoryOptions {
  include_user_memory?: boolean;
  include_ai_memory?: boolean;
  memory_limit?: number;
}

/**
 * 聊天响应
 */
export interface ChatResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: MessageRole;
      content: string;
      tool_calls?: ToolCall[];
    };
    finish_reason: string | null;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  personality?: {
    id: string;
    name: string;
  };
  memories_used?: Array<{
    type: 'user' | 'ai';
    content: string;
    similarity: number;
  }>;
  tools_called?: Array<{
    name: string;
    arguments: Record<string, any>;
    result: any;
  }>;
}

/**
 * 流式响应块
 */
export interface StreamChunk {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    delta: {
      role?: MessageRole;
      content?: string;
      tool_calls?: ToolCall[];
    };
    finish_reason: string | null;
  }>;
}

