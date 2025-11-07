"""
核心编排器测试

测试核心编排器的所有功能，包括：
- 处理聊天请求（基础）
- 处理聊天请求（带记忆）
- 处理聊天请求（带工具）
- 流式响应
- 错误处理
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from app.core.personality.orchestrator import Orchestrator
from app.core.personality.models import Personality
from app.engines.ai.base import ChatMessage, ChatResponse, StreamChunk


class TestOrchestrator:
    """测试核心编排器"""
    
    @pytest.fixture
    def mock_personality(self):
        """Mock人格配置"""
        from app.core.personality.models import AIConfig, MemoryConfig, ToolConfig
        
        return Personality(
            id="test-personality",
            name="Test Personality",
            description="Test personality for testing",
            ai=AIConfig(
                provider="openai",
                model="gpt-3.5-turbo",
                temperature=0.7
            ),
            memory=MemoryConfig(
                enabled=True,
                save_mode="both"
            ),
            tools=ToolConfig(
                enabled=True,
                allowed_tools=["calculator", "time"]
            )
        )
    
    @pytest.fixture
    def mock_personality_manager(self, mock_personality):
        """Mock人格管理器"""
        manager = MagicMock()
        manager.get_personality = MagicMock(return_value=mock_personality)
        return manager
    
    @pytest.fixture
    def mock_memory_manager(self):
        """Mock记忆管理器"""
        manager = MagicMock()
        manager.search_memories = AsyncMock(return_value=[])
        manager.retrieve_memories = AsyncMock(return_value={"user_memories": [], "ai_memories": []})
        manager.add_memory = AsyncMock(return_value="memory-id-123")
        manager.add_conversation_turn = AsyncMock(return_value=None)
        return manager
    
    @pytest.fixture
    def mock_tool_manager(self):
        """Mock工具管理器"""
        manager = MagicMock()
        manager.get_available_tools = MagicMock(return_value=[])
        manager.get_tools_for_openai = MagicMock(return_value=[])
        manager.execute_tool = AsyncMock(return_value={"result": "test"})
        return manager
    
    @pytest.fixture
    def mock_ai_engine(self):
        """Mock AI引擎"""
        engine = MagicMock()
        engine.chat = AsyncMock(return_value=ChatResponse(
            id="chatcmpl-123",
            message=ChatMessage(role="assistant", content="Hello!"),
            model="gpt-3.5-turbo",
            finish_reason="stop",
            usage={"total_tokens": 50}
        ))
        engine.chat_stream = AsyncMock()
        return engine
    
    @pytest.fixture
    def orchestrator(self, mock_personality_manager, mock_memory_manager, mock_tool_manager, mock_ai_engine):
        """核心编排器实例"""
        # 创建orchestrator实例
        orchestrator = Orchestrator(
            personality_manager=mock_personality_manager,
            memory_manager=mock_memory_manager,
            tool_manager=mock_tool_manager
        )
        # 直接设置ai_engines字典，避免调用真实的AIEngineFactory
        orchestrator.ai_engines["test-personality"] = mock_ai_engine
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_process_chat_request_basic(self, orchestrator, mock_personality):
        """测试：处理基础聊天请求"""
        request = {
            "messages": [{"role": "user", "content": "Hello"}],
            "personality_id": "test-personality",
            "user_id": "test-user-id",
            "session_id": "test-session-id"
        }
        
        result = await orchestrator.process_chat_request(**request)
        
        assert result is not None
        # result可能是ChatResponse对象或字典
        if hasattr(result, 'message'):
            # ChatResponse对象
            assert result.message is not None
            assert hasattr(result.message, 'content') or result.message.content is not None
        elif isinstance(result, dict):
            # 字典格式
            assert "content" in result or "message" in result
        else:
            # 其他格式，至少应该存在
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_process_chat_request_with_memory(self, orchestrator, mock_personality, mock_memory_manager):
        """测试：处理带记忆的聊天请求"""
        # 设置记忆搜索结果（orchestrator调用retrieve_memories）
        from app.engines.memory.models import Memory, MemoryType, MemorySearchResult
        mock_memory = Memory(
            id="mem-1",
            user_id="test-user-id",
            session_id="test-session-id",
            content="User likes Python",
            memory_type=MemoryType.USER,
            importance=0.5
        )
        # retrieve_memories返回的是MemorySearchResult列表
        mock_search_result = MemorySearchResult(
            memory=mock_memory,
            similarity=0.9,
            distance=0.1
        )
        mock_memory_manager.retrieve_memories = AsyncMock(return_value={
            "user_memories": [mock_search_result],
            "ai_memories": []
        })
        
        request = {
            "messages": [{"role": "user", "content": "What do I like?"}],
            "personality_id": "test-personality",
            "user_id": "test-user-id",
            "session_id": "test-session-id"
        }
        
        result = await orchestrator.process_chat_request(**request)
        
        assert result is not None
        # 验证记忆检索被调用
        mock_memory_manager.retrieve_memories.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_chat_request_with_tools(self, orchestrator, mock_personality, mock_tool_manager):
        """测试：处理带工具的聊天请求"""
        # 设置工具列表（orchestrator调用get_tools_for_openai）
        mock_tool_manager.get_tools_for_openai = MagicMock(return_value=[
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "Perform calculations",
                    "parameters": {}
                }
            }
        ])
        
        request = {
            "messages": [{"role": "user", "content": "Calculate 2+2"}],
            "personality_id": "test-personality",
            "user_id": "test-user-id",
            "session_id": "test-session-id"
        }
        
        result = await orchestrator.process_chat_request(**request)
        
        assert result is not None
        # 验证工具管理器被调用
        mock_tool_manager.get_tools_for_openai.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_chat_request_stream(self, orchestrator, mock_personality, mock_ai_engine):
        """测试：处理流式聊天请求"""
        # 设置流式响应（需要返回异步生成器）
        async def mock_stream(*args, **kwargs):
            chunk1 = StreamChunk(
                id="chatcmpl-123",
                delta={"content": "Hello"},
                model="gpt-3.5-turbo"
            )
            # 添加content属性以匹配orchestrator的期望
            chunk1.content = "Hello"
            yield chunk1
            
            chunk2 = StreamChunk(
                id="chatcmpl-123",
                delta={"content": " there"},
                model="gpt-3.5-turbo"
            )
            chunk2.content = " there"
            yield chunk2
        
        # 直接设置chat_stream为异步生成器函数（不是AsyncMock）
        # 需要更新orchestrator中的ai_engine引用
        # chat_stream应该是一个异步生成器函数，调用时返回异步生成器
        orchestrator.ai_engines["test-personality"].chat_stream = mock_stream
        
        request = {
            "messages": [{"role": "user", "content": "Hello"}],
            "personality_id": "test-personality",
            "user_id": "test-user-id",
            "session_id": "test-session-id",
            "stream": True
        }
        
        chunks = []
        # orchestrator.process_chat_request在stream=True时返回异步生成器
        # 需要先await获取生成器，然后遍历
        result = orchestrator.process_chat_request(**request)
        # result是协程，需要await获取异步生成器
        async_gen = await result if hasattr(result, '__await__') else result
        async for chunk in async_gen:
            chunks.append(chunk)
        
        assert len(chunks) > 0
    
    @pytest.mark.asyncio
    async def test_process_chat_request_error_handling(self, orchestrator, mock_personality, mock_ai_engine):
        """测试：处理聊天请求错误处理"""
        # 设置AI引擎抛出异常
        mock_ai_engine.chat = AsyncMock(side_effect=Exception("AI Engine Error"))
        
        request = {
            "messages": [{"role": "user", "content": "Hello"}],
            "personality_id": "test-personality",
            "user_id": "test-user-id",
            "session_id": "test-session-id"
        }
        
        with pytest.raises(Exception):
            await orchestrator.process_chat_request(**request)

