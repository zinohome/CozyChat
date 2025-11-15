/**
 * WebRTC 传输层策略
 * 
 * 负责处理 WebRTC 传输层的所有逻辑：
 * - 创建 WebRTC transport
 * - 管理音频流
 * - 初始化音频可视化
 */

import { RealtimeAgent, RealtimeSession, OpenAIRealtimeWebRTC } from '@openai/agents/realtime';
import type { ITransportStrategy, TransportStrategyConfig } from './ITransportStrategy';
import { AudioVisualizer } from '../visualization/AudioVisualizer';

/**
 * WebRTC 传输层策略类
 */
export class WebRTCStrategy implements ITransportStrategy {
  readonly type = 'webrtc' as const;

  private transport: OpenAIRealtimeWebRTC | null = null;
  private mediaStream: MediaStream | null = null;
  private audioElement: HTMLAudioElement | null = null;
  private audioVisualizer: AudioVisualizer;
  private onUserFrequencyData: ((data: Uint8Array) => void) | null = null;
  private onAssistantFrequencyData: ((data: Uint8Array) => void) | null = null;

  constructor() {
    this.audioVisualizer = new AudioVisualizer();
  }

  /**
   * 创建并连接 RealtimeSession
   */
  async createSession(
    agent: RealtimeAgent,
    config: TransportStrategyConfig
  ): Promise<RealtimeSession> {
    console.log('[WebRTCStrategy] 创建 WebRTC Session...');

    // 1. 创建用户音频流
    if (!this.mediaStream) {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 24000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
    }

    // 2. 创建助手音频元素
    // 注意：OpenAIRealtimeWebRTC SDK 内部会自动处理音频播放
    // 我们的 audioElement 仅用于可视化（波形显示），必须静音避免重复播放
    if (!this.audioElement) {
      this.audioElement = new Audio();
      this.audioElement.autoplay = false; // 不自动播放，SDK内部播放
      this.audioElement.muted = true;     // 必须静音，避免重复播放和回声
    }

    // 3. 构建 WebRTC 端点 URL
    let baseUrl = config.baseUrl;
    if (baseUrl.endsWith('/v1')) {
      baseUrl = baseUrl.slice(0, -3);
    } else if (baseUrl.endsWith('/v1/')) {
      baseUrl = baseUrl.slice(0, -4);
    }
    baseUrl = baseUrl.replace(/\/$/, '');
    const webrtcEndpoint = `${baseUrl}/v1/realtime/calls`;

    // 4. 创建 OpenAIRealtimeWebRTC 传输层
    this.transport = new OpenAIRealtimeWebRTC({
      baseUrl: webrtcEndpoint,
      mediaStream: this.mediaStream,
      audioElement: this.audioElement,
    });

    // 5. 创建 RealtimeSession
    const session = new RealtimeSession(agent, {
      apiKey: config.apiKey,
      transport: this.transport,
      model: config.model,
    });

    console.log('[WebRTCStrategy] WebRTC Session 已创建');
    return session;
  }

  /**
   * 初始化音频可视化
   */
  async initAudioVisualization(
    _session: RealtimeSession,
    onUserFrequencyData: (data: Uint8Array) => void,
    onAssistantFrequencyData: (data: Uint8Array) => void
  ): Promise<void> {
    if (!this.mediaStream || !this.audioElement) {
      throw new Error('WebRTC 音频流未初始化');
    }

    this.onUserFrequencyData = onUserFrequencyData;
    this.onAssistantFrequencyData = onAssistantFrequencyData;

    // 初始化用户音频可视化
    await this.audioVisualizer.initUserVisualization(
      this.mediaStream,
      onUserFrequencyData
    );

    // 初始化助手音频可视化
    this.audioVisualizer.initAssistantVisualization(
      this.audioElement,
      onAssistantFrequencyData
    );

    console.log('[WebRTCStrategy] 音频可视化已初始化');
  }

  /**
   * 开始音频可视化
   */
  startAudioVisualization(): void {
    this.audioVisualizer.setCallingState(true);
    this.audioVisualizer.startUserFrequencyExtraction();
    this.audioVisualizer.startAssistantFrequencyExtraction();
    console.log('[WebRTCStrategy] 音频可视化已启动');
  }

  /**
   * 停止音频可视化
   */
  stopAudioVisualization(): void {
    this.audioVisualizer.setCallingState(false);
    this.audioVisualizer.stopFrequencyExtraction();
    console.log('[WebRTCStrategy] 音频可视化已停止');
  }

  /**
   * 立即停止通话（停止音频播放）
   * 
   * 关闭 WebRTC transport 以立即停止音频播放
   */
  stopCall(): void {
    console.log('[WebRTCStrategy] 立即停止通话...');

    // ✅ 关键修复：先停止用户音频流的所有轨道（停止输入）
    // 这样可以立即停止向服务器发送音频数据
    if (this.mediaStream) {
      try {
        this.mediaStream.getTracks().forEach((track) => {
          track.stop();
          console.log('[WebRTCStrategy] 已停止音频轨道:', track.kind);
        });
        // 注意：不设置为 null，因为 cleanup() 中会处理
      } catch (error) {
        console.error('[WebRTCStrategy] 停止音频轨道失败:', error);
      }
    }

    // ✅ 关键修复：关闭 WebRTC transport 以立即停止音频播放
    if (this.transport) {
      try {
        // OpenAIRealtimeWebRTC 可能有 close() 方法
        if (typeof (this.transport as any).close === 'function') {
          (this.transport as any).close();
          console.log('[WebRTCStrategy] WebRTC transport 已关闭');
        }
        // 或者尝试断开连接
        if (typeof (this.transport as any).disconnect === 'function') {
          (this.transport as any).disconnect();
          console.log('[WebRTCStrategy] WebRTC transport 已断开');
        }
        // 尝试访问内部的 RTCPeerConnection 并关闭
        if ((this.transport as any).peerConnection) {
          const pc = (this.transport as any).peerConnection;
          if (pc && typeof pc.close === 'function') {
            pc.close();
            console.log('[WebRTCStrategy] RTCPeerConnection 已关闭');
          }
        }
      } catch (error) {
        console.error('[WebRTCStrategy] 关闭 transport 失败:', error);
      }
    }

    // 停止音频可视化
    this.stopAudioVisualization();

    // ✅ 关键修复：暂停并清理音频元素播放
    // 注意：虽然 audioElement 是静音的，但清理它可以确保没有残留的音频数据
    if (this.audioElement) {
      try {
        this.audioElement.pause();
        this.audioElement.src = '';
        this.audioElement.srcObject = null; // 移除媒体流引用
        console.log('[WebRTCStrategy] 音频元素已暂停并清理');
      } catch (error) {
        console.error('[WebRTCStrategy] 暂停音频元素失败:', error);
      }
    }

    console.log('[WebRTCStrategy] 通话已立即停止');
  }

  /**
   * 清理资源
   */
  cleanup(): void {
    console.log('[WebRTCStrategy] 清理资源...');

    // 停止音频可视化
    this.stopAudioVisualization();
    this.audioVisualizer.cleanup();

    // 停止音频流
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    // 清理音频元素
    if (this.audioElement) {
      this.audioElement.pause();
      this.audioElement.src = '';
      this.audioElement = null;
    }

    // 清理 transport
    this.transport = null;

    this.onUserFrequencyData = null;
    this.onAssistantFrequencyData = null;

    console.log('[WebRTCStrategy] 资源已清理');
  }

  /**
   * 获取用户音频流（用于外部访问）
   */
  getUserMediaStream(): MediaStream | null {
    return this.mediaStream;
  }

  /**
   * 获取助手音频元素（用于外部访问）
   */
  getAssistantAudioElement(): HTMLAudioElement | null {
    return this.audioElement;
  }

  /**
   * 获取当前用户音频频率数据（用于可视化）
   */
  getCurrentUserFrequencyData(): Uint8Array | null {
    return this.audioVisualizer.getCurrentUserFrequencyData();
  }

  /**
   * 获取当前助手音频频率数据（用于可视化）
   */
  getCurrentAssistantFrequencyData(): Uint8Array | null {
    return this.audioVisualizer.getCurrentAssistantFrequencyData();
  }
}

