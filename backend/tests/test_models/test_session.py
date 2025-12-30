"""
会话模型测试

测试Session模型的功能
"""

# 标准库
import pytest
import uuid
from datetime import datetime

# 本地库
from app.models.session import Session
from app.models.user import User


class TestSessionModel:
    """测试会话模型"""
    
    @pytest.fixture
    def test_user(self, sync_db_session):
        """创建测试用户"""
        from app.utils.security import hash_password
        
        user = User(
            id=uuid.uuid4(),
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email=f"test_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=hash_password("TestPassword123!"),
            role="user",
            status="active"
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        sync_db_session.refresh(user)
        
        yield user
        
        # 清理
        try:
            sync_db_session.delete(user)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    def test_session_creation(self, sync_db_session, test_user):
        """测试：创建会话"""
        session = Session(
            user_id=test_user.id,
            personality_id="test_personality",
            title="测试会话"
        )
        
        sync_db_session.add(session)
        sync_db_session.commit()
        sync_db_session.refresh(session)
        
        assert session.id is not None
        assert session.user_id == test_user.id
        assert session.personality_id == "test_personality"
        assert session.title == "测试会话"
        assert session.message_count == 0
        assert session.total_tokens_used == 0
        assert session.created_at is not None
        assert session.updated_at is not None
        
        # 清理
        try:
            sync_db_session.delete(session)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    def test_session_to_dict(self, sync_db_session, test_user):
        """测试：会话转字典"""
        session = Session(
            user_id=test_user.id,
            personality_id="test_personality",
            title="测试会话"
        )
        
        sync_db_session.add(session)
        sync_db_session.commit()
        sync_db_session.refresh(session)
        
        session_dict = session.to_dict()
        
        assert isinstance(session_dict, dict)
        assert "id" in session_dict
        assert "user_id" in session_dict
        assert "personality_id" in session_dict
        assert "title" in session_dict
        assert "message_count" in session_dict
        assert "total_tokens_used" in session_dict
        assert "created_at" in session_dict
        assert "updated_at" in session_dict
        
        # 清理
        try:
            sync_db_session.delete(session)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    def test_session_relationships(self, sync_db_session, test_user):
        """测试：会话关系"""
        session = Session(
            user_id=test_user.id,
            personality_id="test_personality",
            title="测试会话"
        )
        
        sync_db_session.add(session)
        sync_db_session.commit()
        sync_db_session.refresh(session)
        
        # 测试messages关系（应该为空列表）
        assert hasattr(session, "messages")
        assert isinstance(session.messages, list)
        
        # 清理
        try:
            sync_db_session.delete(session)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    def test_session_default_values(self, sync_db_session, test_user):
        """测试：会话默认值"""
        session = Session(
            user_id=test_user.id,
            personality_id="test_personality"
            # 不设置title，应该使用默认值
        )
        
        sync_db_session.add(session)
        sync_db_session.commit()
        sync_db_session.refresh(session)
        
        assert session.title == "新会话"
        assert session.message_count == 0
        assert session.total_tokens_used == 0
        assert session.session_metadata == {}
        
        # 清理
        try:
            sync_db_session.delete(session)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    def test_session_metadata(self, sync_db_session, test_user):
        """测试：会话元数据"""
        metadata = {"key1": "value1", "key2": 123}
        
        session = Session(
            user_id=test_user.id,
            personality_id="test_personality",
            title="测试会话",
            session_metadata=metadata
        )
        
        sync_db_session.add(session)
        sync_db_session.commit()
        sync_db_session.refresh(session)
        
        assert session.session_metadata == metadata
        
        # 清理
        try:
            sync_db_session.delete(session)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()

