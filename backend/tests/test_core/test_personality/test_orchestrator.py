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
        # 需要await获取生成器
        async_gen = await orchestrator.process_chat_request(**request)
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
    
    @pytest.mark.asyncio
    async def test_get_or_create_ai_engine_existing(self, orchestrator, mock_personality, mock_ai_engine):
        """测试：获取已存在的AI引擎"""
        # 引擎已存在
        result = await orchestrator._get_or_create_ai_engine(mock_personality)
        
        assert result == mock_ai_engine
    
    @pytest.mark.asyncio
    async def test_get_or_create_ai_engine_new(self, orchestrator, mock_personality, mocker):
        """测试：创建新的AI引擎"""
        # 移除现有引擎
        orchestrator.ai_engines.clear()
        
        # Mock AIEngineFactory
        mock_factory = mocker.patch('app.core.personality.orchestrator.AIEngineFactory.create_engine')
        mock_factory.return_value = MagicMock()
        
        result = await orchestrator._get_or_create_ai_engine(mock_personality)
        
        assert result is not None
        assert mock_personality.id in orchestrator.ai_engines
        mock_factory.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_memories_enabled(self, orchestrator, mock_personality, mock_memory_manager):
        """测试：检索记忆（启用）"""
        from app.engines.memory.models import Memory, MemoryType, MemorySearchResult
        
        mock_memory = Memory(
            id="mem-1",
            user_id="test-user-id",
            session_id="test-session-id",
            content="User likes Python",
            memory_type=MemoryType.USER,
            importance=0.5
        )
        mock_search_result = MemorySearchResult(
            memory=mock_memory,
            similarity=0.9,
            distance=0.1
        )
        mock_memory_manager.retrieve_memories = AsyncMock(return_value={
            "user_memories": [mock_search_result],
            "ai_memories": []
        })
        
        messages = [{"role": "user", "content": "What do I like?"}]
        result = await orchestrator._retrieve_memories(
            personality=mock_personality,
            messages=messages,
            user_id="test-user-id",
            session_id="test-session-id"
        )
        
        assert isinstance(result, dict)
        assert "user_memories" in result
        assert "ai_memories" in result
        mock_memory_manager.retrieve_memories.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_memories_disabled(self, orchestrator, mock_personality):
        """测试：检索记忆（禁用）"""
        # 禁用记忆
        mock_personality.memory.enabled = False
        
        messages = [{"role": "user", "content": "Hello"}]
        result = await orchestrator._retrieve_memories(
            personality=mock_personality,
            messages=messages,
            user_id="test-user-id",
            session_id="test-session-id"
        )
        
        assert result == {"user_memories": [], "ai_memories": []}
    
    @pytest.mark.asyncio
    async def test_retrieve_memories_no_user_message(self, orchestrator, mock_personality, mock_memory_manager):
        """测试：检索记忆（无用户消息）"""
        messages = [{"role": "assistant", "content": "Hello"}]
        result = await orchestrator._retrieve_memories(
            personality=mock_personality,
            messages=messages,
            user_id="test-user-id",
            session_id="test-session-id"
        )
        
        assert result == {"user_memories": [], "ai_memories": []}
        mock_memory_manager.retrieve_memories.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_retrieve_memories_error(self, orchestrator, mock_personality, mock_memory_manager):
        """测试：检索记忆错误处理"""
        # Mock retrieve_memories抛出异常
        mock_memory_manager.retrieve_memories = AsyncMock(side_effect=Exception("Memory error"))
        
        messages = [{"role": "user", "content": "Hello"}]
        result = await orchestrator._retrieve_memories(
            personality=mock_personality,
            messages=messages,
            user_id="test-user-id",
            session_id="test-session-id"
        )
        
        # 错误应该被捕获，返回空记忆
        assert result == {"user_memories": [], "ai_memories": []}
    
    def test_build_system_prompt_without_memories(self, orchestrator, mock_personality):
        """测试：构建系统提示（无记忆）"""
        memories = {"user_memories": [], "ai_memories": []}
        result = orchestrator._build_system_prompt(mock_personality, memories)
        
        assert isinstance(result, str)
        assert result == mock_personality.ai.system_prompt
    
    def test_build_system_prompt_with_memories(self, orchestrator, mock_personality):
        """测试：构建系统提示（有记忆）"""
        from app.engines.memory.models import Memory, MemoryType, MemorySearchResult
        
        mock_memory = Memory(
            id="mem-1",
            user_id="test-user-id",
            session_id="test-session-id",
            content="User likes Python",
            memory_type=MemoryType.USER,
            importance=0.5
        )
        mock_search_result = MemorySearchResult(
            memory=mock_memory,
            similarity=0.9,
            distance=0.1
        )
        
        memories = {
            "user_memories": [mock_search_result],
            "ai_memories": []
        }
        result = orchestrator._build_system_prompt(mock_personality, memories)
        
        assert isinstance(result, str)
        assert "相关记忆" in result
        assert "User likes Python" in result
    
    @pytest.mark.asyncio
    async def test_prepare_tools_enabled(self, orchestrator, mock_personality, mock_tool_manager):
        """测试：准备工具（启用）"""
        mock_tool_manager.get_tools_for_openai = MagicMock(return_value=[
            {"type": "function", "function": {"name": "calculator"}}
        ])
        
        result = await orchestrator._prepare_tools(mock_personality)
        
        assert isinstance(result, list)
        assert len(result) == 1
        mock_tool_manager.get_tools_for_openai.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prepare_tools_disabled(self, orchestrator, mock_personality):
        """测试：准备工具（禁用）"""
        # 禁用工具
        mock_personality.tools.enabled = False
        
        result = await orchestrator._prepare_tools(mock_personality)
        
        assert result == []
    
    def test_build_full_messages_with_system_prompt(self, orchestrator):
        """测试：构建完整消息列表（有系统提示）"""
        system_prompt = "You are a helpful assistant."
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        result = orchestrator._build_full_messages(system_prompt, messages)
        
        assert isinstance(result, list)
        assert len(result) == 3  # system + 2 messages
        assert result[0].role == "system"
        assert result[0].content == system_prompt
    
    def test_build_full_messages_without_system_prompt(self, orchestrator):
        """测试：构建完整消息列表（无系统提示）"""
        system_prompt = ""
        messages = [{"role": "user", "content": "Hello"}]
        
        result = orchestrator._build_full_messages(system_prompt, messages)
        
        assert isinstance(result, list)
        assert len(result) == 1  # 只有1条消息
        assert result[0].role == "user"
    
    @pytest.mark.asyncio
    async def test_generate_with_memory_saving(self, orchestrator, mock_personality, mock_memory_manager, mock_ai_engine):
        """测试：生成回复（保存记忆）"""
        messages = [
            ChatMessage(role="system", content="You are helpful"),
            ChatMessage(role="user", content="Hello")
        ]
        
        result = await orchestrator._generate(
            ai_engine=mock_ai_engine,
            messages=messages,
            tools=[],
            user_id="test-user-id",
            session_id="test-session-id",
            personality=mock_personality,
            start_time=0.0
        )
        
        assert isinstance(result, dict)
        assert "content" in result
        assert "role" in result
        assert "usage" in result
        assert "elapsed_time" in result
        # 验证记忆保存被调用
        mock_memory_manager.add_conversation_turn.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_without_memory_saving(self, orchestrator, mock_personality, mock_memory_manager, mock_ai_engine):
        """测试：生成回复（不保存记忆）"""
        # 禁用记忆
        mock_personality.memory.enabled = False
        
        messages = [
            ChatMessage(role="system", content="You are helpful"),
            ChatMessage(role="user", content="Hello")
        ]
        
        result = await orchestrator._generate(
            ai_engine=mock_ai_engine,
            messages=messages,
            tools=[],
            user_id="test-user-id",
            session_id="test-session-id",
            personality=mock_personality,
            start_time=0.0
        )
        
        assert isinstance(result, dict)
        # 验证记忆保存未被调用
        mock_memory_manager.add_conversation_turn.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_generate_error(self, orchestrator, mock_personality, mock_ai_engine):
        """测试：生成回复错误处理"""
        # Mock AI引擎抛出异常
        mock_ai_engine.chat = AsyncMock(side_effect=Exception("Generation error"))
        
        messages = [ChatMessage(role="user", content="Hello")]
        
        with pytest.raises(Exception):
            await orchestrator._generate(
                ai_engine=mock_ai_engine,
                messages=messages,
                tools=[],
                user_id="test-user-id",
                session_id="test-session-id",
                personality=mock_personality,
                start_time=0.0
            )
    
    @pytest.mark.asyncio
    async def test_stream_generate_success(self, orchestrator, mock_personality, mock_memory_manager, mock_ai_engine):
        """测试：流式生成成功"""
        # 设置流式响应
        async def mock_stream(*args, **kwargs):
            chunk = StreamChunk(
                id="chatcmpl-123",
                delta={"content": "Hello"},
                model="gpt-3.5-turbo"
            )
            chunk.content = "Hello"
            yield chunk
        
        mock_ai_engine.chat_stream = mock_stream
        
        messages = [
            ChatMessage(role="system", content="You are helpful"),
            ChatMessage(role="user", content="Hello")
        ]
        
        chunks = []
        async for chunk in orchestrator._stream_generate(
            ai_engine=mock_ai_engine,
            messages=messages,
            tools=[],
            user_id="test-user-id",
            session_id="test-session-id",
            personality=mock_personality,
            start_time=0.0
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert all("content" in chunk for chunk in chunks)
        # 验证记忆保存被调用
        mock_memory_manager.add_conversation_turn.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stream_generate_without_memory(self, orchestrator, mock_personality, mock_memory_manager, mock_ai_engine):
        """测试：流式生成（不保存记忆）"""
        # 禁用记忆
        mock_personality.memory.enabled = False
        
        # 设置流式响应
        async def mock_stream(*args, **kwargs):
            chunk = StreamChunk(
                id="chatcmpl-123",
                delta={"content": "Hello"},
                model="gpt-3.5-turbo"
            )
            chunk.content = "Hello"
            yield chunk
        
        mock_ai_engine.chat_stream = mock_stream
        
        messages = [ChatMessage(role="user", content="Hello")]
        
        chunks = []
        async for chunk in orchestrator._stream_generate(
            ai_engine=mock_ai_engine,
            messages=messages,
            tools=[],
            user_id="test-user-id",
            session_id="test-session-id",
            personality=mock_personality,
            start_time=0.0
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        # 验证记忆保存未被调用
        mock_memory_manager.add_conversation_turn.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_stream_generate_error(self, orchestrator, mock_personality, mock_ai_engine):
        """测试：流式生成错误处理"""
        # Mock流式响应抛出异常
        async def failing_stream(*args, **kwargs):
            raise Exception("Stream error")
            yield  # 永远不会执行
        
        mock_ai_engine.chat_stream = failing_stream
        
        messages = [ChatMessage(role="user", content="Hello")]
        
        # _stream_generate在错误时会yield错误消息，而不是抛出异常
        chunks = []
        async for chunk in orchestrator._stream_generate(
            ai_engine=mock_ai_engine,
            messages=messages,
            tools=[],
            user_id="test-user-id",
            session_id="test-session-id",
            personality=mock_personality,
            start_time=0.0
        ):
            chunks.append(chunk)
        
        # 应该有一个错误消息chunk
        assert len(chunks) > 0
        assert any("error" in chunk or "生成失败" in chunk.get("content", "") for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_process_chat_request_personality_not_found(self, orchestrator, mock_personality_manager):
        """测试：处理聊天请求（人格不存在）"""
        # Mock personality_manager返回None
        mock_personality_manager.get_personality = MagicMock(return_value=None)
        
        request = {
            "messages": [{"role": "user", "content": "Hello"}],
            "personality_id": "nonexistent-personality",
            "user_id": "test-user-id",
            "session_id": "test-session-id"
        }
        
        with pytest.raises(ValueError, match="Personality not found"):
            await orchestrator.process_chat_request(**request)

