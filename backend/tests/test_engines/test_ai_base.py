"""
AI引擎基类测试

测试AI引擎基类的功能
"""

# 第三方库
import pytest

# 本地库
from app.engines.ai.base import (
    AIEngineBase,
    ChatMessage,
    ChatResponse,
    MessageRole,
    StreamChunk,
)


class TestMessageRole:
    """测试MessageRole枚举"""
    
    def test_message_roles(self):
        """测试所有消息角色"""
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.FUNCTION == "function"
        assert MessageRole.TOOL == "tool"


class TestChatMessage:
    """测试ChatMessage数据类"""
    
    def test_create_simple_message(self):
        """测试创建简单消息"""
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.name is None
    
    def test_message_to_dict(self):
        """测试消息转换为字典"""
        msg = ChatMessage(role="user", content="Hello", name="Alice")
        msg_dict = msg.to_dict()
        
        assert msg_dict["role"] == "user"
        assert msg_dict["content"] == "Hello"
        assert msg_dict["name"] == "Alice"
    
    def test_message_with_function_call(self):
        """测试带函数调用的消息"""
        msg = ChatMessage(
            role="assistant",
            function_call={"name": "test_func", "arguments": "{}"}
        )
        
        assert msg.function_call is not None
        assert msg.function_call["name"] == "test_func"


class TestChatResponse:
    """测试ChatResponse数据类"""
    
    def test_create_response(self):
        """测试创建响应"""
        message = ChatMessage(role="assistant", content="Hi there!")
        response = ChatResponse(
            id="test-123",
            message=message,
            model="gpt-3.5-turbo",
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        )
        
        assert response.id == "test-123"
        assert response.message.content == "Hi there!"
        assert response.model == "gpt-3.5-turbo"
        assert response.finish_reason == "stop"
    
    def test_response_to_dict(self):
        """测试响应转换为字典"""
        message = ChatMessage(role="assistant", content="Hi")
        response = ChatResponse(
            id="test-123",
            message=message,
            model="gpt-3.5-turbo"
        )
        
        response_dict = response.to_dict()
        
        assert response_dict["id"] == "test-123"
        assert response_dict["object"] == "chat.completion"
        assert response_dict["model"] == "gpt-3.5-turbo"
        assert "choices" in response_dict
        assert len(response_dict["choices"]) == 1
        assert response_dict["choices"][0]["message"]["content"] == "Hi"


class TestStreamChunk:
    """测试StreamChunk数据类"""
    
    def test_create_chunk(self):
        """测试创建流式数据块"""
        chunk = StreamChunk(
            id="test-123",
            delta={"content": "Hello"},
            model="gpt-3.5-turbo"
        )
        
        assert chunk.id == "test-123"
        assert chunk.delta["content"] == "Hello"
        assert chunk.model == "gpt-3.5-turbo"
    
    def test_chunk_to_dict(self):
        """测试数据块转换为字典"""
        chunk = StreamChunk(
            id="test-123",
            delta={"role": "assistant"},
            model="gpt-3.5-turbo"
        )
        
        chunk_dict = chunk.to_dict()
        
        assert chunk_dict["id"] == "test-123"
        assert chunk_dict["object"] == "chat.completion.chunk"
        assert chunk_dict["model"] == "gpt-3.5-turbo"
        assert "choices" in chunk_dict

