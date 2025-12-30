# 语音传输层策略模式重构

## 重构目标

将 WebSocket 和 WebRTC 的功能完全分离，使用策略模式，确保：
1. 代码结构清晰，易于维护
2. WebRTC 和 WebSocket 逻辑互不干扰
3. 不影响已实现的 WebRTC 功能
4. 便于后续扩展新的传输层类型

## 重构方案

### 1. 策略模式架构

```
frontend/src/features/voice/
├── strategies/                    # 传输层策略（新增）
│   ├── ITransportStrategy.ts     # 策略接口
│   ├── WebRTCStrategy.ts          # WebRTC 策略实现
│   ├── WebSocketStrategy.ts      # WebSocket 策略实现
│   └── TransportStrategyFactory.ts # 策略工厂
├── services/
│   ├── VoiceAgentService.ts      # 核心服务（重构）
│   ├── SessionManager.ts          # 会话管理（简化）
│   ├── EventHandler.ts           # 事件处理（不变）
│   ├── ConfigManager.ts          # 配置管理（不变）
│   └── ToolManager.ts            # 工具管理（不变）
└── transports/                    # 传输层实现（保留，但不再直接使用）
    ├── TransportInterface.ts
    ├── WebRTCTransport.ts
    └── WebSocketTransport.ts
```

### 2. 策略接口设计

**ITransportStrategy** 定义了统一的接口：
- `createSession()`: 创建并连接 RealtimeSession
- `initAudioVisualization()`: 初始化音频可视化
- `startAudioVisualization()`: 启动音频可视化
- `stopAudioVisualization()`: 停止音频可视化
- `cleanup()`: 清理资源
- `getCurrentUserFrequencyData()`: 获取用户音频频率数据
- `getCurrentAssistantFrequencyData()`: 获取助手音频频率数据

### 3. WebRTC 策略实现

**WebRTCStrategy** 封装了所有 WebRTC 相关逻辑：
- 使用 `OpenAIRealtimeWebRTC` SDK
- 自动处理音频输入输出（SDK 内部处理）
- 管理 `MediaStream` 和 `AudioElement`
- 音频可视化通过 `AudioVisualizer` 实现

### 4. WebSocket 策略实现

**WebSocketStrategy** 封装了所有 WebSocket 相关逻辑：
- 使用 SDK 原生的 `transport: 'websocket'` 字符串
- 手动处理音频捕获和播放：
  - 使用 `AudioContext` + `ScriptProcessor` 捕获音频
  - 转换为 PCM16 格式并调用 `session.sendAudio()` 发送
  - 监听 `session.on('audio', ...)` 接收音频
  - 将 PCM16 转换为 WAV 格式并播放
- 音频可视化通过 `AudioVisualizer` 实现

### 5. VoiceAgentService 重构

**VoiceAgentService** 现在：
- 不再直接处理传输层逻辑
- 根据配置选择策略（WebRTC 或 WebSocket）
- 委托策略处理所有传输层相关操作
- 保持统一的接口，对上层透明

## 代码变更

### 新增文件

1. `frontend/src/features/voice/strategies/ITransportStrategy.ts`
   - 策略接口定义

2. `frontend/src/features/voice/strategies/WebRTCStrategy.ts`
   - WebRTC 策略实现（约 200 行）

3. `frontend/src/features/voice/strategies/WebSocketStrategy.ts`
   - WebSocket 策略实现（约 310 行）

4. `frontend/src/features/voice/strategies/TransportStrategyFactory.ts`
   - 策略工厂（约 30 行）

### 修改文件

1. `frontend/src/features/voice/services/VoiceAgentService.ts`
   - 移除所有 WebSocket/WebRTC 混合逻辑
   - 使用策略模式，代码从 566 行简化到约 340 行
   - 完全分离两种传输层的处理逻辑

2. `frontend/src/features/voice/services/SessionManager.ts`
   - 简化，支持策略模式传递的 transport 参数

## 优势

1. **清晰的职责分离**
   - WebRTC 逻辑完全在 `WebRTCStrategy` 中
   - WebSocket 逻辑完全在 `WebSocketStrategy` 中
   - `VoiceAgentService` 只负责协调

2. **易于维护**
   - 修改 WebRTC 功能不会影响 WebSocket
   - 修改 WebSocket 功能不会影响 WebRTC
   - 每个策略类独立测试

3. **易于扩展**
   - 添加新的传输层类型只需：
     - 实现 `ITransportStrategy` 接口
     - 在 `TransportStrategyFactory` 中注册

4. **向后兼容**
   - 保持 `VoiceAgentService` 的公共接口不变
   - Hook 层无需修改

## 测试建议

1. **WebRTC 功能测试**
   - 确保现有 WebRTC 功能完全正常
   - 测试音频输入输出
   - 测试音频可视化
   - 测试多次通话（startCall → endCall → startCall）

2. **WebSocket 功能测试**
   - 测试 WebSocket 连接
   - 测试音频捕获和发送
   - 测试音频接收和播放
   - 测试音频可视化
   - 测试多次通话

3. **切换测试**
   - 测试在配置中切换传输层类型
   - 确保切换后功能正常

## 后续优化

1. 可以考虑移除 `transports/` 目录下的旧实现（如果不再需要）
2. 可以考虑将 `SessionManager` 的功能合并到策略中
3. 可以考虑添加更多的传输层类型（如 SIP）

