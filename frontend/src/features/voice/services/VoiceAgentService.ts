/**
 * Voice Agent 服务
 * 
 * 核心服务，协调所有模块：
 * - ConfigManager：配置管理
 * - ToolManager：工具管理
 * - TransportStrategy：传输层策略（WebRTC/WebSocket）
 * - SessionManager：会话管理
 * - EventHandler：事件处理
 * 
 * 使用策略模式，将 WebRTC 和 WebSocket 的逻辑完全分离
 */

import { RealtimeAgent } from '@openai/agents/realtime';
import { ConfigManager } from './ConfigManager';
import { SessionManager } from './SessionManager';
import { ToolManager } from './ToolManager';
import { EventHandler, type EventHandlerCallbacks } from './EventHandler';
import { TransportStrategyFactory } from '../strategies/TransportStrategyFactory';
import type { ITransportStrategy } from '../strategies/ITransportStrategy';

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
  
  // 传输层策略（根据配置动态创建）
  private transportStrategy: ITransportStrategy | null = null;

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
   * 
   * 使用策略模式，根据配置选择 WebRTC 或 WebSocket 策略
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

      // ✅ 关键修复：每次 startCall 都重新创建 session 和 transport，确保完全初始化
      console.log('[VoiceAgentService] 重新创建 Session 和 Transport 以确保完全初始化');
      
      // 清理旧的 session 和策略
      this.sessionManager.close();
      if (this.transportStrategy) {
        this.transportStrategy.cleanup();
        this.transportStrategy = null;
      }
      
      // 1. 加载配置
      const config = await this.configManager.loadConfig();
      const transportType = config.transportType || 'webrtc';
      
      // 2. 创建传输层策略（根据配置选择 WebRTC 或 WebSocket）
      this.transportStrategy = TransportStrategyFactory.create(transportType);
      console.log(`[VoiceAgentService] 使用 ${transportType.toUpperCase()} 传输层策略`);
      
      // 3. 加载工具
      const toolInfos = await this.toolManager.getTools(this.config.personalityId, 'builtin');
      const tools = this.toolManager.convertToRealtimeFormat(toolInfos);
      
      // 4. 创建 Agent
      const agent = new RealtimeAgent({
        name: 'cozychat-agent',
        instructions: config.instructions,
        voice: config.voice,
        tools: tools.length > 0 ? (tools as any) : undefined,
      });

      // 5. 使用策略创建 Session
      const session = await this.transportStrategy.createSession(agent, {
        apiKey: config.apiKey,
        model: config.model,
        baseUrl: config.baseUrl,
        wsUrl: config.wsUrl,
        inputAudioTranscription: config.inputAudioTranscription,
        websocket: config.websocket,
      });

      // 6. 设置事件处理器
      this.eventHandler.cleanup();
      this.eventHandler.setSession(session);
      
      const callbacks = this.config.callbacks || {};
      console.log('[VoiceAgentService] 设置回调函数:', {
        hasOnUserTranscript: !!callbacks.onUserTranscript,
        hasOnAssistantTranscript: !!callbacks.onAssistantTranscript,
        hasOnToolCall: !!callbacks.onToolCall,
        hasOnToolResult: !!callbacks.onToolResult,
      });
      
      this.eventHandler.setCallbacks(callbacks);
      
      // ✅ 关键修复：在 connect() 之前设置事件监听器！
      if (tools.length > 0) {
        this.eventHandler.setupToolCallListeners();
      }
      this.eventHandler.setupUserTranscriptListener();
      this.eventHandler.setupAssistantTranscriptListener();
      console.log('[VoiceAgentService] 事件处理器已设置（在连接前）');
      
      // 7. 连接 Session
      console.log('[VoiceAgentService] 正在连接 RealtimeSession...', {
        model: config.model,
        inputAudioTranscription: config.inputAudioTranscription,
      });
      
      await session.connect({
        apiKey: config.apiKey,
        model: config.model,
      } as any);
      
      console.log('[VoiceAgentService] RealtimeSession 已连接到 OpenAI');
      
      // ✅ 关键修复：等待一小段时间，确保历史记录事件能够正确触发
      await new Promise(resolve => setTimeout(resolve, 200));

      // 8. 初始化音频可视化（使用策略）
      await this.transportStrategy.initAudioVisualization(
        session,
        () => {
          // 频率数据回调将由 Hook 层订阅
        },
        () => {
          // 频率数据回调将由 Hook 层订阅
        }
      );
      
      // 9. 启动音频可视化
      this.transportStrategy.startAudioVisualization();

      // ✅ 通话启动成功，设置 Service 层内部状态
      this.isCalling = true;
      
      console.log('[VoiceAgentService] 通话已开始（Service 层）');
    } catch (error) {
      // 如果失败，恢复状态
      this.isCalling = false;
      if (this.transportStrategy) {
        this.transportStrategy.stopAudioVisualization();
      }
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

    // ✅ 关键修复：先立即停止通话（停止音频播放）
    if (this.transportStrategy?.stopCall) {
      this.transportStrategy.stopCall();
    } else {
      // 如果没有 stopCall 方法，至少停止音频可视化
      this.transportStrategy?.stopAudioVisualization();
    }

    // 关闭 RealtimeSession 连接
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
   * 获取音频可视化器
   * 
   * 注意：音频可视化器由策略管理，这里返回策略的音频可视化器
   * 为了保持接口兼容，返回策略对象本身（如果它实现了 getCurrentUserFrequencyData 等方法）
   */
  getAudioVisualizer(): any {
    // 返回策略对象，Hook 层可以通过策略获取频率数据
    return this.transportStrategy;
  }

  /**
   * 获取用户音频频率数据
   * 
   * 从策略中获取当前的用户音频频率数据
   */
  getUserFrequencyData(): Uint8Array | null {
    if (this.transportStrategy?.getCurrentUserFrequencyData) {
      return this.transportStrategy.getCurrentUserFrequencyData();
    }
    return null;
  }

  /**
   * 获取助手音频频率数据
   * 
   * 从策略中获取当前的助手音频频率数据
   */
  getAssistantFrequencyData(): Uint8Array | null {
    if (this.transportStrategy?.getCurrentAssistantFrequencyData) {
      return this.transportStrategy.getCurrentAssistantFrequencyData();
    }
    return null;
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
    if (this.transportStrategy) {
      this.transportStrategy.stopAudioVisualization();
      this.transportStrategy.cleanup();
      this.transportStrategy = null;
    }

    // 清理事件处理器
    this.eventHandler.cleanup();

    // 关闭 session
    this.sessionManager.close();

    this.isConnected = false;
    this.isCalling = false;

    console.log('[VoiceAgentService] 所有资源已清理');
  }
}
