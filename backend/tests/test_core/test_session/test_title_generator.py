"""
会话标题生成器测试

测试会话标题自动生成功能
"""

# 标准库
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime

# 本地库
from app.core.session.title_generator import SessionTitleGenerator
from app.models.session import Session as SessionModel
from app.models.message import Message as MessageModel


class TestSessionTitleGenerator:
    """测试会话标题生成器"""
    
    @pytest.fixture
    def title_generator(self, sync_db_session):
        """标题生成器实例"""
        return SessionTitleGenerator(sync_db_session)
    
    @pytest.fixture
    def test_session(self, sync_db_session):
        """测试会话"""
        from app.models.user import User as UserModel
        
        # 先创建用户（外键约束）
        test_user = UserModel(
            id=uuid.uuid4(),
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email=f"test_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="hashed_password",
            role="user",
            status="active"
        )
        sync_db_session.add(test_user)
        sync_db_session.commit()
        
        # 创建会话
        session = SessionModel(
            id=uuid.uuid4(),
            user_id=test_user.id,
            personality_id="default",
            title="新会话",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        sync_db_session.add(session)
        sync_db_session.commit()
        sync_db_session.refresh(session)
        return session
    
    def test_initialization(self, title_generator):
        """测试：初始化"""
        assert title_generator.db is not None
        assert title_generator.config_loader is not None
    
    def test_get_config(self, title_generator):
        """测试：获取配置"""
        config = title_generator._get_config()
        assert isinstance(config, dict)
        # 第二次调用应该使用缓存
        config2 = title_generator._get_config()
        assert config is config2
    
    def test_should_auto_generate_title_enabled(self, title_generator):
        """测试：自动生成标题已启用"""
        # Mock配置：启用自动生成，阈值为6
        with patch.object(
            title_generator.config_loader,
            'load_session_config',
            return_value={
                "auto_title": {
                    "enabled": True,
                    "message_threshold": 6
                }
            }
        ):
            assert title_generator._should_auto_generate_title(7) is True
            assert title_generator._should_auto_generate_title(6) is False
            assert title_generator._should_auto_generate_title(5) is False
    
    def test_should_auto_generate_title_disabled(self, title_generator):
        """测试：自动生成标题已禁用"""
        with patch.object(
            title_generator.config_loader,
            'load_session_config',
            return_value={
                "auto_title": {
                    "enabled": False,
                    "message_threshold": 6
                }
            }
        ):
            assert title_generator._should_auto_generate_title(10) is False
    
    @pytest.mark.asyncio
    async def test_generate_title_session_not_found(self, title_generator):
        """测试：会话不存在"""
        fake_id = str(uuid.uuid4())
        result = await title_generator.generate_title(fake_id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_title_no_messages(self, title_generator, test_session):
        """测试：没有消息"""
        result = await title_generator.generate_title(str(test_session.id))
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_title_below_threshold(self, title_generator, test_session, db_session):
        """测试：消息数量低于阈值"""
        # 添加少量消息
        for i in range(3):
            message = MessageModel(
                id=uuid.uuid4(),
                session_id=test_session.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                created_at=datetime.utcnow()
            )
            db_session.add(message)
        db_session.commit()
        
        # Mock配置：阈值为6
        with patch.object(
            title_generator.config_loader,
            'load_session_config',
            return_value={
                "auto_title": {
                    "enabled": True,
                    "message_threshold": 6,
                    "generation": {
                        "max_length": 50,
                        "model": "gpt-3.5-turbo"
                    }
                }
            }
        ):
            result = await title_generator.generate_title(str(test_session.id))
            assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_title_already_has_title(self, title_generator, test_session, db_session):
        """测试：会话已有标题"""
        # 设置已有标题
        test_session.title = "已有标题"
        db_session.commit()
        
        # 添加足够消息
        for i in range(10):
            message = MessageModel(
                id=uuid.uuid4(),
                session_id=test_session.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                created_at=datetime.utcnow()
            )
            db_session.add(message)
        db_session.commit()
        
        result = await title_generator.generate_title(str(test_session.id))
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_title_success(self, title_generator, test_session, db_session):
        """测试：成功生成标题"""
        # 添加足够消息
        for i in range(10):
            message = MessageModel(
                id=uuid.uuid4(),
                session_id=test_session.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                created_at=datetime.utcnow()
            )
            db_session.add(message)
        db_session.commit()
        
        # Mock AI引擎响应
        mock_response = MagicMock()
        mock_response.message = MagicMock()
        mock_response.message.content = "测试标题"
        
        with patch.object(
            title_generator.config_loader,
            'load_session_config',
            return_value={
                "auto_title": {
                    "enabled": True,
                    "message_threshold": 6,
                    "generation": {
                        "max_length": 50,
                        "model": "gpt-3.5-turbo"
                    }
                }
            }
        ), patch(
            'app.core.session.title_generator.AIEngineFactory.create_engine'
        ) as mock_factory:
            mock_engine = AsyncMock()
            mock_engine.chat = AsyncMock(return_value=mock_response)
            mock_factory.return_value = mock_engine
            
            result = await title_generator.generate_title(str(test_session.id))
            assert result is not None
            assert result == "测试标题"
    
    @pytest.mark.asyncio
    async def test_update_session_title_if_needed_no_update(self, title_generator, test_session):
        """测试：不需要更新标题"""
        # 消息数量不足
        result = await title_generator.update_session_title_if_needed(str(test_session.id))
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_session_title_if_needed_success(self, title_generator, test_session, db_session):
        """测试：成功更新标题"""
        # 添加足够消息
        for i in range(10):
            message = MessageModel(
                id=uuid.uuid4(),
                session_id=test_session.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                created_at=datetime.utcnow()
            )
            db_session.add(message)
        db_session.commit()
        
        # Mock AI引擎响应
        mock_response = MagicMock()
        mock_response.message = MagicMock()
        mock_response.message.content = "新标题"
        
        with patch.object(
            title_generator.config_loader,
            'load_session_config',
            return_value={
                "auto_title": {
                    "enabled": True,
                    "message_threshold": 6,
                    "generation": {
                        "max_length": 50,
                        "model": "gpt-3.5-turbo"
                    }
                }
            }
        ), patch(
            'app.core.session.title_generator.AIEngineFactory.create_engine'
        ) as mock_factory:
            mock_engine = AsyncMock()
            mock_engine.chat = AsyncMock(return_value=mock_response)
            mock_factory.return_value = mock_engine
            
            result = await title_generator.update_session_title_if_needed(str(test_session.id))
            assert result is True
            
            # 验证标题已更新
            db_session.refresh(test_session)
            assert test_session.title == "新标题"

