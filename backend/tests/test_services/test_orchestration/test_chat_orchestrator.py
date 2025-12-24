"""
ChatOrchestrator单元测试

测试编排器的所有功能，包括：
- 处理非流式请求
- 处理流式请求
- 错误处理
- 服务编排
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.services.orchestration.chat_orchestrator import ChatOrchestrator
from app.schemas.chat import ChatCompletionRequest, ChatCompletionUsage
from app.models.user import User


class TestChatOrchestrator:
    """ChatOrchestrator单元测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = AsyncMock()
        return db
    
    @pytest.fixture
    def mock_user(self):
        """创建模拟用户"""
        user = MagicMock(spec=User)
        # 使用UUID格式的user_id，符合PostgreSQL UUID类型要求
        user.id = str(uuid.uuid4())
        user.username = "testuser"
        return user
    
    @pytest.fixture
    def mock_context_service(self):
        """创建模拟上下文服务"""
        service = AsyncMock()
        service.build_context = AsyncMock(return_value=MagicMock(
            messages=[],
            memories=[],
            user_profile=None
        ))
        return service
    
    @pytest.fixture
    def mock_message_service(self):
        """创建模拟消息服务"""
        service = AsyncMock()
        service.save_conversation_turn = AsyncMock(return_value=True)
        return service
    
    @pytest.fixture
    def mock_tool_service(self):
        """创建模拟工具服务"""
        service = AsyncMock()
        service.prepare_tools = AsyncMock(return_value=[])
        service.execute_tool_call = AsyncMock(return_value=None)
        return service
    
    @pytest.fixture
    def mock_ai_engine(self):
        """创建模拟AI引擎"""
        engine = AsyncMock()
        engine.chat = AsyncMock(return_value=MagicMock(
            message=MagicMock(content="Test response"),
            usage=MagicMock(total_tokens=100)
        ))
        engine.chat_stream = AsyncMock()
        return engine
    
    @pytest.fixture
    def mock_personality_registry(self):
        """创建模拟人格注册表"""
        registry = MagicMock()
        registry.get_personality = MagicMock(return_value=MagicMock(
            id="test-personality",
            ai=MagicMock(provider="openai", model="gpt-3.5-turbo")
        ))
        return registry
    
    @pytest.fixture
    def mock_tool_factory(self):
        """创建模拟工具工厂"""
        factory = MagicMock()
        factory.create_manager = MagicMock(return_value=MagicMock())
        return factory
    
    @pytest.fixture
    def mock_engine_pool(self):
        """创建模拟引擎池"""
        pool = MagicMock()
        pool.get_engine = MagicMock(return_value=MagicMock())
        return pool
    
    @pytest.fixture
    def mock_context_builder(self):
        """创建模拟上下文构建器（旧版）"""
        builder = AsyncMock()
        builder.build_context = AsyncMock(return_value=MagicMock(
            messages=[],
            memories=[],
            user_profile=None
        ))
        return builder
    
    @pytest.fixture
    def mock_memory_manager(self):
        """创建模拟记忆管理器"""
        manager = MagicMock()
        manager.retrieve_memories = AsyncMock(return_value={
            "user_memories": [],
            "ai_memories": []
        })
        return manager
    
    @pytest.fixture
    def orchestrator(
        self,
        mock_personality_registry,
        mock_tool_factory,
        mock_engine_pool,
        mock_context_builder,
        mock_memory_manager,
        mock_context_service
    ):
        """创建ChatOrchestrator实例"""
        return ChatOrchestrator(
            personality_registry=mock_personality_registry,
            tool_factory=mock_tool_factory,
            engine_pool=mock_engine_pool,
            context_builder=mock_context_builder,
            memory_manager=mock_memory_manager,
            context_service=mock_context_service
        )
    
    @pytest.mark.asyncio
    async def test_process_request_non_stream_success(
        self,
        orchestrator,
        mock_user,
        mock_ai_engine,
        mock_db
    ):
        """测试：成功处理非流式请求"""
        # Arrange
        request = ChatCompletionRequest(
            messages=[{"role": "user", "content": "Hello"}],
            personality_id="test-personality",
            stream=False
        )
        
        # Mock所有内部方法，避免真实数据库调用
        orchestrator._prepare_request = AsyncMock(return_value=MagicMock(
            personality_id="test-personality",
            user_id=str(uuid.uuid4()),  # 使用UUID格式
            session_id=None,
            session=None,
            user_obj=mock_user,
            personality=MagicMock(
                id="test-personality",
                ai=MagicMock(provider="openai", model="gpt-3.5-turbo")
            ),
            model="gpt-3.5-turbo",
            engine_type="openai",
            max_tokens=4096
        ))
        
        # Mock context_service.build_context
        from app.schemas.context import ContextBundle
        mock_context_bundle = ContextBundle(
            system_prompts=[],
            recent_messages=[],
            summarized_history=[],
            retrieved_memories=[],
            user_profile=None,
            total_tokens=0,
            metadata={}
        )
        orchestrator.context_service.build_context = AsyncMock(return_value=mock_context_bundle)
        
        orchestrator._prepare_tools = AsyncMock(return_value=[])
        
        # Mock引擎池返回AI引擎
        orchestrator.engine_pool.get_engine.return_value = mock_ai_engine
        
        # Mock ChatService
        with patch('app.services.orchestration.chat_orchestrator.ChatService') as mock_chat_service_class:
            mock_chat_service = AsyncMock()
            mock_chat_service.generate_response = AsyncMock(return_value=MagicMock(
                id="test-id",
                created=1234567890,
                model="gpt-3.5-turbo",
                message=MagicMock(to_dict=lambda: {"role": "assistant", "content": "Test response"}),
                finish_reason="stop",
                usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            ))
            mock_chat_service_class.return_value = mock_chat_service
            
            # Act
            result = await orchestrator.process_request(
                request=request,
                user=mock_user,
                db=mock_db
            )
            
            # Assert
            assert result is not None
            # 验证使用了context_service
            orchestrator.context_service.build_context.assert_called_once()
            # 验证ChatService被调用
            mock_chat_service.generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_request_stream_success(
        self,
        orchestrator,
        mock_user,
        mock_ai_engine,
        mock_db
    ):
        """测试：成功处理流式请求"""
        # Arrange
        request = ChatCompletionRequest(
            messages=[{"role": "user", "content": "Hello"}],
            personality_id="test-personality",
            stream=True
        )
        
        # Mock所有内部方法
        orchestrator._prepare_request = AsyncMock(return_value=MagicMock(
            personality_id="test-personality",
            user_id=str(uuid.uuid4()),  # 使用UUID格式
            session_id=None,
            session=None,
            user_obj=mock_user,
            personality=MagicMock(
                id="test-personality",
                ai=MagicMock(provider="openai", model="gpt-3.5-turbo")
            ),
            model="gpt-3.5-turbo",
            engine_type="openai",
            max_tokens=4096
        ))
        
        orchestrator._build_context = AsyncMock(return_value=[
            MagicMock(role="user", content="Hello")
        ])
        
        orchestrator._prepare_tools = AsyncMock(return_value=[])
        
        # Mock流式响应
        async def mock_stream():
            yield "chunk1"
            yield "chunk2"
        
        mock_ai_engine.chat_stream.return_value = mock_stream()
        orchestrator.engine_pool.get_engine.return_value = mock_ai_engine
        
        # Mock StreamChatService
        with patch('app.services.orchestration.chat_orchestrator.StreamChatService') as mock_stream_service_class:
            mock_stream_service = MagicMock()
            mock_stream_service.generate_stream = MagicMock(return_value=mock_stream())
            mock_stream_service_class.return_value = mock_stream_service
            
            # Act
            result = await orchestrator.process_request(
                request=request,
                user=mock_user,
                db=mock_db
            )
            
            # Assert
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_process_request_with_tools(
        self,
        orchestrator,
        mock_user,
        mock_ai_engine,
        mock_db
    ):
        """测试：处理带工具调用的请求"""
        # Arrange
        request = ChatCompletionRequest(
            messages=[{"role": "user", "content": "What's the weather?"}],
            personality_id="test-personality",
            stream=False
        )
        
        # Mock所有内部方法
        orchestrator._prepare_request = AsyncMock(return_value=MagicMock(
            personality_id="test-personality",
            user_id=str(uuid.uuid4()),  # 使用UUID格式
            session_id=None,
            session=None,
            user_obj=mock_user,
            personality=MagicMock(
                id="test-personality",
                ai=MagicMock(provider="openai", model="gpt-3.5-turbo"),
                tools=MagicMock(enabled=True)
            ),
            model="gpt-3.5-turbo",
            engine_type="openai",
            max_tokens=4096
        ))
        
        orchestrator._build_context = AsyncMock(return_value=[
            MagicMock(role="user", content="What's the weather?")
        ])
        
        orchestrator._prepare_tools = AsyncMock(return_value=[
            MagicMock(name="get_weather")
        ])
        
        # Mock工具调用响应
        mock_response = MagicMock()
        mock_response.message = MagicMock(content="")
        mock_response.tool_calls = [MagicMock(
            id="call-1",
            function=MagicMock(name="get_weather", arguments='{"location": "Beijing"}')
        )]
        mock_ai_engine.chat.return_value = mock_response
        orchestrator.engine_pool.get_engine.return_value = mock_ai_engine
        
        # Mock ChatService
        with patch('app.services.orchestration.chat_orchestrator.ChatService') as mock_chat_service_class:
            mock_chat_service = AsyncMock()
            mock_chat_service.generate_response = AsyncMock(return_value=MagicMock(
                id="test-id",
                created=1234567890,
                model="gpt-3.5-turbo",
                message=MagicMock(to_dict=lambda: {"role": "assistant", "content": "Test response"}),
                finish_reason="stop",
                usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            ))
            mock_chat_service_class.return_value = mock_chat_service
            
            # Act
            result = await orchestrator.process_request(
                request=request,
                user=mock_user,
                db=mock_db
            )
            
            # Assert
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_process_request_error_handling(
        self,
        orchestrator,
        mock_user,
        mock_ai_engine,
        mock_db
    ):
        """测试：错误处理"""
        # Arrange
        request = ChatCompletionRequest(
            messages=[{"role": "user", "content": "Hello"}],
            personality_id="test-personality",
            stream=False
        )
        
        # Mock _prepare_request抛出异常
        orchestrator._prepare_request = AsyncMock(side_effect=Exception("Preparation error"))
        
        # Act & Assert
        with pytest.raises(Exception):
            await orchestrator.process_request(
                request=request,
                user=mock_user,
                db=mock_db
            )
