/**
 * Voice Agent 服务
 * 
 * 核心服务，协调所有模块：
 * - ConfigManager：配置管理
 * - ToolManager：工具管理
 * - TransportFactory：传输层创建
 * - SessionManager：会话管理
 * - AudioVisualizer：音频可视化
 * - EventHandler：事件处理
 */

import { RealtimeAgent } from '@openai/agents/realtime';
import { ConfigManager, type VoiceAgentConfig } from './ConfigManager';
import { SessionManager } from './SessionManager';
import { ToolManager } from './ToolManager';
import { EventHandler, type EventHandlerCallbacks } from './EventHandler';
import { TransportFactory } from '../transports/TransportFactory';
import { AudioVisualizer } from '../visualization/AudioVisualizer';
import type { ITransport } from '../transports/TransportInterface';

/**
 * Voice Agent 服务配置
 */
export interface VoiceAgentServiceConfig {
  /** 会话ID */
  sessionId?: string;
  /** 人格ID */
  personalityId?: string;
  /** 回调函数 */
  callbacks?: EventHandlerCallbacks;
}

/**
 * Voice Agent 服务类
 */
export class VoiceAgentService {
  // 配置
  private config: VoiceAgentServiceConfig;

  // 各模块实例
  private configManager: ConfigManager;
  private sessionManager: SessionManager;
  private toolManager: ToolManager;
  private eventHandler: EventHandler;
  private audioVisualizer: AudioVisualizer;
  private transport: ITransport | null = null;

  // 状态
  private isConnected: boolean = false;
  private isCalling: boolean = false;

  constructor(config: VoiceAgentServiceConfig) {
    this.config = config;

    // 初始化各模块
    this.configManager = new ConfigManager(config.personalityId);
    this.sessionManager = new SessionManager();
    this.toolManager = new ToolManager();
    this.eventHandler = new EventHandler();
    this.audioVisualizer = new AudioVisualizer();

    console.log('[VoiceAgentService] 服务已创建');
  }

  /**
   * 连接 Voice Agent
   */
  async connect(): Promise<void> {
    if (this.isConnected) {
      console.warn('[VoiceAgentService] 已连接，无需重复连接');
      return;
    }

    try {
      console.log('[VoiceAgentService] 开始连接...');

      // 1. 加载配置
      const config: VoiceAgentConfig = await this.configManager.loadConfig();

      // 2. 加载工具列表
      const toolInfos = await this.toolManager.getTools(this.config.personalityId, 'builtin');
      const tools = this.toolManager.convertToRealtimeFormat(toolInfos);
      console.log(`[VoiceAgentService] 工具已加载: ${tools.length} 个`);

      // 3. 创建 RealtimeAgent
      const agent = new RealtimeAgent({
        name: 'cozychat-agent',
        instructions: config.instructions,
        voice: config.voice,
        tools: tools.length > 0 ? tools : undefined,
      });
      console.log('[VoiceAgentService] RealtimeAgent 已创建');

      // 4. 创建传输层（WebRTC）
      this.transport = TransportFactory.create('webrtc', {
        baseUrl: config.baseUrl,
      });

      // 连接传输层
      await this.transport.connect({});
      console.log('[VoiceAgentService] 传输层已连接');

      // 5. 创建 RealtimeSession
      const session = await this.sessionManager.createSession(agent, this.transport, {
        apiKey: config.apiKey,
        model: config.model,
      });

      // 6. 设置事件处理器
      this.eventHandler.setSession(session);
      this.eventHandler.setCallbacks(this.config.callbacks || {});
      
      // 设置工具调用监听（如果有工具）
      if (tools.length > 0) {
        this.eventHandler.setupToolCallListeners();
      }

      // 设置转录监听
      this.eventHandler.setupUserTranscriptListener();
      this.eventHandler.setupAssistantTranscriptListener();
      console.log('[VoiceAgentService] 事件处理器已设置');

      this.isConnected = true;
      console.log('[VoiceAgentService] 连接成功');
    } catch (error) {
      console.error('[VoiceAgentService] 连接失败:', error);
      this.cleanup();
      throw error;
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    console.log('[VoiceAgentService] 断开连接');
    this.cleanup();
  }

  /**
   * 开始通话
   */
  async startCall(): Promise<void> {
    if (!this.isConnected) {
      throw new Error('未连接，无法开始通话');
    }

    if (this.isCalling) {
      console.warn('[VoiceAgentService] 已在通话中');
      return;
    }

    try {
      console.log('[VoiceAgentService] 开始通话');

      // 获取用户和助手的音频流
      const userStream = this.transport?.getUserMediaStream();
      const assistantAudioElement = this.transport?.getAssistantAudioStream();

      if (!userStream) {
        throw new Error('无法获取用户音频流');
      }

      // 初始化音频可视化
      this.audioVisualizer.setCallingState(true);
      
      if (userStream) {
        await this.audioVisualizer.initUserVisualization(
          userStream,
          (data) => {
            // 频率数据回调将由 Hook 层订阅
          }
        );
        this.audioVisualizer.startUserFrequencyExtraction();
      }

      if (assistantAudioElement instanceof HTMLAudioElement) {
        this.audioVisualizer.initAssistantVisualization(
          assistantAudioElement,
          (data) => {
            // 频率数据回调将由 Hook 层订阅
          }
        );
        this.audioVisualizer.startAssistantFrequencyExtraction();
      }

      this.isCalling = true;
      console.log('[VoiceAgentService] 通话已开始');
    } catch (error) {
      console.error('[VoiceAgentService] 开始通话失败:', error);
      throw error;
    }
  }

  /**
   * 结束通话
   */
  endCall(): void {
    if (!this.isCalling) {
      console.warn('[VoiceAgentService] 未在通话中');
      return;
    }

    console.log('[VoiceAgentService] 结束通话');

    // 停止音频可视化
    this.audioVisualizer.setCallingState(false);
    this.audioVisualizer.stopFrequencyExtraction();

    this.isCalling = false;
    console.log('[VoiceAgentService] 通话已结束');
  }

  /**
   * 获取连接状态
   */
  getConnectionState(): { isConnected: boolean; isCalling: boolean } {
    return {
      isConnected: this.isConnected,
      isCalling: this.isCalling,
    };
  }

  /**
   * 获取 AudioVisualizer 实例
   */
  getAudioVisualizer(): AudioVisualizer {
    return this.audioVisualizer;
  }

  /**
   * 清理资源
   */
  private cleanup(): void {
    // 结束通话
    if (this.isCalling) {
      this.endCall();
    }

    // 清理事件处理器
    this.eventHandler.cleanup();

    // 关闭 session
    this.sessionManager.close();

    // 断开传输层
    if (this.transport) {
      this.transport.disconnect();
      this.transport = null;
    }

    // 清理音频可视化
    this.audioVisualizer.cleanup();

    this.isConnected = false;

    console.log('[VoiceAgentService] 资源已清理');
  }
}

