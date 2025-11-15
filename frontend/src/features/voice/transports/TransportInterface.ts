/**
 * 传输层接口
 * 
 * 定义了 WebRTC 和 WebSocket 传输层的统一接口
 */

/**
 * 传输层类型
 */
export type TransportType = 'webrtc' | 'websocket';

/**
 * 传输层状态
 */
export type TransportStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

/**
 * 传输层接口
 */
export interface ITransport {
  /**
   * 传输层类型
   */
  type: TransportType;

  /**
   * 当前状态
   */
  status: TransportStatus;

  /**
   * 连接传输层
   * 
   * @param config - 连接配置
   */
  connect(config: Record<string, any>): Promise<void>;

  /**
   * 断开连接
   */
  disconnect(): void;

  /**
   * 获取用户音频流（用于可视化）
   * 
   * @returns 用户的 MediaStream
   */
  getUserMediaStream(): MediaStream | null;

  /**
   * 获取助手音频流（用于可视化）
   * 
   * @returns 助手的音频元素或 MediaStream
   */
  getAssistantAudioStream(): HTMLAudioElement | MediaStream | null;

  /**
   * 监听事件
   * 
   * @param event - 事件名称
   * @param callback - 回调函数
   */
  on(event: string, callback: (...args: any[]) => void): void;

  /**
   * 取消监听事件
   * 
   * @param event - 事件名称
   * @param callback - 回调函数
   */
  off(event: string, callback: (...args: any[]) => void): void;

  /**
   * 获取底层传输对象（OpenAIRealtimeWebRTC 或 OpenAIRealtimeWebSocket）
   */
  getUnderlyingTransport(): any;
}

