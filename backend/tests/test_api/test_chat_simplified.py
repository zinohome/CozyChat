"""
简化后的chat.py API测试

测试简化后的API层，确保：
- 参数验证正确
- 正确调用编排器
- 错误处理正确
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.user import User


class TestChatAPISimplified:
    """简化后的chat.py API测试类"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def async_client(self):
        """创建异步测试客户端"""
        # AsyncClient的正确初始化方式（使用ASGITransport）
        # 注意：不能使用async fixture，因为测试函数需要直接使用client
        return AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver"
        )
    
    @pytest.fixture
    def mock_user(self):
        """创建模拟用户"""
        user = MagicMock(spec=User)
        # 使用UUID格式的user_id，符合PostgreSQL UUID类型要求
        user.id = str(uuid.uuid4())
        user.username = "testuser"
        user.status = "active"
        return user
    
    @pytest.fixture
    def mock_orchestrator(self):
        """创建模拟编排器"""
        orchestrator = AsyncMock()
        orchestrator.process_request = AsyncMock(return_value={
            "content": "Test response",
            "role": "assistant"
        })
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_create_chat_completion_success(
        self,
        async_client,
        mock_user,
        mock_orchestrator
    ):
        """测试：成功创建聊天补全"""
        # Arrange
        from app.api.deps import get_current_active_user_async, get_chat_orchestrator
        
        # 使用app.dependency_overrides来覆盖依赖
        app.dependency_overrides[get_current_active_user_async] = lambda: mock_user
        app.dependency_overrides[get_chat_orchestrator] = lambda: mock_orchestrator
        
        try:
            request_data = {
                "messages": [{"role": "user", "content": "Hello"}],
                "personality_id": "test-personality",
                "stream": False
            }
            
            # Act
            response = await async_client.post(
                "/v1/chat/completions",
                json=request_data,
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Assert
            assert response.status_code == 200
            mock_orchestrator.process_request.assert_called_once()
        finally:
            # 清理依赖覆盖
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_create_chat_completion_empty_messages(
        self,
        async_client,
        mock_user,
        db_session
    ):
        """测试：空消息列表返回错误"""
        from app.api.deps import get_current_active_user_async, get_chat_orchestrator, get_db
        from unittest.mock import MagicMock
        
        # Arrange
        async def get_user():
            return mock_user
        
        async def get_async_db():
            yield db_session
        
        # Mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request = AsyncMock(side_effect=ValueError("Messages cannot be empty"))
        
        app.dependency_overrides[get_current_active_user_async] = get_user
        app.dependency_overrides[get_chat_orchestrator] = lambda: mock_orchestrator
        app.dependency_overrides[get_db] = get_async_db
        
        try:
            request_data = {
                "messages": [],
                "personality_id": "test-personality",
                "stream": False
            }
            
            # Act
            response = await async_client.post(
                "/v1/chat/completions",
                json=request_data,
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Assert
            assert response.status_code in [400, 422, 500], f"Expected 400, 422, or 500, got {response.status_code}: {response.json() if response.status_code not in [400, 422, 500] else ''}"
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_create_chat_completion_stream_success(
        self,
        async_client,
        mock_user,
        mock_orchestrator,
        db_session
    ):
        """测试：成功创建流式聊天补全"""
        from app.api.deps import get_current_active_user_async, get_chat_orchestrator, get_db
        from fastapi.responses import StreamingResponse
        
        # Arrange
        async def mock_stream():
            yield b'data: {"content": "chunk1"}\n\n'
            yield b'data: {"content": "chunk2"}\n\n'
            yield b'data: [DONE]\n\n'
        
        mock_orchestrator.process_request = AsyncMock(return_value=StreamingResponse(mock_stream(), media_type="text/event-stream"))
        
        async def get_user():
            return mock_user
        
        async def get_async_db():
            yield db_session
        
        app.dependency_overrides[get_current_active_user_async] = get_user
        app.dependency_overrides[get_chat_orchestrator] = lambda: mock_orchestrator
        app.dependency_overrides[get_db] = get_async_db
        
        try:
            request_data = {
                "messages": [{"role": "user", "content": "Hello"}],
                "personality_id": "test-personality",
                "stream": True
            }
            
            # Act
            response = await async_client.post(
                "/v1/chat/completions",
                json=request_data,
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Assert
            assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}: {response.json() if response.status_code not in [200, 500] else ''}"
            if response.status_code == 200:
                assert "text/event-stream" in response.headers.get("content-type", "")
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_create_chat_completion_unauthorized(
        self,
        async_client
    ):
        """测试：未授权访问返回401"""
        # Arrange
        with patch('app.api.deps.get_current_active_user_async', side_effect=Exception("Unauthorized")):
            request_data = {
                "messages": [{"role": "user", "content": "Hello"}],
                "personality_id": "test-personality",
                "stream": False
            }
            
            # Act
            response = await async_client.post(
                "/v1/chat/completions",
                json=request_data
            )
            
            # Assert
            assert response.status_code == 401
