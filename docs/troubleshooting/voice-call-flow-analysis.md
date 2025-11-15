# 语音通话流程分析

## 第一次通话 vs 第二次通话的区别

### 第一次通话流程

```
1. useVoiceAgent.startCall() 被调用
   ↓
2. 检查 !isConnected → true，调用 connect()
   ↓
3. VoiceAgentService.connect() 执行：
   - 创建 transport (WebRTC)
   - 创建 session (RealtimeSession)
   - 设置事件监听器
   - isConnected = true
   ↓
4. useVoiceAgent.startCall() 继续执行
   ↓
5. VoiceAgentService.startCall() 执行：
   - 关闭旧的 session（connect() 创建的）❌ 浪费！
   - 断开旧的 transport（connect() 创建的）❌ 浪费！
   - 创建新的 transport
   - 创建新的 session
   - 设置事件监听器
   - 连接 session
```

**问题：** `connect()` 创建的 transport 和 session 立即被 `startCall()` 覆盖，造成资源浪费。

### 第二次通话流程

```
1. useVoiceAgent.startCall() 被调用
   ↓
2. 检查 isConnected → true，跳过 connect() ✅
   ↓
3. 直接调用 VoiceAgentService.startCall()
   ↓
4. VoiceAgentService.startCall() 执行：
   - 关闭旧的 session（第一次通话时创建的）
   - 断开旧的 transport（第一次通话时创建的）
   - 创建新的 transport
   - 创建新的 session
   - 设置事件监听器
   - 连接 session
```

**问题：** 每次 `startCall()` 都重新创建 transport 和 session，这是正确的，但是 `connect()` 的逻辑是多余的。

## 解决方案

### 方案1：简化 connect()，只做初始化（推荐）

`connect()` 不应该创建 transport 和 session，只应该做初始化工作（加载配置、工具等）。

```typescript
async connect(): Promise<void> {
  // 只做初始化，不创建 transport 和 session
  // transport 和 session 在 startCall() 中创建
  this.isConnected = true;
}
```

### 方案2：connect() 创建 transport，startCall() 只创建 session

`connect()` 创建 transport，`startCall()` 只创建 session（复用 transport）。

```typescript
async connect(): Promise<void> {
  // 创建 transport
  this.transport = TransportFactory.create('webrtc', {...});
  await this.transport.connect({});
  this.isConnected = true;
}

async startCall(): Promise<void> {
  // 只创建 session，复用 transport
  const session = await this.sessionManager.createSession(agent, this.transport, {...});
  // ...
}
```

### 方案3：移除 connect()，所有逻辑都在 startCall() 中

完全移除 `connect()`，所有逻辑都在 `startCall()` 中。

```typescript
async startCall(): Promise<void> {
  // 如果未连接，先初始化
  if (!this.isConnected) {
    // 初始化逻辑
    this.isConnected = true;
  }
  
  // 创建 transport 和 session
  // ...
}
```

## 当前实现的问题

1. **资源浪费**：第一次通话时，`connect()` 创建的 transport 和 session 立即被覆盖
2. **逻辑冗余**：`connect()` 和 `startCall()` 都在创建 transport 和 session
3. **状态不一致**：`isConnected = true` 但 transport 和 session 可能已经被替换

## 推荐方案

**推荐使用方案1**：简化 `connect()`，只做初始化工作，transport 和 session 都在 `startCall()` 中创建。

这样可以：
- 避免资源浪费
- 逻辑更清晰
- 每次通话都是全新的 transport 和 session（避免状态问题）

