/**
 * 传输层策略接口
 * 
 * 定义不同传输层（WebRTC、WebSocket）的统一接口
 * 每个策略类负责处理特定传输层的所有逻辑
 */

import { RealtimeAgent, RealtimeSession } from '@openai/agents/realtime';

/**
 * 传输层策略配置
 */
export interface TransportStrategyConfig {
  /** API密钥（ephemeral token） */
  apiKey: string;
  /** 模型名称 */
  model: string;
  /** 基础 URL */
  baseUrl: string;
  /** WebSocket URL（仅用于 WebSocket） */
  wsUrl?: string;
  /** 音频转录配置 */
  inputAudioTranscription?: {
    model: string;
  };
  /** WebSocket配置（包括音频缓冲区等） */
  websocket?: {
    audio_buffer?: {
      min_size?: number;
      max_size?: number;
    };
  };
}

/**
 * 传输层策略接口
 */
export interface ITransportStrategy {
  /**
   * 传输层类型
   */
  readonly type: 'webrtc' | 'websocket';

  /**
   * 创建并连接 RealtimeSession
   * 
   * @param agent - RealtimeAgent 实例
   * @param config - 传输层配置
   * @returns RealtimeSession 实例
   */
  createSession(
    agent: RealtimeAgent,
    config: TransportStrategyConfig
  ): Promise<RealtimeSession>;

  /**
   * 初始化音频可视化
   * 
   * @param session - RealtimeSession 实例
   * @param onUserFrequencyData - 用户音频频率数据回调
   * @param onAssistantFrequencyData - 助手音频频率数据回调
   */
  initAudioVisualization(
    session: RealtimeSession,
    onUserFrequencyData: (data: Uint8Array) => void,
    onAssistantFrequencyData: (data: Uint8Array) => void
  ): Promise<void>;

  /**
   * 开始音频可视化
   */
  startAudioVisualization(): void;

  /**
   * 停止音频可视化
   */
  stopAudioVisualization(): void;

  /**
   * 立即停止通话（停止音频播放）
   * 
   * 与 cleanup() 不同，stopCall() 只停止当前通话，不释放资源
   * 用于在 endCall() 时立即停止音频播放
   */
  stopCall?(): void;

  /**
   * 清理资源
   */
  cleanup(): void;

  /**
   * 获取当前用户音频频率数据（用于可视化）
   */
  getCurrentUserFrequencyData?(): Uint8Array | null;

  /**
   * 获取当前助手音频频率数据（用于可视化）
   */
  getCurrentAssistantFrequencyData?(): Uint8Array | null;
}

