"""
MessageSaver服务单元测试

测试消息保存服务的各种场景
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chat.message_saver import MessageSaver
from app.models.message import Message as MessageModel
from app.models.session import Session as SessionModel


class TestMessageSaver:
    """MessageSaver单元测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话（异步）"""
        db = AsyncMock(spec=AsyncSession)
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.refresh = AsyncMock()
        # 配置execute返回结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        db.execute = AsyncMock(return_value=mock_result)
        return db
    
    @pytest.fixture
    def mock_session_model(self):
        """创建模拟会话模型"""
        session = Mock(spec=SessionModel)
        session.message_count = 0
        session.last_message_at = None
        return session
    
    @pytest.fixture
    def mock_memory_manager(self):
        """创建模拟记忆管理器"""
        manager = Mock()
        manager.add_conversation_turn = AsyncMock(return_value=None)
        return manager
    
    @pytest.fixture
    def mock_personality(self):
        """创建模拟人格配置"""
        personality = Mock()
        personality.memory.enabled = True
        return personality
    
    @pytest.fixture
    def message_saver(self, mock_db):
        """创建MessageSaver实例"""
        return MessageSaver(db=mock_db)
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_success(
        self,
        message_saver,
        mock_db,
        mock_session_model
    ):
        """测试：成功保存一轮对话"""
        # Arrange
        session_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        user_message = "你好"
        assistant_message = "你好！有什么可以帮助你的吗？"
        model = "gpt-3.5-turbo"
        
        # 配置execute返回会话模型
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session_model)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await message_saver.save_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            assistant_model=model,
            use_memory=False
        )
        
        # Assert
        assert result is True
        assert mock_db.add.call_count == 2  # 用户消息 + 助手消息
        mock_db.commit.assert_called_once()
        assert mock_session_model.message_count == 2
        assert mock_session_model.last_message_at is not None
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_with_memory(
        self,
        message_saver,
        mock_db,
        mock_session_model,
        mock_memory_manager,
        mock_personality
    ):
        """测试：保存对话并同时保存记忆"""
        # Arrange
        session_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        user_message = "介绍一下量子计算"
        assistant_message = "量子计算是基于量子力学原理的新型计算方式..."
        
        # 配置execute返回会话模型
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session_model)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await message_saver.save_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            memory_manager=mock_memory_manager,
            personality=mock_personality,
            use_memory=True
        )
        
        # Assert
        assert result is True
        mock_db.commit.assert_called_once()
        mock_memory_manager.add_conversation_turn.assert_awaited_once_with(
            user_id=user_id,
            session_id=session_id,
            user_message=user_message,
            assistant_message=assistant_message,
            async_save=True
        )
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_memory_disabled(
        self,
        message_saver,
        mock_db,
        mock_session_model,
        mock_memory_manager,
        mock_personality
    ):
        """测试：人格禁用记忆时不保存记忆"""
        # Arrange
        session_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        user_message = "测试消息"
        assistant_message = "测试回复"
        
        mock_personality.memory.enabled = False
        # 配置execute返回会话模型
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session_model)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await message_saver.save_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            memory_manager=mock_memory_manager,
            personality=mock_personality,
            use_memory=True
        )
        
        # Assert
        assert result is True
        mock_db.commit.assert_called_once()
        mock_memory_manager.add_conversation_turn.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_no_memory_manager(
        self,
        message_saver,
        mock_db,
        mock_session_model
    ):
        """测试：没有记忆管理器时不保存记忆"""
        # Arrange
        session_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        user_message = "测试"
        assistant_message = "回复"
        
        # 配置execute返回会话模型
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session_model)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await message_saver.save_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            memory_manager=None,
            use_memory=True
        )
        
        # Assert
        assert result is True
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_database_error(
        self,
        message_saver,
        mock_db
    ):
        """测试：数据库保存失败时正确处理"""
        # Arrange
        session_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        user_message = "测试"
        assistant_message = "回复"
        
        mock_db.add.side_effect = Exception("Database error")
        
        # Act
        result = await message_saver.save_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            use_memory=False
        )
        
        # Assert
        assert result is False
        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_memory_error(
        self,
        message_saver,
        mock_db,
        mock_session_model,
        mock_memory_manager,
        mock_personality
    ):
        """测试：记忆保存失败不影响消息保存"""
        # Arrange
        session_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        user_message = "测试"
        assistant_message = "回复"
        
        # 配置execute返回会话模型
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session_model)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_memory_manager.add_conversation_turn.side_effect = Exception("Memory error")
        
        # Act
        result = await message_saver.save_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            memory_manager=mock_memory_manager,
            personality=mock_personality,
            use_memory=True
        )
        
        # Assert
        assert result is True  # 消息保存仍然成功
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_invalid_uuid(
        self,
        message_saver,
        mock_db
    ):
        """测试：无效的UUID格式"""
        # Arrange
        session_id = "invalid-uuid"
        user_id = "invalid-uuid"
        user_message = "测试"
        assistant_message = "回复"
        
        # Act
        result = await message_saver.save_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            use_memory=False
        )
        
        # Assert
        assert result is False
        mock_db.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_updates_session_stats(
        self,
        message_saver,
        mock_db,
        mock_session_model
    ):
        """测试：正确更新会话统计信息"""
        # Arrange
        session_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        user_message = "测试消息"
        assistant_message = "测试回复"
        
        mock_session_model.message_count = 10
        # 配置execute返回会话模型
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session_model)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await message_saver.save_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            use_memory=False
        )
        
        # Assert
        assert result is True
        assert mock_session_model.message_count == 12  # 10 + 2
        assert isinstance(mock_session_model.last_message_at, datetime)
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_no_existing_session(
        self,
        message_saver,
        mock_db
    ):
        """测试：会话不存在时仍然保存消息"""
        # Arrange
        session_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        user_message = "测试"
        assistant_message = "回复"
        
        # 配置execute返回None（会话不存在）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await message_saver.save_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            use_memory=False
        )
        
        # Assert
        assert result is True
        assert mock_db.add.call_count == 2
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_empty_messages(
        self,
        message_saver,
        mock_db,
        mock_session_model
    ):
        """测试：空消息也能正确保存"""
        # Arrange
        session_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        user_message = ""
        assistant_message = ""
        
        # 配置execute返回会话模型
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session_model)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await message_saver.save_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            use_memory=False
        )
        
        # Assert
        assert result is True
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_with_model_name(
        self,
        message_saver,
        mock_db,
        mock_session_model
    ):
        """测试：正确保存模型名称"""
        # Arrange
        session_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        user_message = "测试"
        assistant_message = "回复"
        model = "gpt-4"
        
        # 配置execute返回会话模型
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session_model)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # 捕获add的调用参数
        added_messages = []
        def capture_add(obj):
            added_messages.append(obj)
        
        mock_db.add = Mock(side_effect=capture_add)
        
        # Act
        result = await message_saver.save_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            assistant_model=model,
            use_memory=False
        )
        
        # Assert
        assert result is True
        assert len(added_messages) == 2
        # 验证助手消息包含模型名称
        assistant_msg = [m for m in added_messages if m.role == "assistant"][0]
        assert assistant_msg.model == model

