/**
 * WebRTC 传输层
 * 
 * 实现 ITransport 接口，封装 OpenAIRealtimeWebRTC 相关逻辑
 */

import { OpenAIRealtimeWebRTC } from '@openai/agents/realtime';
import type { ITransport, TransportStatus } from './TransportInterface';

/**
 * WebRTC 传输层配置
 */
export interface WebRTCTransportConfig {
  /** 基础 URL（OpenAI API endpoint） */
  baseUrl: string;
  /** 用户媒体流 */
  mediaStream?: MediaStream;
  /** 助手音频元素 */
  audioElement?: HTMLAudioElement;
}

/**
 * WebRTC 传输层类
 */
export class WebRTCTransport implements ITransport {
  public readonly type = 'webrtc' as const;
  public status: TransportStatus = 'disconnected';

  private transport: OpenAIRealtimeWebRTC | null = null;
  private mediaStream: MediaStream | null = null;
  private audioElement: HTMLAudioElement | null = null;
  private config: WebRTCTransportConfig;

  constructor(config: WebRTCTransportConfig) {
    this.config = config;
  }

  /**
   * 连接传输层
   */
  async connect(config: Record<string, any>): Promise<void> {
    try {
      this.status = 'connecting';

      // 1. 创建用户音频流（如果未提供）
      if (!this.config.mediaStream) {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: 1,
            sampleRate: 24000,
            echoCancellation: true,
            noiseSuppression: true,
          },
        });
      } else {
        this.mediaStream = this.config.mediaStream;
      }

      // 2. 创建助手音频元素（如果未提供）
      if (!this.config.audioElement) {
        this.audioElement = new Audio();
        this.audioElement.autoplay = false;
        this.audioElement.muted = true; // 静音，只用于可视化
      } else {
        this.audioElement = this.config.audioElement;
      }

      // 3. 构建 WebRTC 端点 URL
      let baseUrl = this.config.baseUrl;
      // 移除尾部 /v1 或 /v1/
      if (baseUrl.endsWith('/v1')) {
        baseUrl = baseUrl.slice(0, -3);
      } else if (baseUrl.endsWith('/v1/')) {
        baseUrl = baseUrl.slice(0, -4);
      }
      // 确保 baseUrl 不以 / 结尾
      baseUrl = baseUrl.replace(/\/$/, '');
      // 添加 /v1/realtime/calls 路径（WebRTC 端点）
      const webrtcEndpoint = `${baseUrl}/v1/realtime/calls`;

      // 4. 创建 OpenAIRealtimeWebRTC 传输层
      this.transport = new OpenAIRealtimeWebRTC({
        baseUrl: webrtcEndpoint,
        mediaStream: this.mediaStream,
        audioElement: this.audioElement,
      });

      // 5. 等待连接建立
      await this.waitForConnection();

      this.status = 'connected';
      console.log('[WebRTCTransport] 连接成功');
    } catch (error) {
      this.status = 'error';
      console.error('[WebRTCTransport] 连接失败:', error);
      throw error;
    }
  }

  /**
   * 等待 WebRTC 连接建立
   */
  private async waitForConnection(): Promise<void> {
    if (!this.transport) {
      throw new Error('Transport not initialized');
    }

    return new Promise<void>((resolve, reject) => {
      let attempts = 0;
      const maxAttempts = 50; // 最多等待5秒（50 * 100ms）

      const checkConnection = () => {
        if (this.transport!.status === 'connected') {
          resolve();
        } else if (attempts >= maxAttempts) {
          reject(new Error('WebRTC 连接超时'));
        } else {
          attempts++;
          setTimeout(checkConnection, 100);
        }
      };

      checkConnection();
    });
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    // 停止用户音频流
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    // 停止助手音频
    if (this.audioElement) {
      this.audioElement.pause();
      this.audioElement.src = '';
      this.audioElement = null;
    }

    // 清理 transport
    if (this.transport) {
      // OpenAIRealtimeWebRTC 可能有 close() 方法
      if (typeof (this.transport as any).close === 'function') {
        (this.transport as any).close();
      }
      this.transport = null;
    }

    this.status = 'disconnected';
    console.log('[WebRTCTransport] 已断开连接');
  }

  /**
   * 获取用户音频流
   */
  getUserMediaStream(): MediaStream | null {
    return this.mediaStream;
  }

  /**
   * 获取助手音频流
   */
  getAssistantAudioStream(): HTMLAudioElement | MediaStream | null {
    return this.audioElement;
  }

  /**
   * 监听事件
   */
  on(event: string, callback: (...args: any[]) => void): void {
    if (this.transport) {
      (this.transport as any).on?.(event, callback);
    }
  }

  /**
   * 取消监听事件
   */
  off(event: string, callback: (...args: any[]) => void): void {
    if (this.transport) {
      (this.transport as any).off?.(event, callback);
    }
  }

  /**
   * 获取底层传输对象
   */
  getUnderlyingTransport(): any {
    return this.transport;
  }
}

