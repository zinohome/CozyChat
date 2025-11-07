"""
聊天API测试

测试聊天API的所有功能，包括：
- 创建聊天完成（非流式）
- 创建聊天完成（流式）
- 带人格的聊天
- 无效请求处理
- 列出引擎和模型
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.engines.ai.base import ChatMessage, ChatResponse, StreamChunk


class TestChatAPI:
    """测试聊天API"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_openai_engine(self):
        """Mock OpenAI引擎"""
        engine = MagicMock()
        engine.chat = AsyncMock(return_value=ChatResponse(
            id="chatcmpl-123",
            message=ChatMessage(role="assistant", content="Hello! How can I help you?"),
            model="gpt-3.5-turbo",
            finish_reason="stop",
            usage={"total_tokens": 50}
        ))
        
        async def mock_stream():
            yield StreamChunk(
                id="chatcmpl-123",
                delta={"content": "Hello"},
                model="gpt-3.5-turbo"
            )
        
        engine.chat_stream = mock_stream
        return engine
    
    @pytest.fixture
    def auth_token(self):
        """测试认证令牌"""
        from app.utils.security import create_access_token
        data = {"sub": "test-user-id", "username": "testuser", "role": "user"}
        return create_access_token(data)
    
    def test_create_chat_completion_success(self, client, mock_openai_engine, auth_token, mocker):
        """测试：创建聊天完成成功"""
        # Mock AI引擎工厂
        with patch('app.api.v1.chat.AIEngineFactory') as mock_factory:
            mock_factory_instance = MagicMock()
            mock_factory_instance.create_engine.return_value = mock_openai_engine
            mock_factory.return_value = mock_factory_instance
            
            response = client.post(
                "/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "model": "gpt-3.5-turbo"
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data or "content" in data
    
    def test_create_chat_completion_stream(self, client, mock_openai_engine, auth_token, mocker):
        """测试：创建流式聊天完成"""
        # Mock AI引擎工厂
        with patch('app.api.v1.chat.AIEngineFactory') as mock_factory:
            mock_factory_instance = MagicMock()
            mock_factory_instance.create_engine.return_value = mock_openai_engine
            mock_factory.return_value = mock_factory_instance
            
            response = client.post(
                "/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "model": "gpt-3.5-turbo",
                    "stream": True
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            assert response.headers.get("content-type") == "text/event-stream"
    
    def test_create_chat_completion_with_personality(self, client, mock_openai_engine, auth_token, mocker):
        """测试：带人格的聊天完成"""
        # Mock人格管理器
        with patch('app.api.v1.chat.PersonalityManager') as mock_personality_manager:
            mock_personality = MagicMock()
            mock_personality.id = "test-personality"
            mock_personality_manager.return_value.get_personality.return_value = mock_personality
            
            # Mock AI引擎工厂
            with patch('app.api.v1.chat.AIEngineFactory') as mock_factory:
                mock_factory_instance = MagicMock()
                mock_factory_instance.create_engine.return_value = mock_openai_engine
                mock_factory.return_value = mock_factory_instance
                
                response = client.post(
                    "/v1/chat/completions",
                    json={
                        "messages": [{"role": "user", "content": "Hello"}],
                        "model": "gpt-3.5-turbo",
                        "personality_id": "test-personality"
                    },
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                assert response.status_code == 200
    
    def test_create_chat_completion_invalid_request(self, client, auth_token):
        """测试：无效请求处理"""
        response = client.post(
            "/v1/chat/completions",
            json={},  # 缺少必需字段
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 422  # 验证错误
    
    def test_list_engines(self, client, auth_token):
        """测试：列出引擎"""
        response = client.get(
            "/v1/chat/engines",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data or isinstance(data, list)
    
    def test_list_models(self, client, auth_token):
        """测试：列出模型"""
        response = client.get(
            "/v1/chat/models",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "models" in data or isinstance(data, list)
