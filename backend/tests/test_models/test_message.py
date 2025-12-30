"""
消息模型测试

测试Message模型的功能
"""

# 标准库
import pytest
import uuid
from datetime import datetime

# 本地库
from app.models.message import Message
from app.models.session import Session
from app.models.user import User


class TestMessageModel:
    """测试消息模型"""
    
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
    
    @pytest.fixture
    def test_session(self, sync_db_session, test_user):
        """创建测试会话"""
        session = Session(
            user_id=test_user.id,
            personality_id="test_personality",
            title="测试会话"
        )
        sync_db_session.add(session)
        sync_db_session.commit()
        sync_db_session.refresh(session)
        
        yield session
        
        # 清理
        try:
            sync_db_session.delete(session)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    def test_message_creation(self, sync_db_session, test_user, test_session):
        """测试：创建消息"""
        message = Message(
            session_id=test_session.id,
            user_id=test_user.id,
            role="user",
            content="测试消息内容"
        )
        
        sync_db_session.add(message)
        sync_db_session.commit()
        sync_db_session.refresh(message)
        
        assert message.id is not None
        assert message.session_id == test_session.id
        assert message.user_id == test_user.id
        assert message.role == "user"
        assert message.content == "测试消息内容"
        assert message.created_at is not None
        
        # 清理
        try:
            sync_db_session.delete(message)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    def test_message_to_dict(self, sync_db_session, test_user, test_session):
        """测试：消息转字典"""
        message = Message(
            session_id=test_session.id,
            user_id=test_user.id,
            role="user",
            content="测试消息内容"
        )
        
        sync_db_session.add(message)
        sync_db_session.commit()
        sync_db_session.refresh(message)
        
        message_dict = message.to_dict()
        
        assert isinstance(message_dict, dict)
        assert "id" in message_dict
        assert "session_id" in message_dict
        assert "user_id" in message_dict
        assert "role" in message_dict
        assert "content" in message_dict
        assert "created_at" in message_dict
        
        # 清理
        try:
            sync_db_session.delete(message)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    def test_message_relationships(self, sync_db_session, test_user, test_session):
        """测试：消息关系"""
        message = Message(
            session_id=test_session.id,
            user_id=test_user.id,
            role="user",
            content="测试消息内容"
        )
        
        sync_db_session.add(message)
        sync_db_session.commit()
        sync_db_session.refresh(message)
        
        # 测试session关系
        assert hasattr(message, "session")
        assert message.session is not None
        assert message.session.id == test_session.id
        
        # 清理
        try:
            sync_db_session.delete(message)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    def test_message_roles(self, sync_db_session, test_user, test_session):
        """测试：消息角色"""
        roles = ["user", "assistant", "system", "tool"]
        
        for role in roles:
            message = Message(
                session_id=test_session.id,
                user_id=test_user.id,
                role=role,
                content=f"测试{role}消息"
            )
            
            sync_db_session.add(message)
            sync_db_session.commit()
            sync_db_session.refresh(message)
            
            assert message.role == role
            
            # 清理
            try:
                sync_db_session.delete(message)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    def test_message_with_ai_info(self, sync_db_session, test_user, test_session):
        """测试：AI生成信息"""
        message = Message(
            session_id=test_session.id,
            user_id=test_user.id,
            role="assistant",
            content="AI回复内容",
            model="gpt-4",
            temperature=0.7,
            tokens_used={"prompt": 100, "completion": 50, "total": 150}
        )
        
        sync_db_session.add(message)
        sync_db_session.commit()
        sync_db_session.refresh(message)
        
        assert message.model == "gpt-4"
        assert message.temperature == 0.7
        assert message.tokens_used == {"prompt": 100, "completion": 50, "total": 150}
        
        # 清理
        try:
            sync_db_session.delete(message)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    def test_message_with_tool_calls(self, sync_db_session, test_user, test_session):
        """测试：工具调用"""
        tool_calls = [
            {"id": "call_1", "type": "function", "function": {"name": "calculator", "arguments": '{"expression": "2+2"}'}}
        ]
        
        message = Message(
            session_id=test_session.id,
            user_id=test_user.id,
            role="assistant",
            content="使用了工具",
            tool_calls=tool_calls
        )
        
        sync_db_session.add(message)
        sync_db_session.commit()
        sync_db_session.refresh(message)
        
        assert message.tool_calls == tool_calls
        
        # 清理
        try:
            sync_db_session.delete(message)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    def test_message_with_memories_used(self, sync_db_session, test_user, test_session):
        """测试：记忆使用"""
        memories_used = [
            {"id": "mem_123", "similarity": 0.85},
            {"id": "mem_456", "similarity": 0.72}
        ]
        
        message = Message(
            session_id=test_session.id,
            user_id=test_user.id,
            role="assistant",
            content="使用了记忆",
            memories_used=memories_used
        )
        
        sync_db_session.add(message)
        sync_db_session.commit()
        sync_db_session.refresh(message)
        
        assert message.memories_used == memories_used
        
        # 清理
        try:
            sync_db_session.delete(message)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    def test_message_default_metadata(self, sync_db_session, test_user, test_session):
        """测试：消息默认元数据"""
        message = Message(
            session_id=test_session.id,
            user_id=test_user.id,
            role="user",
            content="测试消息"
        )
        
        sync_db_session.add(message)
        sync_db_session.commit()
        sync_db_session.refresh(message)
        
        assert message.message_metadata == {}
        
        # 清理
        try:
            sync_db_session.delete(message)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()

