import { apiClient } from './api';

/**
 * OpenAI配置
 */
export interface OpenAIConfig {
  /** OpenAI API密钥 */
  api_key: string;
  /** OpenAI API基础URL */
  base_url: string;
}

/**
 * Realtime Token
 */
export interface RealtimeToken {
  /** Ephemeral client key (token) */
  token: string;
  /** WebSocket URL（用于 WebSocket 传输层） */
  url: string;
  /** Model name */
  model: string;
}

/**
 * 配置API服务
 *
 * 封装配置相关的API调用。
 */
export const configApi = {
  /**
   * 获取 OpenAI 配置
   *
   * 返回 OpenAI API key 和 base URL，供前端使用 OpenAI Agents SDK 连接 Realtime API。
   *
   * @returns OpenAI配置信息
   */
  async getOpenAIConfig(): Promise<OpenAIConfig> {
    return apiClient.get<OpenAIConfig>('/v1/config/openai-config');
  },

  /**
   * 获取 Realtime API 的 ephemeral client key (token)
   *
   * 这个端点会调用后端生成 ephemeral client key，用于前端连接 OpenAI Realtime API。
   *
   * @returns Realtime token 信息
   */
  async getRealtimeToken(): Promise<RealtimeToken> {
    return apiClient.post<RealtimeToken>('/v1/config/realtime-token');
  },
};

