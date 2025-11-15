/**
 * 会话管理器
 * 
 * 负责：
 * - 封装 RealtimeSession 创建逻辑
 * - 管理 session 生命周期
 * - 提供 session 访问接口
 */

import { RealtimeAgent, RealtimeSession } from '@openai/agents/realtime';
import type { ITransport } from '../transports/TransportInterface';

/**
 * 会话配置
 */
export interface SessionConfig {
  /** API密钥（ephemeral token） */
  apiKey: string;
  /** 模型名称 */
  model: string;
}

/**
 * 会话管理器类
 */
export class SessionManager {
  private session: RealtimeSession | null = null;

  /**
   * 创建 RealtimeSession
   * 
   * @param agent - RealtimeAgent 实例
   * @param transport - 传输层实例
   * @param config - 会话配置
   * @returns RealtimeSession 实例
   */
  async createSession(
    agent: RealtimeAgent,
    transport: ITransport,
    config: SessionConfig
  ): Promise<RealtimeSession> {
    try {
      console.log('[SessionManager] 创建 RealtimeSession...');

      // 创建 RealtimeSession
      // 注意：转录配置已经在后端创建 ephemeral token 时完成
      const session = new RealtimeSession(agent, {
        apiKey: config.apiKey, // 使用后端生成的 ephemeral key（已包含转录配置）
        transport: transport.getUnderlyingTransport(), // 使用传输层的底层对象
        model: config.model, // 使用后端返回的模型名称
      });

      this.session = session;

      console.log('[SessionManager] RealtimeSession 已创建');
      return session;
    } catch (error) {
      console.error('[SessionManager] 创建 session 失败:', error);
      throw error;
    }
  }

  /**
   * 获取当前 session
   */
  getSession(): RealtimeSession | null {
    return this.session;
  }

  /**
   * 关闭 session
   */
  close(): void {
    if (this.session) {
      try {
        this.session.close();
        console.log('[SessionManager] Session 已关闭');
      } catch (error) {
        console.error('[SessionManager] 关闭 session 失败:', error);
      }
      this.session = null;
    }
  }
}

