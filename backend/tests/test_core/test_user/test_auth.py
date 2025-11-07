"""
用户认证服务测试

测试AuthService的所有功能，包括：
- 密码哈希和验证
- JWT令牌创建和验证
- 用户认证
- 从令牌获取用户
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.user.auth import AuthService
from app.models.user import User
from app.config.config import settings


class TestAuthService:
    """测试认证服务"""
    
    @pytest.fixture
    def auth_service(self):
        """认证服务实例"""
        return AuthService()
    
    @pytest.fixture
    def test_user_data(self):
        """测试用户数据"""
        return {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123!",
            "display_name": "Test User"
        }
    
    @pytest.fixture
    def db_user(self, sync_db_session, test_user_data):
        """创建测试用户"""
        from app.utils.security import hash_password
        
        user = User(
            id="test-user-id-123",
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=hash_password(test_user_data["password"]),
            display_name=test_user_data["display_name"],
            role="user",
            status="active"
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        sync_db_session.refresh(user)
        return user
    
    # ========== 密码哈希测试 ==========
    
    def test_hash_password(self, auth_service):
        """测试：密码哈希"""
        password = "TestPassword123!"
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt哈希格式
    
    def test_verify_password_success(self, auth_service):
        """测试：密码验证成功"""
        password = "TestPassword123!"
        hashed = auth_service.hash_password(password)
        
        result = auth_service.verify_password(password, hashed)
        assert result is True
    
    def test_verify_password_failure(self, auth_service):
        """测试：密码验证失败"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = auth_service.hash_password(password)
        
        result = auth_service.verify_password(wrong_password, hashed)
        assert result is False
    
    # ========== JWT令牌测试 ==========
    
    def test_create_access_token(self, auth_service):
        """测试：创建访问令牌"""
        user_id = "test-user-id"
        username = "testuser"
        role = "user"
        token = auth_service.create_access_token(user_id, username, role)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self, auth_service):
        """测试：创建刷新令牌"""
        user_id = "test-user-id"
        username = "testuser"
        token = auth_service.create_refresh_token(user_id, username)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_success(self, auth_service):
        """测试：验证令牌成功"""
        user_id = "test-user-id"
        username = "testuser"
        role = "user"
        token = auth_service.create_access_token(user_id, username, role)
        
        payload = auth_service.verify_token(token)
        assert payload is not None
        assert payload.get("sub") == user_id
        assert "exp" in payload
    
    def test_verify_token_expired(self, auth_service):
        """测试：验证过期令牌"""
        user_id = "test-user-id"
        username = "testuser"
        role = "user"
        # 创建立即过期的令牌
        from datetime import timedelta
        token = auth_service.create_access_token(
            user_id, username, role, 
            expires_delta=timedelta(seconds=-1)
        )
        
        # 等待令牌过期
        import time
        time.sleep(2)
        
        payload = auth_service.verify_token(token)
        assert payload is None
    
    def test_verify_token_invalid(self, auth_service):
        """测试：验证无效令牌"""
        invalid_token = "invalid.token.here"
        
        payload = auth_service.verify_token(invalid_token)
        assert payload is None
    
    # ========== 用户认证测试 ==========
    
    def test_authenticate_user_success(self, auth_service, sync_db_session, db_user, test_user_data):
        """测试：用户认证成功"""
        result = auth_service.authenticate_user(
            sync_db_session,
            test_user_data["username"],
            test_user_data["password"]
        )
        
        assert result is not None
        assert isinstance(result, User)
        assert result.id == db_user.id
        assert result.username == db_user.username
    
    def test_authenticate_user_not_found(self, auth_service, sync_db_session):
        """测试：用户不存在"""
        result = auth_service.authenticate_user(
            sync_db_session,
            "nonexistent_user",
            "password123"
        )
        
        assert result is None
    
    def test_authenticate_user_wrong_password(self, auth_service, sync_db_session, db_user, test_user_data):
        """测试：密码错误"""
        result = auth_service.authenticate_user(
            sync_db_session,
            test_user_data["username"],
            "WrongPassword123!"
        )
        
        assert result is None
    
    def test_authenticate_user_inactive(self, auth_service, sync_db_session, db_user, test_user_data):
        """测试：用户未激活"""
        db_user.status = "inactive"
        sync_db_session.commit()
        
        result = auth_service.authenticate_user(
            sync_db_session,
            test_user_data["username"],
            test_user_data["password"]
        )
        
        assert result is None
    
    # ========== 从令牌获取用户测试 ==========
    
    def test_get_current_user_from_token_success(self, auth_service, sync_db_session, db_user):
        """测试：从令牌获取用户成功"""
        token = auth_service.create_access_token(db_user.id, db_user.username, db_user.role)
        
        user = auth_service.get_current_user_from_token(sync_db_session, token)
        
        assert user is not None
        assert user.id == db_user.id
        assert user.username == db_user.username
    
    def test_get_current_user_from_token_invalid(self, auth_service, sync_db_session):
        """测试：无效令牌"""
        invalid_token = "invalid.token.here"
        
        user = auth_service.get_current_user_from_token(sync_db_session, invalid_token)
        
        assert user is None
    
    def test_get_current_user_from_token_user_not_found(self, auth_service, sync_db_session):
        """测试：用户不存在"""
        token = auth_service.create_access_token("nonexistent-user-id", "testuser", "user")
        
        user = auth_service.get_current_user_from_token(sync_db_session, token)
        
        assert user is None

