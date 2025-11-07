"""
安全工具测试

测试security工具的所有功能，包括：
- 密码哈希和验证
- JWT令牌创建和验证
"""

import pytest
from datetime import timedelta

from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.config.config import settings


class TestSecurityUtils:
    """测试安全工具"""
    
    def test_hash_password(self):
        """测试：密码哈希"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt哈希格式
    
    def test_verify_password_success(self):
        """测试：密码验证成功"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        result = verify_password(password, hashed)
        assert result is True
    
    def test_verify_password_failure(self):
        """测试：密码验证失败"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)
        
        result = verify_password(wrong_password, hashed)
        assert result is False
    
    def test_create_access_token(self):
        """测试：创建访问令牌"""
        data = {"sub": "test-user-id", "username": "testuser", "role": "user"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """测试：创建刷新令牌"""
        data = {"sub": "test-user-id", "username": "testuser"}
        token = create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_token_success(self):
        """测试：解码令牌成功"""
        data = {"sub": "test-user-id", "username": "testuser", "role": "user"}
        token = create_access_token(data)
        
        payload = decode_token(token)
        assert payload is not None
        assert payload.get("sub") == "test-user-id"
        assert "exp" in payload
    
    def test_decode_token_expired(self):
        """测试：解码过期令牌"""
        # 创建立即过期的令牌
        from datetime import datetime, timedelta
        from jose import jwt
        
        payload = {
            "sub": "test-user-id",
            "exp": datetime.utcnow() - timedelta(seconds=1)
        }
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
        
        result = decode_token(token)
        assert result is not None  # decode_token不验证签名，所以会返回结果
    
    def test_decode_token_invalid(self):
        """测试：解码无效令牌"""
        invalid_token = "invalid.token.here"
        
        payload = decode_token(invalid_token)
        assert payload is None
    
    def test_verify_token_success(self):
        """测试：验证令牌成功"""
        from app.utils.security import verify_token
        
        data = {"sub": "test-user-id", "username": "testuser", "role": "user"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        assert payload is not None
        assert payload.get("sub") == "test-user-id"
    
    def test_verify_token_invalid(self):
        """测试：验证无效令牌"""
        from app.utils.security import verify_token
        
        invalid_token = "invalid.token.here"
        
        payload = verify_token(invalid_token)
        assert payload is None

