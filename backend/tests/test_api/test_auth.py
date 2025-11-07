"""
认证API测试

测试认证API的所有功能，包括：
- 刷新令牌
- 无效令牌处理
- 过期令牌处理
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import Depends
from datetime import timedelta

from app.main import app
from app.utils.security import create_refresh_token, create_access_token


class TestAuthAPI:
    """测试认证API"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def valid_refresh_token(self):
        """有效的刷新令牌"""
        data = {"sub": "test-user-id", "username": "testuser"}
        return create_refresh_token(data)
    
    @pytest.fixture
    def expired_refresh_token(self):
        """过期的刷新令牌"""
        from datetime import datetime
        from jose import jwt
        from app.config.config import settings
        
        payload = {
            "sub": "test-user-id",
            "username": "testuser",
            "exp": datetime.utcnow() - timedelta(seconds=1),
            "type": "refresh"
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    
    def test_refresh_token_success(self, client, valid_refresh_token, mocker, sync_db_session):
        """测试：刷新令牌成功"""
        import uuid
        from app.utils.security import create_refresh_token
        from app.models.user import User
        from app.utils.security import hash_password
        from app.api.deps import get_sync_session
        
        # 创建测试用户（使用唯一用户名）
        unique_id = str(uuid.uuid4())[:8]
        test_user = User(
            id=uuid.uuid4(),
            username=f"testuser_refresh_{unique_id}",
            email=f"test_refresh_{unique_id}@example.com",
            password_hash=hash_password("TestPassword123!"),
            role="user",
            status="active"
        )
        sync_db_session.add(test_user)
        sync_db_session.commit()
        
        # 验证用户已创建
        from app.models.user import User as UserModel
        verify_user = sync_db_session.query(UserModel).filter(UserModel.id == test_user.id).first()
        assert verify_user is not None, "User should be created in database"
        assert verify_user.status == "active", f"User status should be active, got {verify_user.status}"
        
        # 创建有效的刷新令牌
        from app.core.user.auth import AuthService
        auth_service = AuthService()
        refresh_token = auth_service.create_refresh_token(str(test_user.id), test_user.username)
        
        # 验证token payload
        from app.utils.security import decode_token
        token_payload = decode_token(refresh_token)
        print(f"Token payload: {token_payload}")
        print(f"Token user_id: {token_payload.get('sub')}")
        print(f"Token username: {token_payload.get('username')}")
        print(f"Token type: {token_payload.get('type')}")
        
        try:
            # 使用FastAPI的override机制来覆盖依赖
            from app.api.deps import get_sync_session
            
            def override_get_sync_session():
                yield sync_db_session
            
            # 覆盖依赖
            app.dependency_overrides[get_sync_session] = override_get_sync_session
            
            try:
                # 再次验证用户存在（在override之后）
                verify_user_after = sync_db_session.query(UserModel).filter(UserModel.id == test_user.id).first()
                print(f"User exists after override: {verify_user_after is not None}")
                if verify_user_after:
                    print(f"User status: {verify_user_after.status}")
                
                response = client.post(
                    "/v1/auth/refresh",
                    json={"refresh_token": refresh_token}
                )
            finally:
                # 清理override
                app.dependency_overrides.clear()
            
            # 如果失败，打印错误信息
            if response.status_code != 200:
                print(f"Response status: {response.status_code}")
                print(f"Response body: {response.json()}")
                print(f"Test user ID: {test_user.id}")
                print(f"Test user status: {test_user.status}")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
            data = response.json()
            assert "access_token" in data
            # 注意：refresh_token API可能不返回refresh_token，只返回access_token
            # 根据实际API实现调整断言
        finally:
            # 清理测试用户
            try:
                sync_db_session.delete(test_user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    def test_refresh_token_invalid(self, client):
        """测试：无效刷新令牌"""
        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        
        assert response.status_code == 401
    
    def test_refresh_token_expired(self, client, expired_refresh_token):
        """测试：过期刷新令牌"""
        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": expired_refresh_token}
        )
        
        assert response.status_code == 401
    
    def test_refresh_token_missing(self, client):
        """测试：缺少刷新令牌"""
        response = client.post(
            "/v1/auth/refresh",
            json={}
        )
        
        assert response.status_code == 422  # 验证错误

