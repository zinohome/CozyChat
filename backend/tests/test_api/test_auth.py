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
    
    def test_refresh_token_success(self, client, valid_refresh_token, mocker):
        """测试：刷新令牌成功"""
        # Mock用户查询
        with patch('app.api.v1.auth.get_sync_db') as mock_db:
            mock_session = MagicMock()
            mock_user = MagicMock()
            mock_user.id = "test-user-id"
            mock_user.username = "testuser"
            mock_user.status = "active"
            mock_session.query.return_value.filter.return_value.first.return_value = mock_user
            mock_db.return_value.__enter__.return_value = mock_session
            
            response = client.post(
                "/v1/auth/refresh",
                json={"refresh_token": valid_refresh_token}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
    
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

