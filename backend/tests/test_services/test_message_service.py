"""
MessageService单元测试

测试消息服务的所有功能，包括：
- 保存对话轮次
- 保存用户消息
- 保存助手消息
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid

from app.services.message_service import MessageService
from app.services.chat.message_saver import MessageSaver


class TestMessageService:
    """MessageService单元测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return AsyncMock()
    
    @pytest.fixture
    def message_service(self, mock_db, mocker):
        """创建MessageService实例"""
        # Mock MessageSaver的创建
        mock_message_saver = MagicMock(spec=MessageSaver)
        mock_message_saver.save_conversation_turn = AsyncMock(return_value=True)
        mocker.patch('app.services.message_service.MessageSaver', return_value=mock_message_saver)
        
        service = MessageService(db=mock_db)
        service.message_saver = mock_message_saver  # 替换为mock对象
        return service
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_success(
        self,
        message_service
    ):
        """测试：成功保存对话轮次"""
        # Arrange
        session_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        user_message = "Hello"
        assistant_message = "Hi there!"
        assistant_model = "gpt-3.5-turbo"
        
        # Act
        await message_service.save_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            assistant_model=assistant_model
        )
        
        # Assert
        message_service.message_saver.save_conversation_turn.assert_called_once_with(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            assistant_model=assistant_model,
            memory_manager=None,
            personality=None
        )
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_with_memory(
        self,
        message_service
    ):
        """测试：保存对话轮次并保存记忆"""
        # Arrange
        session_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        user_message = "Hello"
        assistant_message = "Hi there!"
        assistant_model = "gpt-3.5-turbo"
        memory_manager = MagicMock()
        personality = MagicMock()
        personality.memory.enabled = True
        
        # Act
        await message_service.save_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            assistant_model=assistant_model,
            memory_manager=memory_manager,
            personality=personality
        )
        
        # Assert
        message_service.message_saver.save_conversation_turn.assert_called_once_with(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            assistant_model=assistant_model,
            memory_manager=memory_manager,
            personality=personality
        )
