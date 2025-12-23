"""
MessageService单元测试

测试消息服务的所有功能，包括：
- 保存对话轮次
- 保存用户消息
- 保存助手消息
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import uuid

from app.services.message_service import MessageService
from app.services.chat.message_saver import MessageSaver


class TestMessageService:
    """MessageService单元测试类"""
    
    @pytest_asyncio.fixture
    async def message_service(self, db_session):
        """创建MessageService实例"""
        # 使用真实的db_session，MessageSaver会使用它
        service = MessageService(db=db_session)
        return service
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_success(
        self,
        message_service,
        db_session
    ):
        """测试：成功保存对话轮次"""
        # Arrange
        from app.models.user import User
        from app.models.session import Session
        from datetime import datetime
        
        # 创建测试用户和会话
        test_user_id = uuid.uuid4()
        test_session_id = uuid.uuid4()
        
        user = User(
            id=test_user_id,
            username=f"testuser_{test_user_id.hex[:8]}",
            email=f"test_{test_user_id.hex[:8]}@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        
        session = Session(
            id=test_session_id,
            user_id=test_user_id,
            personality_id="default",
            title="Test Session",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(session)
        await db_session.commit()
        
        user_message = "Hello"
        assistant_message = "Hi there!"
        assistant_model = "gpt-3.5-turbo"
        
        # Act
        await message_service.save_conversation_turn(
            session_id=str(test_session_id),
            user_id=str(test_user_id),
            user_message=user_message,
            assistant_message=assistant_message,
            assistant_model=assistant_model
        )
        await db_session.commit()
        
        # Assert - 验证消息已保存到数据库
        from app.models.message import Message
        from sqlalchemy import select
        
        stmt = select(Message).where(Message.session_id == test_session_id)
        result = await db_session.execute(stmt)
        messages = result.scalars().all()
        
        assert len(messages) == 2  # 用户消息和助手消息
        user_msg = next((m for m in messages if m.role == "user"), None)
        assistant_msg = next((m for m in messages if m.role == "assistant"), None)
        
        assert user_msg is not None
        assert user_msg.content == user_message
        assert assistant_msg is not None
        assert assistant_msg.content == assistant_message
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_with_memory(
        self,
        message_service,
        db_session
    ):
        """测试：保存对话轮次并保存记忆"""
        # Arrange
        from app.models.user import User
        from app.models.session import Session
        from datetime import datetime
        
        # 创建测试用户和会话
        test_user_id = uuid.uuid4()
        test_session_id = uuid.uuid4()
        
        user = User(
            id=test_user_id,
            username=f"testuser_{test_user_id.hex[:8]}",
            email=f"test_{test_user_id.hex[:8]}@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        
        session = Session(
            id=test_session_id,
            user_id=test_user_id,
            personality_id="default",
            title="Test Session",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(session)
        await db_session.commit()
        
        user_message = "Hello"
        assistant_message = "Hi there!"
        assistant_model = "gpt-3.5-turbo"
        memory_manager = MagicMock()
        personality = MagicMock()
        personality.memory.enabled = True
        
        # Act
        await message_service.save_conversation_turn(
            session_id=str(test_session_id),
            user_id=str(test_user_id),
            user_message=user_message,
            assistant_message=assistant_message,
            assistant_model=assistant_model,
            memory_manager=memory_manager,
            personality=personality
        )
        await db_session.commit()
        
        # Assert - 验证消息已保存到数据库
        from app.models.message import Message
        from sqlalchemy import select
        
        stmt = select(Message).where(Message.session_id == test_session_id)
        result = await db_session.execute(stmt)
        messages = result.scalars().all()
        
        assert len(messages) == 2  # 用户消息和助手消息
        user_msg = next((m for m in messages if m.role == "user"), None)
        assistant_msg = next((m for m in messages if m.role == "assistant"), None)
        
        assert user_msg is not None
        assert user_msg.content == user_message
        assert assistant_msg is not None
        assert assistant_msg.content == assistant_message
