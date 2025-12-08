"""
聊天功能回归测试

确保所有现有功能在重构后仍然正常工作
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app


class TestChatRegression:
    """聊天功能回归测试类"""
    
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
    
    @pytest.mark.asyncio
    async def test_chat_completion_api_still_works(
        self,
        client,
        mock_user
    ):
        """测试：聊天补全API仍然工作"""
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
                    "message": {"role": "assistant", "content": "Hello!"},
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
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            # 验证响应格式与之前一致
            assert "id" in data
            assert "created" in data
            assert "model" in data
            assert "choices" in data
            assert "usage" in data
    
    @pytest.mark.asyncio
    async def test_chat_completion_response_format_unchanged(
        self,
        client,
        mock_user
    ):
        """测试：响应格式未改变"""
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
                    "message": {"role": "assistant", "content": "Hello!"},
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
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            # 验证响应结构
            assert isinstance(data["id"], str)
            assert isinstance(data["created"], int)
            assert isinstance(data["model"], str)
            assert isinstance(data["choices"], list)
            assert len(data["choices"]) > 0
            
            choice = data["choices"][0]
            assert "index" in choice
            assert "message" in choice
            assert "finish_reason" in choice
            
            assert choice["message"]["role"] == "assistant"
            assert "content" in choice["message"]
            
            assert "usage" in data
            assert "prompt_tokens" in data["usage"]
            assert "completion_tokens" in data["usage"]
            assert "total_tokens" in data["usage"]
    
    @pytest.mark.asyncio
    async def test_error_handling_unchanged(
        self,
        client,
        mock_user
    ):
        """测试：错误处理未改变"""
        # Arrange
        request_data = {
            "messages": [],
            "personality_id": "test-personality",
            "stream": False
        }
        
        # Mock认证
        with patch('app.api.deps.get_current_active_user_async', return_value=mock_user):
            # Act
            response = client.post(
                "/v1/chat/completions",
                json=request_data,
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Assert
            # 空消息列表应该返回400错误
            assert response.status_code == 400
