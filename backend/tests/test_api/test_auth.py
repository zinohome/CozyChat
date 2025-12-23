"""
认证API测试

测试认证API的所有功能，包括：
- 刷新令牌
- 无效令牌处理
- 过期令牌处理
"""

import pytest
import uuid
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
        # 使用UUID格式的user_id，符合PostgreSQL UUID类型要求
        test_user_id = str(uuid.uuid4())
        data = {"sub": test_user_id, "username": "testuser"}
        return create_refresh_token(data)
    
    @pytest.fixture
    def expired_refresh_token(self):
        """过期的刷新令牌"""
        from datetime import datetime
        from jose import jwt
        from app.config.config import settings
        
        # 使用UUID格式的user_id，符合PostgreSQL UUID类型要求
        test_user_id = str(uuid.uuid4())
        payload = {
            "sub": test_user_id,
            "username": "testuser",
            "exp": datetime.utcnow() - timedelta(seconds=1),
            "type": "refresh"
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    
    def test_refresh_token_success(self, client, valid_refresh_token, sync_db_session):
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
            # refresh_token端点使用get_db（异步会话），需要覆盖为异步会话
            from app.api.deps import get_db
            from sqlalchemy.ext.asyncio import AsyncSession
            
            # 创建一个异步会话适配器
            # 注意：refresh_token端点使用AsyncSession，但TestClient是同步的
            # 我们需要创建一个异步会话的mock或者使用真实的异步会话
            # 由于TestClient的限制，我们使用db_session fixture（异步）
            # 但这里我们需要在测试中创建异步会话
            # 简化：直接使用sync_db_session，但需要转换为AsyncSession
            # 实际上，refresh_token端点会查询数据库，我们需要确保用户存在
            # 最简单的方法是确保用户已经在数据库中，然后不覆盖依赖
            
            # 验证用户存在
            verify_user_after = sync_db_session.query(UserModel).filter(UserModel.id == test_user.id).first()
            assert verify_user_after is not None, "User should exist"
            
            # 由于refresh_token使用AsyncSession，而TestClient是同步的
            # 我们需要确保用户存在于异步会话也能访问
            # 最简单的方法是不覆盖依赖，让端点使用真实的数据库
            # 但我们需要确保用户存在
            response = client.post(
                "/v1/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            
            # 如果失败，打印错误信息
            if response.status_code != 200:
                print(f"Response status: {response.status_code}")
                print(f"Response body: {response.json()}")
                print(f"Test user ID: {test_user.id}")
                print(f"Test user status: {test_user.status}")
                print(f"Token payload: {token_payload}")
            
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

