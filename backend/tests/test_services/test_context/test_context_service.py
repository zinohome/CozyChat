"""
ContextService单元测试

测试上下文服务的所有功能，包括：
- 构建完整上下文
- 消息检索
- 摘要加载
- 记忆检索
- 用户画像加载
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Any

from app.services.context.context_service import ContextService
from app.services.context.message_retriever import MessageRetriever
from app.services.context.summary_loader import SummaryLoader
from app.services.context.memory_retriever import MemoryRetriever
from app.services.context.user_profile_loader import UserProfileLoader
from app.services.context.context_assembler import ContextAssembler


class TestContextService:
    """ContextService单元测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_message_retriever(self):
        """创建模拟消息检索器"""
        retriever = MagicMock(spec=MessageRetriever)
        retriever.get_recent_messages = AsyncMock(return_value=[])
        return retriever
    
    @pytest.fixture
    def mock_summary_loader(self):
        """创建模拟摘要加载器"""
        loader = MagicMock(spec=SummaryLoader)
        loader.load_history_summaries = AsyncMock(return_value=[])
        return loader
    
    @pytest.fixture
    def mock_memory_retriever(self):
        """创建模拟记忆检索器"""
        retriever = MagicMock(spec=MemoryRetriever)
        retriever.retrieve_memories = AsyncMock(return_value={
            "user_memories": [],
            "ai_memories": []
        })
        return retriever
    
    @pytest.fixture
    def mock_user_profile_loader(self):
        """创建模拟用户画像加载器"""
        loader = MagicMock(spec=UserProfileLoader)
        loader.load_user_profile = AsyncMock(return_value=None)
        return loader
    
    @pytest.fixture
    def mock_context_assembler(self):
        """创建模拟上下文组装器"""
        assembler = MagicMock(spec=ContextAssembler)
        assembler.assemble_context = AsyncMock(return_value=MagicMock(
            messages=[],
            memories=[],
            user_profile=None
        ))
        return assembler
    
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
    def context_service(
        self,
        mock_db,
        mock_memory_manager
    ):
        """创建ContextService实例"""
        return ContextService(
            db=mock_db,
            memory_manager=mock_memory_manager
        )
    
    @pytest.mark.asyncio
    async def test_build_context_success(
        self,
        context_service
    ):
        """测试：成功构建上下文"""
        # Arrange
        user_id = "test-user-id"
        session_id = "test-session-id"
        current_message = "Hello"
        personality = MagicMock()
        personality.id = "test-personality"
        personality.ai = MagicMock()
        personality.ai.system_prompt = "You are a helpful assistant"  # 确保是字符串
        max_tokens = 4096
        
        # Mock子服务方法
        context_service.message_retriever.get_recent_messages = AsyncMock(return_value=[])
        context_service.summary_loader.load_history_summaries = AsyncMock(return_value=[])
        context_service.memory_retriever.retrieve_memories = AsyncMock(return_value={
            "user_memories": [],
            "ai_memories": []
        })
        context_service.user_profile_loader.load_user_profile = AsyncMock(return_value=None)
        # Mock ContextBundle对象
        from app.schemas.context import ContextBundle
        mock_bundle = ContextBundle(
            system_prompts=[],
            recent_messages=[],
            summarized_history=[],
            retrieved_memories=[],
            user_profile=None,
            total_tokens=0,
            metadata={}
        )
        context_service.context_assembler.assemble_context = MagicMock(return_value=mock_bundle)
        
        # Act
        result = await context_service.build_context(
            user_id=user_id,
            session_id=session_id,
            current_message=current_message,
            personality_config=personality,
            max_tokens=max_tokens
        )
        
        # Assert
        assert result is not None
        context_service.message_retriever.get_recent_messages.assert_called_once()
        context_service.summary_loader.load_history_summaries.assert_called_once()
        context_service.memory_retriever.retrieve_memories.assert_called_once()
        context_service.user_profile_loader.load_user_profile.assert_called_once()
        context_service.context_assembler.assemble_context.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_build_context_with_memories(
        self,
        context_service
    ):
        """测试：构建包含记忆的上下文"""
        # Arrange
        user_id = "test-user-id"
        session_id = "test-session-id"
        current_message = "What did we talk about?"
        personality = MagicMock()
        max_tokens = 4096
        
        # Mock记忆数据
        context_service.memory_retriever.retrieve_memories = AsyncMock(return_value={
            "user_memories": [
                MagicMock(content="Previous conversation", importance=0.8)
            ],
            "ai_memories": []
        })
        context_service.message_retriever.get_recent_messages = AsyncMock(return_value=[])
        context_service.summary_loader.load_history_summaries = AsyncMock(return_value=[])
        context_service.user_profile_loader.load_user_profile = AsyncMock(return_value=None)
        # Mock ContextBundle对象
        from app.schemas.context import ContextBundle
        mock_bundle = ContextBundle(
            system_prompts=[],
            recent_messages=[],
            summarized_history=[],
            retrieved_memories=[],
            user_profile=None,
            total_tokens=0,
            metadata={}
        )
        context_service.context_assembler.assemble_context = MagicMock(return_value=mock_bundle)
        
        # Act
        result = await context_service.build_context(
            user_id=user_id,
            session_id=session_id,
            current_message=current_message,
            personality_config=personality,
            max_tokens=max_tokens
        )
        
        # Assert
        assert result is not None
        context_service.memory_retriever.retrieve_memories.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_build_context_with_user_profile(
        self,
        context_service
    ):
        """测试：构建包含用户画像的上下文"""
        # Arrange
        user_id = "test-user-id"
        session_id = "test-session-id"
        current_message = "Hello"
        personality = MagicMock()
        personality.id = "test-personality"
        personality.ai = MagicMock()
        personality.ai.system_prompt = "You are a helpful assistant"  # 确保是字符串
        max_tokens = 4096
        
        # Mock用户画像（必须是字典）
        mock_profile = {
            "username": "testuser",
            "interests": ["technology", "AI"],
            "preferences": {}
        }
        context_service.user_profile_loader.load_user_profile = AsyncMock(return_value=mock_profile)
        context_service.message_retriever.get_recent_messages = AsyncMock(return_value=[])
        context_service.summary_loader.load_history_summaries = AsyncMock(return_value=[])
        context_service.memory_retriever.retrieve_memories = AsyncMock(return_value={
            "user_memories": [],
            "ai_memories": []
        })
        # Mock ContextBundle对象
        from app.schemas.context import ContextBundle
        mock_bundle = ContextBundle(
            system_prompts=[],
            recent_messages=[],
            summarized_history=[],
            retrieved_memories=[],
            user_profile=mock_profile,
            total_tokens=0,
            metadata={}
        )
        context_service.context_assembler.assemble_context = MagicMock(return_value=mock_bundle)
        
        # Act
        result = await context_service.build_context(
            user_id=user_id,
            session_id=session_id,
            current_message=current_message,
            personality_config=personality,
            max_tokens=max_tokens
        )
        
        # Assert
        assert result is not None
        context_service.user_profile_loader.load_user_profile.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_build_context_error_handling(
        self,
        context_service
    ):
        """测试：错误处理"""
        # Arrange
        user_id = "test-user-id"
        session_id = "test-session-id"
        current_message = "Hello"
        personality = MagicMock()
        personality.id = "test-personality"
        personality.ai = MagicMock()
        personality.ai.system_prompt = "You are a helpful assistant"  # 确保是字符串
        max_tokens = 4096
        
        # Mock错误 - 使用return_exceptions=True，所以不会抛出异常
        context_service.message_retriever.get_recent_messages = AsyncMock(side_effect=Exception("Database error"))
        context_service.summary_loader.load_history_summaries = AsyncMock(return_value=[])
        context_service.memory_retriever.retrieve_memories = AsyncMock(return_value={"user_memories": [], "ai_memories": []})
        context_service.user_profile_loader.load_user_profile = AsyncMock(return_value=None)
        
        # Mock ContextBundle对象（降级上下文）
        from app.schemas.context import ContextBundle
        mock_bundle = ContextBundle(
            system_prompts=[],
            recent_messages=[],
            summarized_history=[],
            retrieved_memories=[],
            user_profile=None,
            total_tokens=0,
            metadata={}
        )
        context_service.context_assembler.assemble_context = MagicMock(return_value=mock_bundle)
        
        # Act - 应该返回降级上下文，不抛出异常
        result = await context_service.build_context(
            user_id=user_id,
            session_id=session_id,
            current_message=current_message,
            personality_config=personality,
            max_tokens=max_tokens
        )
        
        # Assert - 应该返回降级上下文
        assert result is not None
