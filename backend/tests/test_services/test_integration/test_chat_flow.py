"""
聊天流程集成测试

测试完整的聊天流程，包括：
- 非流式对话流程
- 流式对话流程
- 工具调用流程
- 记忆检索和保存流程
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app


class TestChatFlowIntegration:
    """聊天流程集成测试类"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """创建模拟用户"""
        user = MagicMock()
        user.id = "test-user-id"
        user.username = "testuser"
        user.status = "active"
        return user
    
    @pytest.fixture
    def mock_token(self):
        """创建模拟token"""
        return "test-token"
    
    @pytest.mark.asyncio
    async def test_non_stream_chat_flow(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试：非流式聊天流程"""
        # Arrange
        request_data = {
            "messages": [{"role": "user", "content": "Hello"}],
            "personality_id": "test-personality",
            "stream": False
        }
        
        # Mock认证和编排器
        with patch('app.api.deps.get_current_active_user_async', return_value=mock_user), \
             patch('app.api.deps.get_chat_orchestrator') as mock_get_orchestrator:
            
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_request = AsyncMock(return_value={
                "id": "test-id",
                "created": 1234567890,
                "model": "gpt-3.5-turbo",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello! How can I help you?"},
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15
                }
            })
            mock_get_orchestrator.return_value = mock_orchestrator
            
            # Act
            response = client.post(
                "/v1/chat/completions",
                json=request_data,
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "choices" in data
            assert len(data["choices"]) > 0
    
    @pytest.mark.asyncio
    async def test_stream_chat_flow(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试：流式聊天流程"""
        # Arrange
        request_data = {
            "messages": [{"role": "user", "content": "Hello"}],
            "personality_id": "test-personality",
            "stream": True
        }
        
        # Mock流式响应
        async def mock_stream():
            yield b'data: {"content": "Hello"}\n\n'
            yield b'data: {"content": " there"}\n\n'
            yield b'data: [DONE]\n\n'
        
        # Mock认证和编排器
        with patch('app.api.deps.get_current_active_user_async', return_value=mock_user), \
             patch('app.api.deps.get_chat_orchestrator') as mock_get_orchestrator:
            
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_request = AsyncMock(return_value=mock_stream())
            mock_get_orchestrator.return_value = mock_orchestrator
            
            # Act
            response = client.post(
                "/v1/chat/completions",
                json=request_data,
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            # Assert
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"
    
    @pytest.mark.asyncio
    async def test_chat_with_memory(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试：带记忆的聊天流程"""
        # Arrange
        request_data = {
            "messages": [{"role": "user", "content": "What did we talk about?"}],
            "personality_id": "test-personality",
            "stream": False,
            "use_memory": True
        }
        
        # Mock认证和编排器
        with patch('app.api.deps.get_current_active_user_async', return_value=mock_user), \
             patch('app.api.deps.get_chat_orchestrator') as mock_get_orchestrator:
            
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_request = AsyncMock(return_value={
                "id": "test-id",
                "created": 1234567890,
                "model": "gpt-3.5-turbo",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": "We talked about Python."},
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 20,
                    "completion_tokens": 10,
                    "total_tokens": 30
                }
            })
            mock_get_orchestrator.return_value = mock_orchestrator
            
            # Act
            response = client.post(
                "/v1/chat/completions",
                json=request_data,
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "choices" in data
