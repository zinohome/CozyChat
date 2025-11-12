"""
AI引擎基类

定义所有AI引擎的统一接口
"""

# 标准库
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional

# 本地库
from app.utils.logger import logger


class MessageRole(str, Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


@dataclass
class ChatMessage:
    """聊天消息数据类
    
    Attributes:
        role: 消息角色
        content: 消息内容
        name: 发送者名称（可选）
        function_call: 函数调用信息（可选）
        tool_calls: 工具调用列表（可选）
    """
    role: str
    content: Optional[str] = None
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        注意：
        - assistant 消息必须有 content 字段（即使为空字符串），除非有 tool_calls
        - 如果有 tool_calls，content 可以为 null
        """
        result = {"role": self.role}
        
        # 处理 content 字段
        if self.role == "assistant":
            # assistant 消息：如果有 tool_calls，content 可以为 null；否则必须有 content（即使是空字符串）
            if self.tool_calls:
                # 有 tool_calls 时，content 可以为 null，不包含在字典中
                if self.content is not None:
                    result["content"] = self.content
            else:
                # 没有 tool_calls 时，content 必须存在（即使是空字符串）
                result["content"] = self.content if self.content is not None else ""
        else:
            # 其他角色：只有当 content 不为 None 时才添加
            if self.content is not None:
                result["content"] = self.content
        
        # 处理 name 字段（对于 tool 角色，使用 tool_call_id）
        if self.role == "tool" and self.name:
            result["tool_call_id"] = self.name
        elif self.name:
            result["name"] = self.name
        
        if self.function_call:
            result["function_call"] = self.function_call
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        return result


@dataclass
class ChatResponse:
    """聊天响应数据类
    
    Attributes:
        id: 响应ID
        message: 助手消息
        model: 使用的模型
        finish_reason: 完成原因
        usage: Token使用情况
        created: 创建时间戳
    """
    id: str
    message: ChatMessage
    model: str
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    created: int = field(default_factory=lambda: int(datetime.utcnow().timestamp()))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为OpenAI格式的字典"""
        return {
            "id": self.id,
            "object": "chat.completion",
            "created": self.created,
            "model": self.model,
            "choices": [
                {
                    "index": 0,
                    "message": self.message.to_dict(),
                    "finish_reason": self.finish_reason
                }
            ],
            "usage": self.usage or {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }


@dataclass
class StreamChunk:
    """流式响应数据块
    
    Attributes:
        id: 响应ID
        delta: 增量内容
        model: 使用的模型
        finish_reason: 完成原因
        created: 创建时间戳
    """
    id: str
    delta: Dict[str, Any]
    model: str
    finish_reason: Optional[str] = None
    created: int = field(default_factory=lambda: int(datetime.utcnow().timestamp()))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为OpenAI流式格式的字典"""
        return {
            "id": self.id,
            "object": "chat.completion.chunk",
            "created": self.created,
            "model": self.model,
            "choices": [
                {
                    "index": 0,
                    "delta": self.delta,
                    "finish_reason": self.finish_reason
                }
            ]
        }


class AIEngineBase(ABC):
    """AI引擎基类
    
    所有AI引擎实现必须继承此类并实现抽象方法
    
    Attributes:
        engine_name: 引擎名称
        model: 模型名称
        api_key: API密钥
        base_url: API基础URL
        default_params: 默认参数
    """
    
    def __init__(
        self,
        engine_name: str,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """初始化AI引擎
        
        Args:
            engine_name: 引擎名称
            model: 模型名称
            api_key: API密钥
            base_url: API基础URL
            **kwargs: 其他参数
        """
        self.engine_name = engine_name
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.default_params = kwargs
        
        logger.info(
            f"Initializing {engine_name} engine",
            extra={
                "engine": engine_name,
                "model": model,
                "base_url": base_url
            }
        )
    
    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ChatResponse:
        """生成聊天响应（非流式）
        
        Args:
            messages: 消息列表
            stream: 是否流式输出
            temperature: 温度参数
            max_tokens: 最大token数
            tools: 工具列表
            **kwargs: 其他参数
            
        Returns:
            ChatResponse: 聊天响应
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """生成聊天响应（流式）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            tools: 工具列表
            **kwargs: 其他参数
            
        Yields:
            StreamChunk: 流式响应数据块
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 引擎是否健康
        """
        try:
            # 简单的健康检查：发送一个测试消息
            test_message = ChatMessage(role=MessageRole.USER, content="Hi")
            await self.chat(messages=[test_message], max_tokens=5)
            return True
        except Exception as e:
            logger.error(f"Health check failed for {self.engine_name}: {e}")
            return False
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.engine_name}, model={self.model})>"

