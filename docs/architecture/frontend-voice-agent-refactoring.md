# 前端语音通话架构分析与重构方案

## 1. 当前代码结构分析

### 1.1 代码组织

```
frontend/src/
├── hooks/
│   └── useVoiceAgent.ts          # 816行，包含所有语音通话逻辑
├── features/chat/components/
│   ├── EnhancedChatContainer.tsx # 集成语音通话功能
│   └── VoiceCallIndicator.tsx    # 语音通话指示器（声纹可视化）
└── services/
    └── config.ts                 # 配置API（获取token等）
```

### 1.2 当前实现的问题

#### 问题1：职责不清，代码耦合严重

`useVoiceAgent.ts` 文件过大（816行），包含了以下所有职责：

1. **传输层管理**：直接使用 `OpenAIRealtimeWebRTC`，硬编码在 hook 中
2. **配置管理**：加载 OpenAI 配置、获取 ephemeral token
3. **会话管理**：创建和管理 `RealtimeSession`
4. **音频流管理**：用户麦克风流、助手音频流
5. **音频可视化**：用户和助手的音频频率数据提取
6. **事件处理**：处理各种 SDK 事件（transcript、history等）
7. **状态管理**：连接状态、通话状态、错误状态

#### 问题2：传输层硬编码

```typescript
// 当前实现：直接使用 WebRTC
const transport = new OpenAIRealtimeWebRTC({
  baseUrl: webrtcEndpoint,
  mediaStream: userMediaStream,
  audioElement: assistantAudioElement,
});
```

**问题**：
- 无法切换传输方式（WebRTC vs WebSocket）
- 无法通过配置选择传输层
- 添加新传输方式需要修改核心 hook

#### 问题3：音频可视化逻辑混杂

音频可视化逻辑（`initUserAudioVisualization`、`initAssistantAudioVisualization`）直接写在 hook 中，应该独立出来。

#### 问题4：配置管理分散

配置加载逻辑分散在多个地方：
- `loadConfig()` 在 hook 中
- `getRealtimeToken()` 在 hook 中调用
- personality 配置通过 React Query 获取

### 1.3 当前代码依赖关系

```
EnhancedChatContainer
    ↓
useVoiceAgent (816行)
    ├── OpenAIRealtimeWebRTC (硬编码)
    ├── RealtimeSession
    ├── 音频可视化逻辑
    ├── 配置加载逻辑
    └── 事件处理逻辑
```

## 2. 重构目标

### 2.1 架构目标

1. **分离关注点**：传输层、会话管理、音频可视化、配置管理各自独立
2. **可扩展性**：支持多种传输方式（WebRTC、WebSocket），易于添加新方式
3. **可配置性**：通过配置选择传输方式
4. **可测试性**：各模块独立，易于单元测试
5. **代码清晰**：hook 只负责状态管理和协调，具体实现交给专门模块

### 2.2 目标架构

```
EnhancedChatContainer
    ↓
useVoiceAgent (简化，只负责协调)
    ├── VoiceAgentService (核心服务)
    │   ├── TransportFactory (传输层工厂)
    │   │   ├── WebRTCTransport
    │   │   └── WebSocketTransport
    │   ├── SessionManager (会话管理)
    │   └── ConfigManager (配置管理)
    ├── AudioVisualizer (音频可视化)
    └── EventHandler (事件处理)
```

## 3. 重构方案

### 3.1 目录结构设计

```
frontend/src/
├── features/voice/                    # 新增：语音功能模块
│   ├── services/
│   │   ├── VoiceAgentService.ts       # 核心服务（协调各模块）
│   │   ├── SessionManager.ts          # 会话管理
│   │   ├── ConfigManager.ts           # 配置管理
│   │   └── EventHandler.ts            # 事件处理
│   ├── transports/
│   │   ├── TransportFactory.ts        # 传输层工厂
│   │   ├── TransportInterface.ts      # 传输层接口
│   │   ├── WebRTCTransport.ts         # WebRTC 实现
│   │   └── WebSocketTransport.ts      # WebSocket 实现（待实现）
│   ├── visualization/
│   │   ├── AudioVisualizer.ts         # 音频可视化
│   │   └── FrequencyDataExtractor.ts  # 频率数据提取
│   └── types/
│       └── voice.ts                   # 语音相关类型定义
├── hooks/
│   └── useVoiceAgent.ts               # 简化后的 hook（100-200行）
└── features/chat/components/
    ├── EnhancedChatContainer.tsx      # 保持不变
    └── VoiceCallIndicator.tsx         # 保持不变
```

### 3.2 核心接口设计

#### 3.2.1 传输层接口

```typescript
// features/voice/transports/TransportInterface.ts

/**
 * 传输层接口
 * 
 * 定义所有传输层实现必须遵循的接口，支持 WebRTC 和 WebSocket 两种方式。
 */
export interface ITransport {
  /** 传输类型 */
  readonly type: 'webrtc' | 'websocket';
  
  /** 是否已连接 */
  readonly isConnected: boolean;
  
  /** 连接传输层 */
  connect(config: TransportConfig): Promise<void>;
  
  /** 断开连接 */
  disconnect(): Promise<void>;
  
  /** 发送音频数据 */
  sendAudio(audioData: ArrayBuffer): void;
  
  /** 获取用户音频流（用于可视化） */
  getUserMediaStream(): MediaStream | null;
  
  /** 获取助手音频流（用于可视化） */
  getAssistantAudioStream(): MediaStream | null;
  
  /** 事件监听 */
  on(event: string, callback: (data: any) => void): void;
  
  /** 移除事件监听 */
  off(event: string, callback: (data: any) => void): void;
}

/**
 * 传输层配置
 */
export interface TransportConfig {
  /** API Key */
  apiKey: string;
  /** 模型名称 */
  model: string;
  /** 基础URL */
  baseUrl: string;
  /** 用户音频流 */
  userMediaStream: MediaStream;
  /** 助手音频元素（用于播放） */
  assistantAudioElement: HTMLAudioElement;
}
```

#### 3.2.2 传输层工厂

```typescript
// features/voice/transports/TransportFactory.ts

import { ITransport, TransportConfig } from './TransportInterface';
import { WebRTCTransport } from './WebRTCTransport';
import { WebSocketTransport } from './WebSocketTransport';

/**
 * 传输层类型
 */
export type TransportType = 'webrtc' | 'websocket';

/**
 * 传输层工厂
 * 
 * 根据配置创建相应的传输层实例。
 */
export class TransportFactory {
  /**
   * 创建传输层实例
   * 
   * @param type - 传输层类型
   * @param config - 传输层配置
   * @returns 传输层实例
   */
  static create(type: TransportType, config: TransportConfig): ITransport {
    switch (type) {
      case 'webrtc':
        return new WebRTCTransport(config);
      case 'websocket':
        return new WebSocketTransport(config);
      default:
        throw new Error(`不支持的传输层类型: ${type}`);
    }
  }
  
  /**
   * 从配置获取传输层类型
   * 
   * @param config - 配置对象（从后端获取）
   * @returns 传输层类型
   */
  static getTypeFromConfig(config: any): TransportType {
    // 从配置中读取传输层类型，默认使用 WebRTC
    return config?.transport?.type || 'webrtc';
  }
}
```

#### 3.2.3 WebRTC 传输层实现

```typescript
// features/voice/transports/WebRTCTransport.ts

import { OpenAIRealtimeWebRTC } from '@openai/agents/realtime';
import { ITransport, TransportConfig } from './TransportInterface';

/**
 * WebRTC 传输层实现
 */
export class WebRTCTransport implements ITransport {
  readonly type = 'webrtc' as const;
  private transport: OpenAIRealtimeWebRTC | null = null;
  private config: TransportConfig | null = null;
  
  constructor(config: TransportConfig) {
    this.config = config;
  }
  
  get isConnected(): boolean {
    return this.transport?.status === 'connected';
  }
  
  async connect(config: TransportConfig): Promise<void> {
    this.config = config;
    
    // 构建 WebRTC 端点 URL
    let baseUrl = config.baseUrl;
    if (baseUrl.endsWith('/v1')) {
      baseUrl = baseUrl.slice(0, -3);
    } else if (baseUrl.endsWith('/v1/')) {
      baseUrl = baseUrl.slice(0, -4);
    }
    baseUrl = baseUrl.replace(/\/$/, '');
    const webrtcEndpoint = `${baseUrl}/v1/realtime/calls`;
    
    // 创建 WebRTC 传输层
    this.transport = new OpenAIRealtimeWebRTC({
      baseUrl: webrtcEndpoint,
      mediaStream: config.userMediaStream,
      audioElement: config.assistantAudioElement,
    });
    
    // 等待连接建立
    await this.waitForConnection();
  }
  
  disconnect(): void {
    if (this.transport) {
      // WebRTC transport 的断开逻辑
      this.transport = null;
    }
  }
  
  sendAudio(audioData: ArrayBuffer): void {
    // WebRTC 会自动处理音频流，不需要手动发送
    // 如果需要手动发送，可以通过 transport 的方法
  }
  
  getUserMediaStream(): MediaStream | null {
    return this.config?.userMediaStream || null;
  }
  
  getAssistantAudioStream(): MediaStream | null {
    return this.config?.assistantAudioElement?.srcObject as MediaStream || null;
  }
  
  on(event: string, callback: (data: any) => void): void {
    // 通过 transport 监听事件
    // 注意：OpenAIRealtimeWebRTC 的事件监听方式可能需要适配
  }
  
  off(event: string, callback: (data: any) => void): void {
    // 移除事件监听
  }
  
  private async waitForConnection(): Promise<void> {
    // 等待 WebRTC 连接建立
    // 实现逻辑...
  }
}
```

#### 3.2.4 WebSocket 传输层实现（待实现）

```typescript
// features/voice/transports/WebSocketTransport.ts

import { ITransport, TransportConfig } from './TransportInterface';

/**
 * WebSocket 传输层实现
 * 
 * 使用 WebSocket 连接 OpenAI Realtime API。
 */
export class WebSocketTransport implements ITransport {
  readonly type = 'websocket' as const;
  private websocket: WebSocket | null = null;
  private config: TransportConfig | null = null;
  
  constructor(config: TransportConfig) {
    this.config = config;
  }
  
  get isConnected(): boolean {
    return this.websocket?.readyState === WebSocket.OPEN;
  }
  
  async connect(config: TransportConfig): Promise<void> {
    this.config = config;
    
    // 构建 WebSocket URL
    const wsUrl = this.buildWebSocketUrl(config);
    
    // 创建 WebSocket 连接
    this.websocket = new WebSocket(wsUrl);
    
    // 等待连接建立
    await this.waitForConnection();
    
    // 设置事件监听
    this.setupEventListeners();
  }
  
  disconnect(): void {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
  }
  
  sendAudio(audioData: ArrayBuffer): void {
    if (this.websocket && this.isConnected) {
      // 发送音频数据到 WebSocket
      this.websocket.send(audioData);
    }
  }
  
  getUserMediaStream(): MediaStream | null {
    return this.config?.userMediaStream || null;
  }
  
  getAssistantAudioStream(): MediaStream | null {
    // WebSocket 需要自己处理音频流
    // 实现逻辑...
    return null;
  }
  
  on(event: string, callback: (data: any) => void): void {
    // WebSocket 事件监听
  }
  
  off(event: string, callback: (data: any) => void): void {
    // 移除事件监听
  }
  
  private buildWebSocketUrl(config: TransportConfig): string {
    // 构建 WebSocket URL
    // 实现逻辑...
    return '';
  }
  
  private async waitForConnection(): Promise<void> {
    // 等待 WebSocket 连接建立
    // 实现逻辑...
  }
  
  private setupEventListeners(): void {
    // 设置 WebSocket 事件监听
    // 实现逻辑...
  }
}
```

#### 3.2.5 音频可视化模块

```typescript
// features/voice/visualization/AudioVisualizer.ts

/**
 * 音频可视化器
 * 
 * 负责从音频流中提取频率数据，用于可视化。
 */
export class AudioVisualizer {
  private userAnalyser: AnalyserNode | null = null;
  private assistantAnalyser: AnalyserNode | null = null;
  private userContext: AudioContext | null = null;
  private assistantContext: AudioContext | null = null;
  private userAnimationFrame: number | null = null;
  private assistantAnimationFrame: number | null = null;
  
  /**
   * 初始化用户音频可视化
   */
  async initUserVisualization(stream: MediaStream): Promise<void> {
    // 创建 AudioContext
    const context = new AudioContext({ sampleRate: 24000 });
    this.userContext = context;
    
    // 创建 AnalyserNode
    const source = context.createMediaStreamSource(stream);
    const analyser = context.createAnalyser();
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.3;
    this.userAnalyser = analyser;
    
    source.connect(analyser);
  }
  
  /**
   * 初始化助手音频可视化
   */
  async initAssistantVisualization(audioElement: HTMLAudioElement): Promise<void> {
    // 实现逻辑...
  }
  
  /**
   * 开始提取用户频率数据
   */
  startUserFrequencyExtraction(
    onData: (data: Uint8Array) => void
  ): void {
    if (!this.userAnalyser) return;
    
    const update = () => {
      const bufferLength = this.userAnalyser!.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      this.userAnalyser!.getByteFrequencyData(dataArray);
      onData(dataArray);
      this.userAnimationFrame = requestAnimationFrame(update) as any;
    };
    
    update();
  }
  
  /**
   * 停止提取频率数据
   */
  stopFrequencyExtraction(): void {
    if (this.userAnimationFrame) {
      cancelAnimationFrame(this.userAnimationFrame);
      this.userAnimationFrame = null;
    }
    if (this.assistantAnimationFrame) {
      cancelAnimationFrame(this.assistantAnimationFrame);
      this.assistantAnimationFrame = null;
    }
  }
  
  /**
   * 清理资源
   */
  cleanup(): void {
    this.stopFrequencyExtraction();
    // 清理 AudioContext 等资源
  }
}
```

#### 3.2.6 核心服务

```typescript
// features/voice/services/VoiceAgentService.ts

import { TransportFactory, TransportType } from '../transports/TransportFactory';
import { ITransport, TransportConfig } from '../transports/TransportInterface';
import { AudioVisualizer } from '../visualization/AudioVisualizer';
import { SessionManager } from './SessionManager';
import { ConfigManager } from './ConfigManager';
import { EventHandler } from './EventHandler';

/**
 * Voice Agent 核心服务
 * 
 * 协调传输层、会话管理、音频可视化等模块。
 */
export class VoiceAgentService {
  private transport: ITransport | null = null;
  private transportType: TransportType = 'webrtc';
  private audioVisualizer: AudioVisualizer;
  private sessionManager: SessionManager;
  private configManager: ConfigManager;
  private eventHandler: EventHandler;
  
  constructor() {
    this.audioVisualizer = new AudioVisualizer();
    this.sessionManager = new SessionManager();
    this.configManager = new ConfigManager();
    this.eventHandler = new EventHandler();
  }
  
  /**
   * 连接 Voice Agent
   */
  async connect(
    personalityId: string,
    callbacks: {
      onUserTranscript?: (text: string) => void;
      onAssistantTranscript?: (text: string) => void;
    }
  ): Promise<void> {
    // 1. 加载配置
    const config = await this.configManager.loadConfig(personalityId);
    
    // 2. 获取传输层类型（从配置中读取）
    this.transportType = TransportFactory.getTypeFromConfig(config);
    
    // 3. 获取用户音频流
    const userMediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    // 4. 创建助手音频元素
    const assistantAudioElement = new Audio();
    assistantAudioElement.autoplay = false;
    assistantAudioElement.muted = true;
    
    // 5. 创建传输层
    const transportConfig: TransportConfig = {
      apiKey: config.apiKey,
      model: config.model,
      baseUrl: config.baseUrl,
      userMediaStream,
      assistantAudioElement,
    };
    
    this.transport = TransportFactory.create(this.transportType, transportConfig);
    
    // 6. 连接传输层
    await this.transport.connect(transportConfig);
    
    // 7. 初始化音频可视化
    await this.audioVisualizer.initUserVisualization(userMediaStream);
    await this.audioVisualizer.initAssistantVisualization(assistantAudioElement);
    
    // 8. 设置事件监听
    this.eventHandler.setupEventListeners(this.transport, callbacks);
  }
  
  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.transport) {
      this.transport.disconnect();
      this.transport = null;
    }
    this.audioVisualizer.cleanup();
    this.eventHandler.cleanup();
  }
  
  /**
   * 开始通话
   */
  async startCall(): Promise<void> {
    // 实现逻辑...
  }
  
  /**
   * 结束通话
   */
  async endCall(): Promise<void> {
    // 实现逻辑...
  }
  
  /**
   * 获取用户频率数据
   */
  getUserFrequencyData(): Uint8Array | null {
    // 通过 audioVisualizer 获取
    return null;
  }
  
  /**
   * 获取助手频率数据
   */
  getAssistantFrequencyData(): Uint8Array | null {
    // 通过 audioVisualizer 获取
    return null;
  }
}
```

#### 3.2.7 简化后的 Hook

```typescript
// hooks/useVoiceAgent.ts

import { useState, useRef, useCallback } from 'react';
import { VoiceAgentService } from '@/features/voice/services/VoiceAgentService';

export interface UseVoiceAgentReturn {
  isConnected: boolean;
  isConnecting: boolean;
  isCalling: boolean;
  error: string | null;
  userFrequencyData: Uint8Array | null;
  assistantFrequencyData: Uint8Array | null;
  connect: () => Promise<void>;
  disconnect: () => void;
  startCall: () => Promise<void>;
  endCall: () => Promise<void>;
}

export const useVoiceAgent = (
  _sessionId?: string,
  personalityId?: string,
  callbacks?: {
    onUserTranscript?: (text: string) => void;
    onAssistantTranscript?: (text: string) => void;
  }
): UseVoiceAgentReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isCalling, setIsCalling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userFrequencyData, setUserFrequencyData] = useState<Uint8Array | null>(null);
  const [assistantFrequencyData, setAssistantFrequencyData] = useState<Uint8Array | null>(null);
  
  const serviceRef = useRef<VoiceAgentService | null>(null);
  
  const connect = useCallback(async () => {
    setIsConnecting(true);
    setError(null);
    
    try {
      if (!serviceRef.current) {
        serviceRef.current = new VoiceAgentService();
      }
      
      await serviceRef.current.connect(personalityId || '', callbacks || {});
      setIsConnected(true);
    } catch (err: any) {
      setError(err.message || '连接失败');
      throw err;
    } finally {
      setIsConnecting(false);
    }
  }, [personalityId, callbacks]);
  
  const disconnect = useCallback(() => {
    if (serviceRef.current) {
      serviceRef.current.disconnect();
      serviceRef.current = null;
    }
    setIsConnected(false);
    setIsCalling(false);
  }, []);
  
  const startCall = useCallback(async () => {
    if (!serviceRef.current) {
      throw new Error('Voice Agent 未连接');
    }
    
    setIsCalling(true);
    try {
      await serviceRef.current.startCall();
    } catch (err: any) {
      setError(err.message || '开始通话失败');
      throw err;
    }
  }, []);
  
  const endCall = useCallback(async () => {
    if (serviceRef.current) {
      await serviceRef.current.endCall();
    }
    setIsCalling(false);
  }, []);
  
  return {
    isConnected,
    isConnecting,
    isCalling,
    error,
    userFrequencyData,
    assistantFrequencyData,
    connect,
    disconnect,
    startCall,
    endCall,
  };
};
```

## 4. 重构步骤（已更新）

**注意**：根据功能分析，重构步骤已调整为与功能完善并行进行。详细规划参见 `docs/architecture/voice-agent-feature-analysis.md`。

### 阶段1：基础架构 + 核心功能（2-3周）

**并行进行**：

1. **架构基础**（1周）
   - 创建目录结构
   - 定义核心接口（ITransport、IEventHandler 等）
   - 创建基础服务类（框架）

2. **核心功能实现**（2周）
   - 工具调用功能（在现有代码中添加）
   - 打断处理（在现有代码中添加）
   - 文本输入（在现有代码中添加）

### 阶段2：架构重构（2周）

1. **传输层抽象**
   - 实现 `WebRTCTransport`（将现有逻辑迁移）
   - 实现 `TransportFactory`

2. **模块分离**
   - 创建 `AudioVisualizer`（将现有逻辑迁移）
   - 创建 `EventHandler`
   - 创建 `SessionManager`
   - 创建 `ConfigManager`

3. **Hook 重构**
   - 简化 `useVoiceAgent.ts`，使用新的 `VoiceAgentService`
   - 测试确保现有功能正常

### 阶段3：WebSocket 支持（1周）

1. 实现 `WebSocketTransport`
2. 添加配置支持（从后端读取传输层类型）
3. 测试 WebSocket 传输层

### 阶段4：增强功能（可选，1-2周）

1. 会话历史管理
2. 自定义护栏
3. 多智能体编排

**详细实施计划**：参见 `docs/architecture/voice-agent-feature-analysis.md`

## 5. 配置支持

### 5.1 后端配置

在 `backend/config/voice/realtime.yaml` 中添加传输层配置：

```yaml
engines:
  realtime:
    default: "openai"
    openai:
      # ... 现有配置 ...
      transport:
        type: "webrtc"  # 或 "websocket"
        webrtc:
          endpoint: "/v1/realtime/calls"
        websocket:
          endpoint: "/v1/realtime"
```

### 5.2 前端配置读取

在 `ConfigManager` 中读取传输层类型：

```typescript
export class ConfigManager {
  async loadConfig(personalityId: string): Promise<VoiceAgentConfig> {
    const [openaiConfig, realtimeConfig, personality] = await Promise.all([
      configApi.getOpenAIConfig(),
      configApi.getRealtimeConfig(),
      personalityApi.getPersonality(personalityId),
    ]);
    
    return {
      apiKey: openaiConfig.api_key,
      baseUrl: openaiConfig.base_url,
      model: realtimeConfig.model,
      transport: {
        type: realtimeConfig.transport?.type || 'webrtc',
        // ... 其他传输配置
      },
      // ... 其他配置
    };
  }
}
```

## 6. 优势总结

### 6.1 代码清晰度

- Hook 从 816 行减少到 100-200 行
- 每个模块职责单一，易于理解
- 代码组织更清晰

### 6.2 可扩展性

- 添加新传输方式只需实现 `ITransport` 接口
- 通过工厂模式创建，无需修改核心代码
- 配置驱动，灵活切换

### 6.3 可测试性

- 各模块独立，易于单元测试
- 接口清晰，易于 Mock
- 测试覆盖更全面

### 6.4 可维护性

- 修改传输层实现不影响其他模块
- Bug 定位更容易
- 代码复用性更高

---

**文档版本**: v1.0  
**创建日期**: 2025-01-XX  
**最后更新**: 2025-01-XX

