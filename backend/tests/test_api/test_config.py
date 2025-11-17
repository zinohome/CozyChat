"""
配置管理API测试

测试配置管理API端点
"""

# 标准库
import pytest
from unittest.mock import patch, MagicMock

# 本地库
from app.api.v1.config import router
from app.config.config import settings


class TestConfigAPI:
    """测试配置管理API"""
    
    @pytest.fixture
    def client(self, test_client):
        """测试客户端"""
        return test_client
    
    @pytest.fixture
    def auth_headers(self, test_user_token):
        """认证头"""
        return {"Authorization": f"Bearer {test_user_token}"}
    
    def test_get_openai_config_success(self, client, auth_headers):
        """测试：获取OpenAI配置成功"""
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
    
    def test_get_openai_config_no_key(self, client, auth_headers):
        """测试：OpenAI API key未配置"""
        with patch.object(settings, 'openai_api_key', None):
            response = client.get(
                "/v1/config/openai-config",
                headers=auth_headers
            )
            assert response.status_code == 500
    
    def test_get_openai_config_unauthorized(self, client):
        """测试：未授权访问"""
        response = client.get("/v1/config/openai-config")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_realtime_token_success(self, client, auth_headers):
        """测试：获取Realtime token成功"""
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
                        assert response.status_code == 200
                        data = response.json()
                        assert "token" in data
                        assert "url" in data
                        assert "model" in data
    
    def test_get_realtime_token_no_key(self, client, auth_headers):
        """测试：OpenAI API key未配置"""
        with patch.object(settings, 'openai_api_key', None):
            response = client.post(
                "/v1/config/realtime-token",
                headers=auth_headers,
                json={}
            )
            assert response.status_code == 500
    
    def test_get_realtime_config_success(self, client, auth_headers):
        """测试：获取Realtime配置成功"""
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
            assert response.status_code == 200
            data = response.json()
            assert "voice" in data
            assert "model" in data
            assert "temperature" in data
            assert "max_response_output_tokens" in data
    
    def test_get_realtime_config_error(self, client, auth_headers):
        """测试：获取Realtime配置失败"""
        with patch('app.api.v1.config.get_config_loader') as mock_loader:
            mock_loader.side_effect = Exception("Config error")
            
            response = client.get(
                "/v1/config/realtime-config",
                headers=auth_headers
            )
            assert response.status_code == 500

