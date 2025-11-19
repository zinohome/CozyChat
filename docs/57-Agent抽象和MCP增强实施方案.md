# Agent 抽象优化和 MCP 增强实施方案

> **制定日期**: 2025-01-XX  
> **参考**: `docs/55-Agno架构迁移可行性评估报告.md` (326-333行)  
> **目标**: 优化 Agent 抽象，增强 MCP 支持

---

## 一、实施范围评估

### 1.1 我能做到什么程度？

#### ✅ **可以完全实现的部分**

1. **Agent 抽象优化** - **100% 可实现**
   - 创建统一的 Agent 抽象类
   - 将 Personality 包装成 Agent 实例
   - 提供统一的 Agent API（run, chat, tools 等）
   - 保持人格系统的核心创新（YAML 配置驱动）

2. **MCP 协议基础实现** - **80% 可实现**
   - 实现 MCP 协议的核心功能（initialize, list_tools, call_tool）
   - 支持 stdio transport（标准输入输出）
   - 支持 HTTP transport（HTTP 请求）
   - 实现工具自动发现和注册

#### 🟡 **部分可实现的部分**

1. **MCP streamable-http transport** - **60% 可实现**
   - 需要 WebSocket 支持，可能需要额外开发
   - 可以实现基础版本，但完整功能需要更多测试

2. **MCP 高级特性** - **50% 可实现**
   - Prompts、Resources 等高级特性
   - 可以实现基础版本，完整功能需要参考官方 SDK

#### ❌ **暂时无法实现的部分**

1. **官方 MCP Python SDK 集成** - **需要等待官方 SDK**
   - 如果 OpenAI 发布官方 Python SDK，可以集成
   - 目前可以基于协议规范自行实现

---

## 二、详细实施方案

### 2.1 Agent 抽象优化

#### 2.1.1 设计目标

**当前架构**：
```
Orchestrator (编排器)
  ├── PersonalityManager (人格管理器)
  ├── MemoryManager (记忆管理器)
  ├── ToolManager (工具管理器)
  └── ContextBuilder (上下文构建器)
```

**优化后架构**：
```
Agent (统一抽象)
  ├── Personality (人格配置) - 核心创新保持不变
  ├── AI Engine (AI引擎)
  ├── Memory Manager (记忆管理器)
  ├── Tool Manager (工具管理器)
  └── Context Builder (上下文构建器)

Orchestrator (编排器)
  └── Agent instances (Agent实例池)
```

#### 2.1.2 实现内容

**1. 创建 Agent 抽象基类**

```python
# backend/app/core/agent/base.py
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional
from app.core.personality.models import Personality
from app.engines.ai.base import AIEngineBase, ChatMessage
from app.engines.memory.manager import MemoryManager
from app.engines.tools.manager import ToolManager
from app.core.context.builder import ContextBuilder

class Agent(ABC):
    """Agent 抽象基类
    
    借鉴 Agno 的 Agent 接口设计，提供统一的 Agent API
    保持 CozyChat 的人格系统核心创新（YAML 配置驱动）
    """
    
    def __init__(
        self,
        personality: Personality,
        ai_engine: AIEngineBase,
        memory_manager: MemoryManager,
        tool_manager: ToolManager,
        context_builder: Optional[ContextBuilder] = None,
        db: Optional[AsyncSession] = None
    ):
        """初始化 Agent
        
        Args:
            personality: 人格配置（核心创新，保持不变）
            ai_engine: AI引擎
            memory_manager: 记忆管理器
            tool_manager: 工具管理器
            context_builder: 上下文构建器（可选）
            db: 数据库会话（可选）
        """
        self.personality = personality
        self.ai_engine = ai_engine
        self.memory_manager = memory_manager
        self.tool_manager = tool_manager
        self.context_builder = context_builder
        self.db = db
    
    @property
    def name(self) -> str:
        """Agent 名称（来自人格配置）"""
        return self.personality.name
    
    @property
    def id(self) -> str:
        """Agent ID（来自人格配置）"""
        return self.personality.id
    
    @property
    def instructions(self) -> str:
        """Agent 指令（来自人格配置的 system_prompt）"""
        return self.personality.ai.system_prompt
    
    @property
    def tools(self) -> List[Dict[str, Any]]:
        """Agent 可用工具列表"""
        if not self.personality.tools.enabled:
            return []
        return self.tool_manager.get_tools_for_openai(
            tool_names=self.personality.tools.allowed_tools
        )
    
    async def run(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        session_id: str,
        stream: bool = False,
        **kwargs
    ) -> Any:
        """运行 Agent（统一入口）
        
        这是借鉴 Agno 的 Agent.run() 接口设计
        
        Args:
            messages: 消息历史
            user_id: 用户ID
            session_id: 会话ID
            stream: 是否流式
            **kwargs: 其他参数
            
        Returns:
            流式: AsyncIterator[Dict]
            非流式: Dict
        """
        # 构建智能上下文
        full_messages = await self._build_context(messages, user_id, session_id)
        
        # 准备工具
        tools = self.tools
        
        # 调用AI引擎
        if stream:
            return self._stream_chat(full_messages, tools, user_id, session_id)
        else:
            return await self._chat(full_messages, tools, user_id, session_id)
    
    async def chat(
        self,
        message: str,
        user_id: str,
        session_id: str,
        stream: bool = False,
        **kwargs
    ) -> Any:
        """聊天接口（简化版）
        
        这是借鉴 Agno 的 Agent.chat() 接口设计
        
        Args:
            message: 用户消息
            user_id: 用户ID
            session_id: 会话ID
            stream: 是否流式
            **kwargs: 其他参数
            
        Returns:
            流式: AsyncIterator[Dict]
            非流式: Dict
        """
        messages = [{"role": "user", "content": message}]
        return await self.run(messages, user_id, session_id, stream=stream, **kwargs)
    
    # ... 其他方法实现
```

**2. 创建 PersonalityAgent 实现**

```python
# backend/app/core/agent/personality_agent.py
from app.core.agent.base import Agent
from app.core.personality.models import Personality

class PersonalityAgent(Agent):
    """基于 Personality 的 Agent 实现
    
    这是 CozyChat 的核心创新：
    - 保持 YAML 配置驱动的人格系统
    - 提供统一的 Agent API
    - 兼容 Agno 风格的接口设计
    """
    
    def __init__(
        self,
        personality: Personality,
        # ... 其他参数
    ):
        super().__init__(personality, ...)
    
    # 实现具体的 Agent 逻辑
```

**3. 更新 Orchestrator 使用 Agent**

```python
# backend/app/core/personality/orchestrator.py
class Orchestrator:
    """核心编排器（更新后）
    
    现在使用 Agent 实例而不是直接操作各个管理器
    """
    
    def __init__(self, ...):
        self.agents: Dict[str, Agent] = {}  # personality_id -> Agent
    
    async def process_chat_request(self, ...):
        # 获取或创建 Agent
        agent = await self._get_or_create_agent(personality_id)
        
        # 使用 Agent 的统一接口
        return await agent.run(messages, user_id, session_id, stream=stream)
```

#### 2.1.3 实施步骤

1. **阶段1：创建 Agent 抽象**（1-2天）
   - 创建 `Agent` 抽象基类
   - 定义统一的 Agent API
   - 编写基础测试

2. **阶段2：实现 PersonalityAgent**（2-3天）
   - 实现 `PersonalityAgent` 类
   - 将现有 Orchestrator 逻辑迁移到 Agent
   - 保持人格系统的核心创新

3. **阶段3：更新 Orchestrator**（1-2天）
   - 更新 Orchestrator 使用 Agent 实例
   - 保持向后兼容
   - 更新测试

4. **阶段4：优化和文档**（1天）
   - 代码优化
   - 更新文档
   - 性能测试

**总计**：5-8 天

---

### 2.2 MCP 增强

#### 2.2.1 设计目标

**当前实现**：
- MCPClient 是简化实现，只有占位符代码
- 不支持实际的 MCP 协议通信
- 不支持多种传输方式

**优化后实现**：
- 完整的 MCP 协议实现
- 支持 stdio transport（标准输入输出）
- 支持 HTTP transport（HTTP 请求）
- 支持 streamable-http transport（WebSocket，基础版本）
- 自动发现和注册工具

#### 2.2.2 实现内容

**1. MCP 协议实现**

```python
# backend/app/engines/tools/mcp/protocol.py
"""
MCP 协议实现

基于 Model Context Protocol 规范实现
参考：https://modelcontextprotocol.io/
"""

from typing import Any, Dict, List, Optional
from enum import Enum

class MCPMethod(str, Enum):
    """MCP 协议方法"""
    INITIALIZE = "initialize"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    PROMPTS_LIST = "prompts/list"
    RESOURCES_LIST = "resources/list"

class MCPProtocol:
    """MCP 协议处理器"""
    
    def __init__(self, transport: "MCPTransport"):
        self.transport = transport
        self.protocol_version = "2024-11-05"
    
    async def initialize(
        self,
        protocol_version: str,
        capabilities: Dict[str, Any],
        client_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """初始化 MCP 连接
        
        Args:
            protocol_version: 协议版本
            capabilities: 客户端能力
            client_info: 客户端信息
            
        Returns:
            Dict: 服务器初始化响应
        """
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": MCPMethod.INITIALIZE,
            "params": {
                "protocolVersion": protocol_version,
                "capabilities": capabilities,
                "clientInfo": client_info
            }
        }
        
        response = await self.transport.send_request(request)
        return response.get("result", {})
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出可用工具
        
        Returns:
            List[Dict]: 工具列表
        """
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": MCPMethod.TOOLS_LIST,
            "params": {}
        }
        
        response = await self.transport.send_request(request)
        return response.get("result", {}).get("tools", [])
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """调用工具
        
        Args:
            name: 工具名称
            arguments: 工具参数
            
        Returns:
            Any: 工具执行结果
        """
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": MCPMethod.TOOLS_CALL,
            "params": {
                "name": name,
                "arguments": arguments
            }
        }
        
        response = await self.transport.send_request(request)
        return response.get("result", {}).get("content", [])
```

**2. MCP Transport 抽象**

```python
# backend/app/engines/tools/mcp/transport.py
"""
MCP Transport 抽象

支持多种传输方式：
- stdio: 标准输入输出
- http: HTTP 请求
- streamable-http: WebSocket（基础版本）
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class MCPTransport(ABC):
    """MCP Transport 抽象基类"""
    
    @abstractmethod
    async def connect(self) -> None:
        """建立连接"""
        pass
    
    @abstractmethod
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """发送请求"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """关闭连接"""
        pass

class StdioTransport(MCPTransport):
    """标准输入输出传输"""
    
    def __init__(self, command: List[str], env: Optional[Dict[str, str]] = None):
        self.command = command
        self.env = env
        self.process: Optional[subprocess.Popen] = None
    
    async def connect(self) -> None:
        """启动子进程"""
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.env
        )
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """通过标准输入输出发送请求"""
        # 实现 JSON-RPC 2.0 协议
        # 写入 stdin，读取 stdout
        pass

class HTTPTransport(MCPTransport):
    """HTTP 传输"""
    
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        self.url = url
        self.headers = headers or {}
    
    async def connect(self) -> None:
        """HTTP 连接（无需特殊处理）"""
        pass
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """通过 HTTP 发送请求"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.url,
                json=request,
                headers=self.headers
            )
            return response.json()

class StreamableHTTPTransport(MCPTransport):
    """Streamable HTTP 传输（WebSocket）"""
    
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        self.url = url
        self.headers = headers or {}
        self.websocket: Optional[WebSocket] = None
    
    async def connect(self) -> None:
        """建立 WebSocket 连接"""
        self.websocket = await websockets.connect(self.url, extra_headers=self.headers)
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """通过 WebSocket 发送请求"""
        await self.websocket.send(json.dumps(request))
        response = await self.websocket.recv()
        return json.loads(response)
```

**3. 更新 MCPClient**

```python
# backend/app/engines/tools/mcp/client.py
class MCPClient:
    """MCP 客户端（完整实现）"""
    
    def __init__(
        self,
        server_name: str,
        transport_type: str = "stdio",  # stdio / http / streamable-http
        transport_config: Dict[str, Any] = None
    ):
        self.server_name = server_name
        self.transport = self._create_transport(transport_type, transport_config)
        self.protocol = MCPProtocol(self.transport)
        self.initialized = False
    
    def _create_transport(self, transport_type: str, config: Dict[str, Any]) -> MCPTransport:
        """创建传输层"""
        if transport_type == "stdio":
            return StdioTransport(
                command=config.get("command", []),
                env=config.get("env", {})
            )
        elif transport_type == "http":
            return HTTPTransport(
                url=config.get("url", ""),
                headers=config.get("headers", {})
            )
        elif transport_type == "streamable-http":
            return StreamableHTTPTransport(
                url=config.get("url", ""),
                headers=config.get("headers", {})
            )
        else:
            raise ValueError(f"Unsupported transport type: {transport_type}")
    
    async def initialize(self) -> Dict[str, Any]:
        """初始化 MCP 连接"""
        await self.transport.connect()
        
        response = await self.protocol.initialize(
            protocol_version="2024-11-05",
            capabilities={
                "tools": {}
            },
            client_info={
                "name": "cozychat",
                "version": "1.0.0"
            }
        )
        
        self.initialized = True
        return response
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出工具"""
        if not self.initialized:
            await self.initialize()
        
        return await self.protocol.list_tools()
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """调用工具"""
        if not self.initialized:
            await self.initialize()
        
        return await self.protocol.call_tool(name, arguments)
```

#### 2.2.3 实施步骤

1. **阶段1：MCP 协议实现**（2-3天）
   - 实现 MCP 协议核心功能
   - 实现 JSON-RPC 2.0 协议
   - 编写协议测试

2. **阶段2：Transport 实现**（3-4天）
   - 实现 stdio transport
   - 实现 HTTP transport
   - 实现 streamable-http transport（基础版本）
   - 编写传输层测试

3. **阶段3：集成和优化**（2-3天）
   - 更新 MCPClient 使用新实现
   - 更新 MCPDiscovery
   - 集成测试

4. **阶段4：文档和示例**（1-2天）
   - 更新文档
   - 编写使用示例
   - 性能测试

**总计**：8-12 天

---

## 三、实施优先级

### 3.1 高优先级（必须实现）

1. **Agent 抽象优化** ✅
   - 提供统一的 Agent API
   - 保持人格系统核心创新
   - 提升代码可维护性

2. **MCP stdio transport** ✅
   - 最常用的传输方式
   - 支持本地 MCP 服务器

### 3.2 中优先级（建议实现）

1. **MCP HTTP transport** 🟡
   - 支持远程 MCP 服务器
   - 提升灵活性

2. **MCP 工具自动发现** 🟡
   - 提升用户体验
   - 减少配置工作

### 3.3 低优先级（可选实现）

1. **MCP streamable-http transport** 🟡
   - 需要 WebSocket 支持
   - 可以后续实现

2. **MCP 高级特性（Prompts, Resources）** 🟡
   - 可以后续实现
   - 需要更多测试

---

## 四、预期效果

### 4.1 Agent 抽象优化

**代码质量提升**：
- ✅ 统一的 Agent API，代码更清晰
- ✅ 更好的抽象，易于扩展
- ✅ 保持人格系统核心创新

**开发体验提升**：
- ✅ 更容易理解和使用
- ✅ 更容易测试
- ✅ 更容易扩展新功能

### 4.2 MCP 增强

**功能完整性**：
- ✅ 完整的 MCP 协议支持
- ✅ 支持多种传输方式
- ✅ 自动发现和注册工具

**用户体验提升**：
- ✅ 更容易集成 MCP 服务器
- ✅ 更稳定的工具调用
- ✅ 更好的错误处理

---

## 五、风险评估

### 5.1 Agent 抽象优化

**风险**：低
- 主要是代码重构，不改变核心逻辑
- 保持向后兼容
- 可以逐步迁移

### 5.2 MCP 增强

**风险**：中
- MCP 协议实现需要参考官方规范
- 可能需要处理各种边界情况
- 需要充分测试

**缓解措施**：
- 分阶段实施
- 充分测试
- 参考官方文档和示例

---

## 六、总结

### 6.1 我能做到什么程度？

**Agent 抽象优化**：✅ **100% 可实现**
- 完全实现统一的 Agent API
- 保持人格系统核心创新
- 提升代码质量和可维护性

**MCP 增强**：✅ **80% 可实现**
- 实现完整的 MCP 协议核心功能
- 支持 stdio 和 HTTP transport
- 支持 streamable-http transport（基础版本）
- 实现工具自动发现和注册

### 6.2 实施时间

- **Agent 抽象优化**：5-8 天
- **MCP 增强**：8-12 天
- **总计**：13-20 天（可以并行实施，实际约 15 天）

### 6.3 建议

**建议先实施 Agent 抽象优化**：
1. 风险低，收益高
2. 提升代码质量
3. 为后续优化打下基础

**然后实施 MCP 增强**：
1. 分阶段实施
2. 先实现 stdio transport
3. 再实现 HTTP transport
4. 最后实现 streamable-http transport

---

**结论**：这两个优化都可以实现，Agent 抽象优化可以 100% 实现，MCP 增强可以 80% 实现（核心功能完整，高级特性可以后续补充）。




