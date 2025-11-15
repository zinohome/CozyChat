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
   * 更新回调函数
   * 
   * 当 callbacks 变化时，需要更新 EventHandler 的回调
   */
  updateCallbacks(callbacks: EventHandlerCallbacks): void {
    this.config.callbacks = callbacks;
    // 如果 EventHandler 已经设置，立即更新
    if (this.eventHandler) {
      this.eventHandler.setCallbacks(callbacks);
      console.log('[VoiceAgentService] 回调函数已更新');
    }
  }

  /**
   * 连接 Voice Agent
   * 
   * 注意：这个方法只做初始化工作，不创建 transport 和 session
   * transport 和 session 在 startCall() 中创建，确保每次通话都是全新的
   */
  async connect(): Promise<void> {
    if (this.isConnected) {
      console.warn('[VoiceAgentService] 已连接，无需重复连接');
      return;
    }

    try {
      console.log('[VoiceAgentService] 开始连接（仅初始化）...');

      // ✅ 只做初始化工作，不创建 transport 和 session
      // transport 和 session 在 startCall() 中创建，确保每次通话都是全新的
      
      // 预加载配置（可选，用于验证配置是否正确）
      // const config = await this.configManager.loadConfig();
      // console.log('[VoiceAgentService] 配置已预加载');

      this.isConnected = true;
      console.log('[VoiceAgentService] 连接成功（已初始化）');
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

      // 注意：不立即设置 isCalling，等音频可视化初始化完成后再设置
      // 避免UI状态提前显示"可以说话"

      // ✅ 关键修复：每次 startCall 都重新创建 session 和 transport，确保完全初始化
      // 这样可以避免第二次通话时的问题
      console.log('[VoiceAgentService] 重新创建 Session 和 Transport 以确保完全初始化');
      
      // 清理旧的 session
      this.sessionManager.close();
      
      // ✅ 关键修复：重新创建 transport，确保 WebRTC 连接是全新的
      // 因为 session.close() 可能会关闭底层的 WebRTC 连接
      if (this.transport) {
        console.log('[VoiceAgentService] 断开旧的 Transport');
        this.transport.disconnect();
        this.transport = null;
      }
      
      // 重新创建 transport
      const config = await this.configManager.loadConfig();
      this.transport = TransportFactory.create('webrtc', {
        baseUrl: config.baseUrl,
      });
      await this.transport.connect({});
      console.log('[VoiceAgentService] 新的 Transport 已创建并连接');
      
      // 重新创建 session（使用新的 transport）
      const toolInfos = await this.toolManager.getTools(this.config.personalityId, 'builtin');
      const tools = this.toolManager.convertToRealtimeFormat(toolInfos);
      
      // 创建新的 agent
      const agent = new RealtimeAgent({
        name: 'cozychat-agent',
        instructions: config.instructions,
        voice: config.voice,
        tools: tools.length > 0 ? (tools as any) : undefined,
      });

      // 创建新的 session
      const session = await this.sessionManager.createSession(agent, this.transport, {
        apiKey: config.apiKey,
        model: config.model,
        inputAudioTranscription: config.inputAudioTranscription,
      });

      // ✅ 关键修复：先清理旧的事件监听器，再设置新的
      this.eventHandler.cleanup();
      
      // ✅ 关键修复：设置新的 session 和回调函数
      this.eventHandler.setSession(session);
      
      // ✅ 关键修复：使用最新的回调函数（确保不是旧的引用）
      const callbacks = this.config.callbacks || {};
      console.log('[VoiceAgentService] 设置回调函数:', {
        hasOnUserTranscript: !!callbacks.onUserTranscript,
        hasOnAssistantTranscript: !!callbacks.onAssistantTranscript,
        hasOnToolCall: !!callbacks.onToolCall,
        hasOnToolResult: !!callbacks.onToolResult,
        callbacksObject: callbacks, // 打印完整对象以便调试
      });
      
      this.eventHandler.setCallbacks(callbacks);
      
      // ✅ 关键修复：在 connect() 之前设置事件监听器！
      // 参考旧版本代码：事件监听器必须在 connect() 之前设置，才能捕获所有事件
      if (tools.length > 0) {
        this.eventHandler.setupToolCallListeners();
      }
      this.eventHandler.setupUserTranscriptListener();
      this.eventHandler.setupAssistantTranscriptListener();
      console.log('[VoiceAgentService] 事件处理器已设置（在连接前）');
      
      console.log('[VoiceAgentService] 正在连接 RealtimeSession...', {
        model: config.model,
        inputAudioTranscription: config.inputAudioTranscription,
      });
      
      // ✅ 关键修复：连接 session（事件监听器已在连接前设置）
      await session.connect({
        apiKey: config.apiKey,
        model: config.model,
      } as any);
      
      console.log('[VoiceAgentService] RealtimeSession 已连接到 OpenAI');
      
      // ✅ 关键修复：等待一小段时间，确保历史记录事件能够正确触发
      // 新连接的 session 需要时间初始化历史记录
      await new Promise(resolve => setTimeout(resolve, 200));

      // 获取用户和助手的音频流
      const userStream = this.transport?.getUserMediaStream();
      const assistantAudioElement = this.transport?.getAssistantAudioStream();

      if (!userStream) {
        throw new Error('无法获取用户音频流');
      }

      // 初始化音频可视化
      if (userStream) {
        await this.audioVisualizer.initUserVisualization(
          userStream,
          () => {
            // 频率数据回调将由 Hook 层订阅
          }
        );
        this.audioVisualizer.startUserFrequencyExtraction();
      }

      if (assistantAudioElement instanceof HTMLAudioElement) {
        this.audioVisualizer.initAssistantVisualization(
          assistantAudioElement,
          () => {
            // 频率数据回调将由 Hook 层订阅
          }
        );
        this.audioVisualizer.startAssistantFrequencyExtraction();
      }

      // ✅ 通话启动成功，设置 Service 层内部状态（用于内部逻辑判断）
      // 注意：UI状态由 Hook 层的 isCalling 控制
      this.isCalling = true;
      this.audioVisualizer.setCallingState(true);
      
      console.log('[VoiceAgentService] 通话已开始（Service 层）');
    } catch (error) {
      // 如果失败，恢复状态
      this.isCalling = false;
      this.audioVisualizer.setCallingState(false);
      console.error('[VoiceAgentService] 开始通话失败:', error);
      throw error;
    }
  }

  /**
   * 结束通话
   * 
   * 注意：只结束当前通话，不释放 Transport 和 mediaStream
   * 这样可以支持多次 startCall() → endCall() → startCall()
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

    // 关闭 RealtimeSession 连接（这会停止AI语音播放）
    // 注意：只是关闭连接，session 对象还在，可以重新 connect
    this.sessionManager.close();

    this.isCalling = false;
    console.log('[VoiceAgentService] 通话已结束（Transport 保持连接，可重新开始）');
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
   * 清理所有资源（完全断开）
   * 
   * 注意：这会释放所有资源，包括 Transport 和 mediaStream
   * 之后需要重新调用 connect() 才能使用
   */
  private cleanup(): void {
    console.log('[VoiceAgentService] 开始清理所有资源');

    // 停止音频可视化
    this.audioVisualizer.setCallingState(false);
    this.audioVisualizer.stopFrequencyExtraction();

    // 清理音频可视化资源
    this.audioVisualizer.cleanup();

    // 清理事件处理器
    this.eventHandler.cleanup();

    // 关闭 session
    this.sessionManager.close();

    // 断开 transport（这会释放 mediaStream）
    if (this.transport) {
      this.transport.disconnect();
      this.transport = null;
    }

    this.isConnected = false;
    this.isCalling = false;

    console.log('[VoiceAgentService] 所有资源已清理');
  }
}

