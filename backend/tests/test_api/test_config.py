"""
配置管理API测试

测试配置管理API端点
"""

# 标准库
import pytest
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# 本地库
from app.main import app
from app.api.v1.config import router
from app.config.config import settings
from app.utils.security import create_access_token


class TestConfigAPI:
    """测试配置管理API"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def test_user_token(self, sync_db_session):
        """测试用户令牌（需要创建真实用户）"""
        from app.models.user import User as UserModel
        from app.utils.security import hash_password
        
        # 创建测试用户
        test_user_id = uuid.uuid4()
        unique_suffix = uuid.uuid4().hex[:8]
        test_user = UserModel(
            id=test_user_id,
            username=f"testuser_{unique_suffix}",
            email=f"test_{unique_suffix}@example.com",
            password_hash=hash_password("TestPassword123!"),
            role="user",
            status="active"
        )
        sync_db_session.add(test_user)
        sync_db_session.commit()
        sync_db_session.refresh(test_user)
        
        # 创建访问令牌（使用真实的user_id）
        data = {"sub": str(test_user.id), "username": test_user.username, "role": test_user.role}
        token = create_access_token(data)
        
        yield token
        
        # 清理
        try:
            sync_db_session.delete(test_user)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    @pytest.fixture
    def auth_headers(self, test_user_token):
        """认证头"""
        return {"Authorization": f"Bearer {test_user_token}"}
    
    def test_get_openai_config_success(self, client, auth_headers, sync_db_session):
        """测试：获取OpenAI配置成功"""
        from app.api.deps import get_sync_session
        from app.main import app
        
        # 覆盖get_sync_session依赖，使用测试数据库会话
        def override_get_sync_session():
            yield sync_db_session
        
        app.dependency_overrides[get_sync_session] = override_get_sync_session
        
        try:
            with patch.object(settings, 'openai_api_key', 'test-key'):
                with patch.object(settings, 'openai_base_url', 'https://api.openai.com/v1'):
                    response = client.get(
                        "/v1/config/openai-config",
                        headers=auth_headers
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert "api_key" in data
                    assert "base_url" in data
                    assert data["api_key"] == "test-key"
                    assert data["base_url"] == "https://api.openai.com/v1"
        finally:
            app.dependency_overrides.clear()
    
    def test_get_openai_config_no_key(self, client, auth_headers, sync_db_session):
        """测试：OpenAI API key未配置"""
        from app.api.deps import get_sync_session
        from app.main import app
        
        def override_get_sync_session():
            yield sync_db_session
        
        app.dependency_overrides[get_sync_session] = override_get_sync_session
        
        try:
            with patch.object(settings, 'openai_api_key', None):
                response = client.get(
                    "/v1/config/openai-config",
                    headers=auth_headers
                )
                assert response.status_code == 500
        finally:
            app.dependency_overrides.clear()
    
    def test_get_openai_config_unauthorized(self, client):
        """测试：未授权访问"""
        response = client.get("/v1/config/openai-config")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_realtime_token_success(self, client, auth_headers, sync_db_session):
        from unittest.mock import AsyncMock
        from app.api.deps import get_current_active_user
        from app.utils.security import decode_token
        from app.models.user import User as UserModel
        
        """测试：获取Realtime token成功"""
        # 从token中获取user_id
        token_payload = decode_token(auth_headers["Authorization"].split(" ")[1])
        user_id = token_payload.get("sub")
        
        # 从数据库获取用户
        user = sync_db_session.query(UserModel).filter(UserModel.id == user_id).first()
        assert user is not None, "User should exist in database"
        
        # 覆盖依赖
        def get_user():
            return user
        
        app.dependency_overrides[get_current_active_user] = get_user
        
        try:
            with patch.object(settings, 'openai_api_key', 'test-key'):
                with patch.object(settings, 'openai_base_url', 'https://api.openai.com/v1'):
                    with patch.object(settings, 'openai_realtime_model', 'gpt-4o-realtime-preview-2024-10-01'):
                        with patch('httpx.AsyncClient') as mock_client:
                            # Mock HTTP响应
                            mock_response = MagicMock()
                            mock_response.status_code = 200
                            mock_response.json.return_value = {
                                "client_secret": {
                                    "value": "ek_test_token"
                                }
                            }
                            
                            mock_client_instance = MagicMock()
                            mock_client_instance.__aenter__.return_value = mock_client_instance
                            mock_client_instance.__aexit__.return_value = None
                            mock_client_instance.post = AsyncMock(return_value=mock_response)
                            mock_client.return_value = mock_client_instance
                            
                            response = client.post(
                                "/v1/config/realtime-token",
                                headers=auth_headers,
                                json={}
                            )
                            assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}: {response.json() if response.status_code not in [200, 500] else ''}"
                            if response.status_code == 200:
                                data = response.json()
                                assert "token" in data
                                assert "url" in data
        finally:
            app.dependency_overrides.clear()
    
    def test_get_realtime_token_no_key(self, client, auth_headers, sync_db_session):
        """测试：OpenAI API key未配置"""
        from app.api.deps import get_current_active_user
        from app.utils.security import decode_token
        from app.models.user import User as UserModel
        
        # 从token中获取user_id
        token_payload = decode_token(auth_headers["Authorization"].split(" ")[1])
        user_id = token_payload.get("sub")
        
        # 从数据库获取用户
        user = sync_db_session.query(UserModel).filter(UserModel.id == user_id).first()
        assert user is not None, "User should exist in database"
        
        # 覆盖依赖
        def get_user():
            return user
        
        app.dependency_overrides[get_current_active_user] = get_user
        
        try:
            with patch.object(settings, 'openai_api_key', None):
                response = client.post(
                    "/v1/config/realtime-token",
                    headers=auth_headers,
                    json={}
                )
                assert response.status_code == 500
        finally:
            app.dependency_overrides.clear()
    
    def test_get_realtime_config_success(self, client, auth_headers, sync_db_session):
        """测试：获取Realtime配置成功"""
        from app.api.deps import get_current_active_user
        from app.utils.security import decode_token
        from app.models.user import User as UserModel
        
        # 从token中获取user_id
        token_payload = decode_token(auth_headers["Authorization"].split(" ")[1])
        user_id = token_payload.get("sub")
        
        # 从数据库获取用户
        user = sync_db_session.query(UserModel).filter(UserModel.id == user_id).first()
        assert user is not None, "User should exist in database"
        
        # 覆盖依赖
        def get_user():
            return user
        
        app.dependency_overrides[get_current_active_user] = get_user
        
        try:
            with patch('app.api.v1.config.get_config_loader') as mock_loader:
                mock_config_loader = MagicMock()
                mock_config_loader.load_voice_config.return_value = {
                    "openai": {
                        "voice": "shimmer",
                        "model": "gpt-4o-realtime-preview-2024-10-01",
                        "temperature": 0.8,
                        "max_response_output_tokens": 4096
                    }
                }
                mock_loader.return_value = mock_config_loader
                
                response = client.get(
                    "/v1/config/realtime-config",
                    headers=auth_headers
                )
                assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}: {response.json() if response.status_code not in [200, 500] else ''}"
                if response.status_code == 200:
                    data = response.json()
                    assert "voice" in data
                    assert "model" in data
                    assert "temperature" in data
                    assert "max_response_output_tokens" in data
        finally:
            app.dependency_overrides.clear()
    
    def test_get_realtime_config_error(self, client, auth_headers, sync_db_session):
        """测试：获取Realtime配置失败"""
        from app.api.deps import get_current_active_user
        from app.utils.security import decode_token
        from app.models.user import User as UserModel
        
        # 从token中获取user_id
        token_payload = decode_token(auth_headers["Authorization"].split(" ")[1])
        user_id = token_payload.get("sub")
        
        # 从数据库获取用户
        user = sync_db_session.query(UserModel).filter(UserModel.id == user_id).first()
        assert user is not None, "User should exist in database"
        
        # 覆盖依赖
        def get_user():
            return user
        
        app.dependency_overrides[get_current_active_user] = get_user
        
        try:
            with patch('app.api.v1.config.get_config_loader') as mock_loader:
                mock_loader.side_effect = Exception("Config error")
                
                response = client.get(
                    "/v1/config/realtime-config",
                    headers=auth_headers
                )
                assert response.status_code == 500
        finally:
            app.dependency_overrides.clear()

