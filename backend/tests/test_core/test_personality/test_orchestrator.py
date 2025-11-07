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
        manager.add_memory = AsyncMock(return_value="memory-id-123")
        return manager
    
    @pytest.fixture
    def mock_tool_manager(self):
        """Mock工具管理器"""
        manager = MagicMock()
        manager.get_available_tools = MagicMock(return_value=[])
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
        with patch('app.core.personality.orchestrator.AIEngineFactory') as mock_factory:
            mock_factory_instance = MagicMock()
            mock_factory_instance.create_engine.return_value = mock_ai_engine
            mock_factory.return_value = mock_factory_instance
            
            orchestrator = Orchestrator(
                personality_manager=mock_personality_manager,
                memory_manager=mock_memory_manager,
                tool_manager=mock_tool_manager
            )
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
        assert "content" in result or "message" in result
    
    @pytest.mark.asyncio
    async def test_process_chat_request_with_memory(self, orchestrator, mock_personality, mock_memory_manager):
        """测试：处理带记忆的聊天请求"""
        # 设置记忆搜索结果
        mock_memory_manager.search_memories = AsyncMock(return_value=[
            {
                "id": "mem-1",
                "content": "User likes Python",
                "type": "user"
            }
        ])
        
        request = {
            "messages": [{"role": "user", "content": "What do I like?"}],
            "personality_id": "test-personality",
            "user_id": "test-user-id",
            "session_id": "test-session-id"
        }
        
        result = await orchestrator.process_chat_request(**request)
        
        assert result is not None
        # 验证记忆搜索被调用
        mock_memory_manager.search_memories.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_chat_request_with_tools(self, orchestrator, mock_personality, mock_tool_manager):
        """测试：处理带工具的聊天请求"""
        # 设置工具列表
        mock_tool_manager.get_available_tools = MagicMock(return_value=[
            {
                "name": "calculator",
                "description": "Perform calculations",
                "parameters": {}
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
        mock_tool_manager.get_available_tools.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_chat_request_stream(self, orchestrator, mock_personality, mock_ai_engine):
        """测试：处理流式聊天请求"""
        # 设置流式响应
        async def mock_stream():
            yield StreamChunk(
                id="chatcmpl-123",
                delta={"content": "Hello"},
                model="gpt-3.5-turbo"
            )
            yield StreamChunk(
                id="chatcmpl-123",
                delta={"content": " there"},
                model="gpt-3.5-turbo"
            )
        
        mock_ai_engine.chat_stream = mock_stream
        
        request = {
            "messages": [{"role": "user", "content": "Hello"}],
            "personality_id": "test-personality",
            "user_id": "test-user-id",
            "session_id": "test-session-id",
            "stream": True
        }
        
        chunks = []
        async for chunk in orchestrator.process_chat_request(**request):
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

