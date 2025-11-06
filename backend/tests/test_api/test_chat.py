"""
Chat API测试

测试聊天接口功能
"""

# 第三方库
import pytest
from httpx import AsyncClient

# 本地库
from app.schemas.chat import ChatCompletionRequest


@pytest.mark.asyncio
class TestChatAPI:
    """测试Chat API"""
    
    async def test_list_engines(self, async_client: AsyncClient):
        """测试列出引擎"""
        response = await async_client.get("/v1/chat/engines")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "engines" in data
        assert "openai" in data["engines"]
        assert "ollama" in data["engines"]
        assert data["default_engine"] == "openai"
    
    async def test_list_models(self, async_client: AsyncClient):
        """测试列出模型"""
        response = await async_client.get("/v1/chat/models")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["object"] == "list"
        assert "data" in data
        assert len(data["data"]) > 0
        
        # 检查模型信息
        model_ids = [m["id"] for m in data["data"]]
        assert "gpt-3.5-turbo" in model_ids
        assert "gpt-4" in model_ids
    
    @pytest.mark.skip(reason="需要真实的OpenAI API Key")
    async def test_chat_completions_non_stream(self, async_client: AsyncClient):
        """测试非流式聊天补全"""
        request_data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Say 'test' only"}
            ],
            "temperature": 0.1,
            "max_tokens": 10,
            "stream": False,
            "engine_type": "openai"
        }
        
        response = await async_client.post("/v1/chat/completions", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["object"] == "chat.completion"
        assert "choices" in data
        assert len(data["choices"]) > 0
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert "usage" in data
    
    async def test_chat_completions_invalid_engine(self, async_client: AsyncClient):
        """测试使用无效引擎"""
        request_data = {
            "model": "test-model",
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "engine_type": "invalid_engine"
        }
        
        response = await async_client.post("/v1/chat/completions", json=request_data)
        
        assert response.status_code == 400  # Bad Request
    
    async def test_chat_completions_missing_messages(self, async_client: AsyncClient):
        """测试缺少消息字段"""
        request_data = {
            "model": "gpt-3.5-turbo",
            "engine_type": "openai"
        }
        
        response = await async_client.post("/v1/chat/completions", json=request_data)
        
        assert response.status_code == 422  # Validation Error

