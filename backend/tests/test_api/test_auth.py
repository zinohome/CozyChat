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
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client, sync_db_session, db_session):
        """测试：刷新令牌成功"""
        import uuid
        from app.utils.security import hash_password
        from app.models.user import User
        from app.api.deps import get_db
        from app.core.user.auth import AuthService
        
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
        
        # 同时添加到异步会话，确保异步查询能找到用户
        async with db_session.begin():
            # 检查用户是否已存在（避免重复）
            from sqlalchemy import select
            stmt = select(User).where(User.id == test_user.id)
            result = await db_session.execute(stmt)
            existing_user = result.scalar_one_or_none()
            if not existing_user:
                db_session.add(test_user)
                await db_session.commit()
        
        # 创建有效的刷新令牌
        auth_service = AuthService()
        refresh_token = auth_service.create_refresh_token(str(test_user.id), test_user.username)
        
        try:
            # 覆盖get_db依赖，返回包含用户的异步会话（异步生成器）
            async def get_async_db():
                yield db_session
            
            app.dependency_overrides[get_db] = get_async_db
            
            response = client.post(
                "/v1/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json() if response.status_code != 200 else ''}"
            data = response.json()
            assert "access_token" in data
        finally:
            # 清理依赖覆盖
            app.dependency_overrides.pop(get_db, None)
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

