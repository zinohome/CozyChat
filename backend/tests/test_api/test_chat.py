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
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.engines.ai.base import ChatMessage, ChatResponse, StreamChunk
from app.engines.ai.factory import AIEngineFactory


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
        
        engine.chat_stream = AsyncMock(return_value=mock_stream())
        # 修复chat_stream为异步生成器
        async def async_generator():
            yield StreamChunk(
                id="chatcmpl-123",
                delta={"content": "Hello"},
                model="gpt-3.5-turbo"
            )
        engine.chat_stream = async_generator
        return engine
    
    @pytest.fixture
    def auth_token(self, sync_db_session):
        """测试认证令牌（需要创建真实用户）"""
        from app.utils.security import create_access_token, hash_password
        from app.models.user import User as UserModel
        
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
    
    def test_create_chat_completion_success(self, client, mock_openai_engine, auth_token, sync_db_session):
        """测试：创建聊天完成成功"""
        from datetime import datetime
        from app.api.deps import get_chat_orchestrator, get_current_active_user_async
        from app.models.user import User as UserModel
        
        # 从token中获取user_id（auth_token fixture已经创建了用户）
        from app.utils.security import decode_token
        token_payload = decode_token(auth_token)
        user_id = token_payload.get("sub")
        
        # 从数据库获取用户
        user = sync_db_session.query(UserModel).filter(UserModel.id == user_id).first()
        assert user is not None, "User should exist in database"
        
        # Mock编排器
        mock_orchestrator = AsyncMock()
        mock_orchestrator.process_request = AsyncMock(return_value={
            "id": "chatcmpl-123",
            "created": int(datetime.now().timestamp()),
            "model": "gpt-3.5-turbo",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "Hello! How can I help you?"},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 40, "total_tokens": 50}
        })
        
        # 使用app.dependency_overrides来覆盖依赖
        # 注意：get_current_active_user_async需要返回用户对象
        async def get_user():
            return user
        
        app.dependency_overrides[get_current_active_user_async] = get_user
        app.dependency_overrides[get_chat_orchestrator] = lambda: mock_orchestrator
        
        try:
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
            assert "choices" in data or "message" in data or "content" in data
        finally:
            # 清理依赖覆盖
            app.dependency_overrides.clear()
    
    def test_create_chat_completion_stream(self, client, mock_openai_engine, auth_token):
        """测试：创建流式聊天完成"""
        # Mock AI引擎工厂
        with patch.object(AIEngineFactory, 'create_engine', return_value=mock_openai_engine):
            # 设置流式响应
            async def mock_stream():
                from app.engines.ai.base import StreamChunk
                yield StreamChunk(
                    id="chatcmpl-123",
                    delta={"content": "Hello"},
                    model="gpt-3.5-turbo"
                )
            
            mock_openai_engine.chat_stream = mock_stream
            
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
            assert "text/event-stream" in response.headers.get("content-type", "")
    
    def test_create_chat_completion_stream_error(self, client, mock_openai_engine, auth_token):
        """测试：流式聊天完成错误处理"""
        with patch.object(AIEngineFactory, 'create_engine', return_value=mock_openai_engine):
            # 设置流式响应抛出异常
            async def failing_stream():
                raise Exception("Stream error")
                yield  # 永远不会执行
            
            mock_openai_engine.chat_stream = failing_stream
            
            response = client.post(
                "/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "model": "gpt-3.5-turbo",
                    "stream": True
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # 流式响应即使有错误也会返回200，但内容包含错误信息
            assert response.status_code == 200
    
    def test_create_chat_completion_with_personality(self, client, mock_openai_engine, auth_token):
        """测试：带人格的聊天完成（当前chat.py不支持personality_id，暂时跳过）"""
        # 注意：当前chat.py API不支持personality_id参数
        # 这个测试暂时跳过，等chat.py支持personality后再启用
        pytest.skip("chat.py API currently does not support personality_id")
    
    def test_create_chat_completion_invalid_request(self, client, auth_token):
        """测试：无效请求处理"""
        response = client.post(
            "/v1/chat/completions",
            json={},  # 缺少必需字段
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 422  # 验证错误
    
    def test_create_chat_completion_engine_error(self, client, auth_token):
        """测试：引擎创建错误"""
        with patch.object(AIEngineFactory, 'create_engine', side_effect=ValueError("Invalid engine")):
            response = client.post(
                "/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "model": "gpt-3.5-turbo"
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 400
    
    def test_create_chat_completion_chat_error(self, client, mock_openai_engine, auth_token):
        """测试：聊天生成错误"""
        with patch.object(AIEngineFactory, 'create_engine', return_value=mock_openai_engine):
            mock_openai_engine.chat = AsyncMock(side_effect=Exception("Chat error"))
            
            response = client.post(
                "/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "model": "gpt-3.5-turbo"
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 500
    
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
        assert "data" in data
        assert isinstance(data["data"], list)
