# Voice Agent 工具调用实现方案

## 1. 当前状态分析

### 1.1 后端已实现

**工具列表**：
- ✅ `calculator` - 计算器工具
- ✅ `time` - 时间/日期工具
- ⚠️ `weather` - 天气工具（可能未完全实现）

**后端 API**：
- ✅ `GET /v1/tools` - 获取工具列表
- ✅ `POST /v1/tools/execute` - 执行工具

**工具系统**：
- ✅ `Tool` 基类，支持 `to_openai_function()` 转换为 OpenAI 格式
- ✅ `ToolManager` 管理工具执行
- ✅ Personality 配置中定义 `allowed_tools`

### 1.2 前端未实现

- ❌ 工具定义传递给 RealtimeAgent
- ❌ 工具调用事件监听
- ❌ 工具执行逻辑
- ❌ 工具结果返回
- ❌ 工具调用 UI 显示

## 2. 实现方案

### 2.1 架构设计

```
useVoiceAgent
    ↓
VoiceAgentService
    ├── ToolManager (前端)
    │   ├── 获取工具列表（从后端）
    │   ├── 转换为 RealtimeAgent 格式
    │   └── 工具执行（调用后端 API）
    ├── EventHandler
    │   └── 监听工具调用事件
    └── RealtimeAgent
        └── 传递 tools 配置
```

### 2.2 核心模块

#### 2.2.1 前端 ToolManager

```typescript
// features/voice/services/ToolManager.ts

import { toolsApi } from '@/services/tools';
import type { ToolInfo } from '@/types/tools';

/**
 * 前端工具管理器
 * 
 * 负责：
 * 1. 从后端获取工具列表
 * 2. 转换为 RealtimeAgent 格式
 * 3. 执行工具（调用后端 API）
 */
export class ToolManager {
  private toolsCache: Map<string, ToolInfo[]> = new Map();
  
  /**
   * 获取工具列表（从后端）
   */
  async getTools(personalityId: string): Promise<ToolInfo[]> {
    // 检查缓存
    if (this.toolsCache.has(personalityId)) {
      return this.toolsCache.get(personalityId)!;
    }
    
    // 从后端获取
    const response = await toolsApi.listTools();
    this.toolsCache.set(personalityId, response.tools);
    
    return response.tools;
  }
  
  /**
   * 转换为 RealtimeAgent 工具格式
   * 
   * RealtimeAgent 需要的格式：
   * {
   *   type: "function",
   *   function: {
   *     name: string,
   *     description: string,
   *     parameters: {
   *       type: "object",
   *       properties: {...},
   *       required: [...]
   *     }
   *   }
   * }
   */
  convertToRealtimeFormat(tools: ToolInfo[]): any[] {
    return tools
      .filter(tool => tool.enabled)
      .map(tool => ({
        type: "function",
        function: {
          name: tool.name,
          description: tool.description,
          parameters: tool.parameters || {},
        }
      }));
  }
  
  /**
   * 执行工具（调用后端 API）
   */
  async executeTool(
    toolName: string,
    parameters: Record<string, any>
  ): Promise<any> {
    return toolsApi.executeTool(toolName, parameters);
  }
}
```

#### 2.2.2 工具调用事件处理

```typescript
// features/voice/services/EventHandler.ts

import { ToolManager } from './ToolManager';

/**
 * 事件处理器
 * 
 * 处理 RealtimeSession 的各种事件，包括工具调用。
 */
export class EventHandler {
  private toolManager: ToolManager;
  private session: any; // RealtimeSession
  
  constructor(toolManager: ToolManager) {
    this.toolManager = toolManager;
  }
  
  /**
   * 设置事件监听
   */
  setupEventListeners(
    session: any,
    callbacks: {
      onUserTranscript?: (text: string) => void;
      onAssistantTranscript?: (text: string) => void;
      onToolCall?: (toolName: string, parameters: any) => void;
      onToolResult?: (toolName: string, result: any) => void;
    }
  ): void {
    this.session = session;
    
    // 监听工具调用事件
    session.on('conversation.item.created', async (event: any) => {
      const item = event.item;
      
      // 检查是否是工具调用
      if (item.type === 'function_call' || item.type === 'tool_call') {
        await this.handleToolCall(item, callbacks);
      }
    });
    
    // 也可以监听其他事件...
  }
  
  /**
   * 处理工具调用
   */
  private async handleToolCall(
    item: any,
    callbacks: any
  ): Promise<void> {
    const toolName = item.name || item.function?.name;
    const parameters = item.arguments || item.function?.arguments || {};
    
    // 解析参数（可能是字符串）
    let parsedParams = parameters;
    if (typeof parameters === 'string') {
      try {
        parsedParams = JSON.parse(parameters);
      } catch (e) {
        console.error('Failed to parse tool parameters:', e);
        return;
      }
    }
    
    // 触发回调
    callbacks.onToolCall?.(toolName, parsedParams);
    
    try {
      // 执行工具（调用后端 API）
      const result = await this.toolManager.executeTool(toolName, parsedParams);
      
      // 返回工具结果给 RealtimeSession
      // 注意：需要根据 SDK 文档确定正确的返回方式
      await this.submitToolResult(item.id, result);
      
      // 触发回调
      callbacks.onToolResult?.(toolName, result);
    } catch (error) {
      console.error('Tool execution failed:', error);
      // 返回错误结果
      await this.submitToolResult(item.id, {
        success: false,
        error: error.message,
      });
    }
  }
  
  /**
   * 提交工具结果
   */
  private async submitToolResult(itemId: string, result: any): Promise<void> {
    // 根据 OpenAI Agents SDK 文档，提交工具结果
    // 可能需要使用 session.submitToolResult() 或类似方法
    // 需要查看 SDK 文档确认
  }
  
  cleanup(): void {
    // 清理事件监听
  }
}
```

#### 2.2.3 集成到 useVoiceAgent

```typescript
// hooks/useVoiceAgent.ts (修改部分)

import { ToolManager } from '@/features/voice/services/ToolManager';
import { EventHandler } from '@/features/voice/services/EventHandler';

export const useVoiceAgent = (
  _sessionId?: string,
  personalityId?: string,
  callbacks?: {
    onUserTranscript?: (text: string) => void;
    onAssistantTranscript?: (text: string) => void;
    onToolCall?: (toolName: string, parameters: any) => void;
    onToolResult?: (toolName: string, result: any) => void;
  }
): UseVoiceAgentReturn => {
  // ... 现有代码 ...
  
  const toolManagerRef = useRef<ToolManager | null>(null);
  const eventHandlerRef = useRef<EventHandler | null>(null);
  
  const connect = useCallback(async () => {
    // ... 现有连接逻辑 ...
    
    // 1. 获取工具列表
    if (!toolManagerRef.current) {
      toolManagerRef.current = new ToolManager();
    }
    
    const tools = await toolManagerRef.current.getTools(personalityId || '');
    const realtimeTools = toolManagerRef.current.convertToRealtimeFormat(tools);
    
    // 2. 创建 RealtimeAgent，传递工具
    const agent = new RealtimeAgent({
      name: 'cozychat-agent',
      instructions: instructions,
      voice: voice,
      tools: realtimeTools, // ✅ 传递工具
    });
    
    // 3. 设置事件处理器
    if (!eventHandlerRef.current) {
      eventHandlerRef.current = new EventHandler(toolManagerRef.current);
    }
    
    // ... 创建 session ...
    
    // 4. 设置事件监听（包括工具调用）
    eventHandlerRef.current.setupEventListeners(session, {
      onUserTranscript: callbacks?.onUserTranscript,
      onAssistantTranscript: callbacks?.onAssistantTranscript,
      onToolCall: callbacks?.onToolCall,
      onToolResult: callbacks?.onToolResult,
    });
    
    // ... 其余连接逻辑 ...
  }, [personalityId, callbacks]);
  
  // ... 其余代码 ...
};
```

### 2.3 API 服务

```typescript
// services/tools.ts

import { apiClient } from './api';

/**
 * 工具信息
 */
export interface ToolInfo {
  name: string;
  type: 'builtin' | 'mcp';
  description: string;
  parameters: Record<string, any>;
  enabled: boolean;
  server?: string; // MCP 服务器名称
}

/**
 * 工具列表响应
 */
export interface ToolsListResponse {
  tools: ToolInfo[];
  total: number;
}

/**
 * 执行工具请求
 */
export interface ExecuteToolRequest {
  tool_name: string;
  parameters: Record<string, any>;
}

/**
 * 执行工具响应
 */
export interface ExecuteToolResponse {
  tool_name: string;
  result: any;
  execution_time: number;
  success: boolean;
}

/**
 * 工具 API 服务
 */
export const toolsApi = {
  /**
   * 获取工具列表
   */
  async listTools(type?: 'builtin' | 'mcp' | 'all'): Promise<ToolsListResponse> {
    const params = type ? { type } : {};
    return apiClient.get<ToolsListResponse>('/v1/tools', { params });
  },
  
  /**
   * 执行工具
   */
  async executeTool(
    toolName: string,
    parameters: Record<string, any>
  ): Promise<ExecuteToolResponse> {
    return apiClient.post<ExecuteToolResponse>('/v1/tools/execute', {
      tool_name: toolName,
      parameters,
    });
  },
};
```

### 2.4 类型定义

```typescript
// types/tools.ts

/**
 * 工具信息
 */
export interface ToolInfo {
  name: string;
  type: 'builtin' | 'mcp';
  description: string;
  parameters: Record<string, any>;
  enabled: boolean;
  server?: string;
}

/**
 * 工具调用事件
 */
export interface ToolCallEvent {
  id: string;
  toolName: string;
  parameters: Record<string, any>;
}

/**
 * 工具结果事件
 */
export interface ToolResultEvent {
  toolName: string;
  result: any;
  success: boolean;
  error?: string;
}
```

## 3. 实施步骤

### 阶段1：基础实现（1周）

#### Day 1-2: API 服务和类型定义
- [ ] 创建 `services/tools.ts`
- [ ] 创建 `types/tools.ts`
- [ ] 测试 API 调用

#### Day 3-4: ToolManager 实现
- [ ] 创建 `features/voice/services/ToolManager.ts`
- [ ] ] 实现 `getTools()` 方法
- [ ] 实现 `convertToRealtimeFormat()` 方法
- [ ] 实现 `executeTool()` 方法
- [ ] 单元测试

#### Day 5: EventHandler 实现
- [ ] 创建 `features/voice/services/EventHandler.ts`
- [ ] 实现工具调用事件监听
- [ ] 实现工具执行逻辑
- [ ] 实现工具结果返回

### 阶段2：集成到 useVoiceAgent（3-5天）

#### Day 1-2: 修改 useVoiceAgent
- [ ] 添加 ToolManager 和 EventHandler
- [ ] 在 `connect()` 中获取工具列表
- [ ] 在创建 RealtimeAgent 时传递工具
- [ ] 设置工具调用事件监听

#### Day 3: 测试和调试
- [ ] 测试工具调用流程
- [ ] 调试工具执行
- [ ] 验证工具结果返回

#### Day 4-5: UI 显示（可选）
- [ ] 在消息中显示工具调用
- [ ] 显示工具执行结果
- [ ] 工具调用状态指示

### 阶段3：扩展能力设计（2-3天）

#### Day 1: 工具注册机制
- [ ] 设计工具注册接口
- [ ] 支持动态添加工具
- [ ] 工具优先级管理

#### Day 2: 工具配置
- [ ] 支持工具启用/禁用
- [ ] 支持工具参数验证
- [ ] 支持工具超时配置

#### Day 3: 文档和测试
- [ ] 编写使用文档
- [ ] 添加单元测试
- [ ] 集成测试

## 4. 关键技术点

### 4.1 RealtimeAgent 工具格式

根据 OpenAI Agents SDK 文档，工具需要转换为以下格式：

```typescript
{
  type: "function",
  function: {
    name: "calculator",
    description: "执行数学计算",
    parameters: {
      type: "object",
      properties: {
        expression: {
          type: "string",
          description: "数学表达式"
        }
      },
      required: ["expression"]
    }
  }
}
```

### 4.2 工具调用事件

根据 SDK 文档，工具调用可能通过以下事件触发：
- `conversation.item.created` - 当创建工具调用项时
- `conversation.item.function_call` - 工具调用事件（如果存在）

需要查看 SDK 文档确认具体事件名称。

### 4.3 工具结果返回

工具执行后，需要将结果返回给 RealtimeSession。可能需要：
- `session.submitToolResult(itemId, result)` - 如果 SDK 提供此方法
- 或通过 `session.send()` 发送工具结果消息

需要查看 SDK 文档确认。

## 5. 扩展能力设计

### 5.1 工具注册接口

```typescript
// features/voice/services/ToolRegistry.ts

/**
 * 工具注册器
 * 
 * 支持动态注册新工具，为后续扩展提供能力。
 */
export class ToolRegistry {
  private customTools: Map<string, ToolDefinition> = new Map();
  
  /**
   * 注册自定义工具
   */
  registerTool(tool: ToolDefinition): void {
    this.customTools.set(tool.name, tool);
  }
  
  /**
   * 获取所有工具（包括自定义工具）
   */
  async getAllTools(personalityId: string): Promise<ToolInfo[]> {
    const toolManager = new ToolManager();
    const backendTools = await toolManager.getTools(personalityId);
    
    // 合并自定义工具
    const customTools = Array.from(this.customTools.values()).map(tool => ({
      name: tool.name,
      type: 'custom' as const,
      description: tool.description,
      parameters: tool.parameters,
      enabled: true,
    }));
    
    return [...backendTools, ...customTools];
  }
}

/**
 * 工具定义接口
 */
export interface ToolDefinition {
  name: string;
  description: string;
  parameters: Record<string, any>;
  execute: (parameters: Record<string, any>) => Promise<any>;
}
```

### 5.2 工具配置管理

```typescript
// features/voice/services/ToolConfig.ts

/**
 * 工具配置管理器
 * 
 * 管理工具的启用/禁用、参数验证、超时等配置。
 */
export class ToolConfig {
  private config: Map<string, ToolConfigItem> = new Map();
  
  /**
   * 设置工具配置
   */
  setToolConfig(toolName: string, config: ToolConfigItem): void {
    this.config.set(toolName, config);
  }
  
  /**
   * 检查工具是否启用
   */
  isToolEnabled(toolName: string): boolean {
    return this.config.get(toolName)?.enabled !== false;
  }
  
  /**
   * 获取工具超时时间
   */
  getToolTimeout(toolName: string): number {
    return this.config.get(toolName)?.timeout || 30000; // 默认30秒
  }
}

/**
 * 工具配置项
 */
export interface ToolConfigItem {
  enabled: boolean;
  timeout?: number;
  maxRetries?: number;
  validateParams?: (params: Record<string, any>) => boolean;
}
```

## 6. 测试计划

### 6.1 单元测试

- [ ] ToolManager.getTools() 测试
- [ ] ToolManager.convertToRealtimeFormat() 测试
- [ ] ToolManager.executeTool() 测试
- [ ] EventHandler.handleToolCall() 测试

### 6.2 集成测试

- [ ] 完整工具调用流程测试
  - 用户语音输入 → AI 调用工具 → 工具执行 → 结果返回 → AI 回复
- [ ] 多个工具调用测试
- [ ] 工具执行失败处理测试

### 6.3 端到端测试

- [ ] 计算器工具测试（"帮我算一下 123 + 456"）
- [ ] 时间工具测试（"现在几点了"）
- [ ] 工具调用 UI 显示测试

## 7. 参考资料

- [OpenAI Agents SDK 官方文档](https://openai.github.io/openai-agents-js/zh/guides/voice-agents/build/)
- [工具调用文档](https://openai.github.io/openai-agents-js/zh/guides/tools/)
- 后端工具实现：`backend/app/engines/tools/`

---

**文档版本**: v1.0  
**创建日期**: 2025-01-XX  
**最后更新**: 2025-01-XX

