"""
AI引擎注册中心测试

测试AI引擎注册和管理功能
"""

# 第三方库
import pytest

# 本地库
from app.engines.ai.base import AIEngineBase, ChatMessage, ChatResponse
from app.engines.ai.registry import AIEngineRegistry


class MockAIEngine(AIEngineBase):
    """模拟AI引擎，用于测试"""
    
    async def chat(self, messages, **kwargs):
        return ChatResponse(
            id="mock-123",
            message=ChatMessage(role="assistant", content="Mock response"),
            model="mock-model"
        )
    
    async def chat_stream(self, messages, **kwargs):
        yield


class TestAIEngineRegistry:
    """测试AI引擎注册中心"""
    
    def test_singleton(self):
        """测试单例模式"""
        registry1 = AIEngineRegistry()
        registry2 = AIEngineRegistry()
        assert registry1 is registry2
    
    def test_register_engine(self):
        """测试注册引擎"""
        AIEngineRegistry.register("mock", MockAIEngine)
        assert AIEngineRegistry.is_registered("mock")
    
    def test_get_engine_class(self):
        """测试获取引擎类"""
        AIEngineRegistry.register("mock", MockAIEngine)
        engine_class = AIEngineRegistry.get_engine_class("mock")
        assert engine_class == MockAIEngine
    
    def test_list_engines(self):
        """测试列出所有引擎"""
        AIEngineRegistry.register("mock", MockAIEngine)
        engines = AIEngineRegistry.list_engines()
        assert "mock" in engines
        assert "openai" in engines  # 内置引擎
        assert "ollama" in engines  # 内置引擎
    
    def test_is_registered(self):
        """测试检查引擎是否注册"""
        AIEngineRegistry.register("mock", MockAIEngine)
        assert AIEngineRegistry.is_registered("mock") is True
        assert AIEngineRegistry.is_registered("nonexistent") is False
    
    def test_unregister_engine(self):
        """测试注销引擎"""
        AIEngineRegistry.register("mock_temp", MockAIEngine)
        assert AIEngineRegistry.is_registered("mock_temp")
        
        AIEngineRegistry.unregister("mock_temp")
        assert not AIEngineRegistry.is_registered("mock_temp")
    
    def test_register_invalid_class(self):
        """测试注册无效类"""
        class InvalidClass:
            pass
        
        with pytest.raises(ValueError):
            AIEngineRegistry.register("invalid", InvalidClass)

