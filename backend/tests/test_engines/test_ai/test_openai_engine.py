"""
OpenAI引擎测试

测试OpenAI引擎的所有功能，包括：
- 聊天完成（非流式）
- 流式响应
- 工具调用
- 错误处理
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from app.engines.ai.openai_engine import OpenAIEngine
from app.engines.ai.base import ChatMessage, ChatResponse, StreamChunk


class TestOpenAIEngine:
    """测试OpenAI引擎"""
    
    @pytest.fixture
    def engine_config(self):
        """引擎配置"""
        return {
            "model": "gpt-3.5-turbo",
            "api_key": "test-api-key",
            "base_url": "https://api.openai.com/v1"
        }
    
    @pytest.fixture
    def openai_engine(self, engine_config):
        """OpenAI引擎实例"""
        return OpenAIEngine(**engine_config)
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI响应"""
        mock_response = MagicMock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.created = 1234567890
        
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.role = "assistant"
        mock_message.content = "Hello! How can I help you?"
        mock_message.function_call = None
        mock_message.tool_calls = None
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]
        
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30
        mock_response.usage = mock_usage
        
        return mock_response
    
    @pytest.fixture
    def test_messages(self):
        """测试消息列表"""
        return [
            ChatMessage(role="user", content="Hello")
        ]
    
    # ========== 引擎初始化测试 ==========
    
    def test_engine_initialization(self, engine_config):
        """测试：引擎初始化"""
        engine = OpenAIEngine(**engine_config)
        
        assert engine.engine_name == "openai"
        assert engine.model == engine_config["model"]
        assert engine.api_key == engine_config["api_key"]
        assert engine.base_url == engine_config["base_url"]
        assert engine.client is not None
    
    # ========== 聊天完成测试 ==========
    
    @pytest.fixture
    def openai_engine_async(self, engine_config):
        """OpenAI引擎实例（异步测试用）"""
        return OpenAIEngine(**engine_config)
    
    @pytest.mark.asyncio
    async def test_chat_completion_success(self, openai_engine_async, mock_openai_response, test_messages, mocker):
        """测试：聊天完成成功"""
        # Mock OpenAI API调用
        mock_create = AsyncMock(return_value=mock_openai_response)
        mocker.patch.object(
            openai_engine_async.client.chat.completions,
            "create",
            mock_create
        )
        
        # 执行测试
        result = await openai_engine_async.chat(test_messages)
        
        # 验证结果
        assert isinstance(result, ChatResponse)
        assert result.id == "chatcmpl-123"
        assert result.message.role == "assistant"
        assert result.message.content == "Hello! How can I help you?"
        assert result.model == "gpt-3.5-turbo"
        assert result.finish_reason == "stop"
        assert result.usage is not None
        assert result.usage["total_tokens"] == 30
        
        # 验证API调用
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args[1]["model"] == "gpt-3.5-turbo"
        assert call_args[1]["stream"] is False
    
    @pytest.mark.asyncio
    async def test_chat_completion_with_tools(self, openai_engine_async, mock_openai_response, test_messages, mocker):
        """测试：带工具调用的聊天完成"""
        # 设置工具调用响应
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_function = MagicMock()
        mock_function.name = "search"
        mock_function.arguments = '{"query": "test"}'
        mock_tool_call.function = mock_function
        
        mock_openai_response.choices[0].message.tool_calls = [mock_tool_call]
        mock_openai_response.choices[0].message.content = None
        
        # Mock OpenAI API调用
        mock_create = AsyncMock(return_value=mock_openai_response)
        mocker.patch.object(
            openai_engine_async.client.chat.completions,
            "create",
            mock_create
        )
        
        # 执行测试
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Search the web",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        }
                    }
                }
            }
        ]
        
        result = await openai_engine_async.chat(test_messages, tools=tools)
        
        # 验证结果
        assert result.message.tool_calls is not None
        assert len(result.message.tool_calls) == 1
        assert result.message.tool_calls[0]["function"]["name"] == "search"
        
        # 验证工具参数传递
        call_args = mock_create.call_args
        assert "tools" in call_args[1]
    
    @pytest.mark.asyncio
    async def test_chat_completion_api_error(self, openai_engine_async, test_messages, mocker):
        """测试：API错误处理"""
        from openai import APIError
        
        # Mock API错误
        mock_create = AsyncMock(side_effect=APIError(
            message="API Error",
            request=None,
            response=None
        ))
        mocker.patch.object(
            openai_engine_async.client.chat.completions,
            "create",
            mock_create
        )
        
        # 执行测试并验证异常
        with pytest.raises(APIError):
            await openai_engine_async.chat(test_messages)
    
    @pytest.mark.asyncio
    async def test_chat_completion_with_temperature(self, openai_engine_async, mock_openai_response, test_messages, mocker):
        """测试：带温度参数的聊天完成"""
        mock_create = AsyncMock(return_value=mock_openai_response)
        mocker.patch.object(
            openai_engine_async.client.chat.completions,
            "create",
            mock_create
        )
        
        # 执行测试
        await openai_engine_async.chat(test_messages, temperature=0.9)
        
        # 验证温度参数传递
        call_args = mock_create.call_args
        assert call_args[1]["temperature"] == 0.9
    
    @pytest.mark.asyncio
    async def test_chat_completion_with_max_tokens(self, openai_engine_async, mock_openai_response, test_messages, mocker):
        """测试：带最大token数的聊天完成"""
        mock_create = AsyncMock(return_value=mock_openai_response)
        mocker.patch.object(
            openai_engine_async.client.chat.completions,
            "create",
            mock_create
        )
        
        # 执行测试
        await openai_engine_async.chat(test_messages, max_tokens=100)
        
        # 验证max_tokens参数传递
        call_args = mock_create.call_args
        assert call_args[1]["max_tokens"] == 100
    
    # ========== 流式响应测试 ==========
    
    @pytest.mark.asyncio
    async def test_chat_stream_success(self, openai_engine_async, test_messages, mocker):
        """测试：流式响应成功"""
        # Mock流式响应
        mock_chunk1 = MagicMock()
        mock_chunk1.id = "chatcmpl-123"
        mock_chunk1.model = "gpt-3.5-turbo"
        mock_chunk1.created = 1234567890
        mock_choice1 = MagicMock()
        mock_choice1.delta = MagicMock()
        mock_choice1.delta.role = None
        mock_choice1.delta.content = "Hello"
        mock_choice1.delta.function_call = None
        mock_choice1.delta.tool_calls = None
        mock_choice1.finish_reason = None
        mock_chunk1.choices = [mock_choice1]
        
        mock_chunk2 = MagicMock()
        mock_chunk2.id = "chatcmpl-123"
        mock_chunk2.model = "gpt-3.5-turbo"
        mock_chunk2.created = 1234567890
        mock_choice2 = MagicMock()
        mock_choice2.delta = MagicMock()
        mock_choice2.delta.role = None
        mock_choice2.delta.content = " there"
        mock_choice2.delta.function_call = None
        mock_choice2.delta.tool_calls = None
        mock_choice2.finish_reason = None
        mock_chunk2.choices = [mock_choice2]
        
        mock_chunk3 = MagicMock()
        mock_chunk3.id = "chatcmpl-123"
        mock_chunk3.model = "gpt-3.5-turbo"
        mock_chunk3.created = 1234567890
        mock_choice3 = MagicMock()
        mock_choice3.delta = MagicMock()
        mock_choice3.delta.role = None
        mock_choice3.delta.content = "!"
        mock_choice3.delta.function_call = None
        mock_choice3.delta.tool_calls = None
        mock_choice3.finish_reason = "stop"
        mock_chunk3.choices = [mock_choice3]
        
        # 创建异步生成器
        async def mock_stream():
            for chunk in [mock_chunk1, mock_chunk2, mock_chunk3]:
                yield chunk
        
        # Mock OpenAI API调用
        mock_create = AsyncMock(return_value=mock_stream())
        mocker.patch.object(
            openai_engine_async.client.chat.completions,
            "create",
            mock_create
        )
        
        # 执行测试
        chunks = []
        async for chunk in openai_engine_async.chat_stream(test_messages):
            chunks.append(chunk)
        
        # 验证结果
        assert len(chunks) == 3
        assert chunks[0].delta["content"] == "Hello"
        assert chunks[1].delta["content"] == " there"
        assert chunks[2].delta["content"] == "!"
        assert chunks[2].finish_reason == "stop"
        
        # 验证API调用
        call_args = mock_create.call_args
        assert call_args[1]["stream"] is True
    
    @pytest.mark.asyncio
    async def test_chat_stream_error(self, openai_engine_async, test_messages, mocker):
        """测试：流式响应错误处理"""
        from openai import OpenAIError
        
        # Mock流式错误
        async def mock_error_stream():
            raise OpenAIError("Streaming error")
            yield  # 永远不会执行
        
        mock_create = AsyncMock(return_value=mock_error_stream())
        mocker.patch.object(
            openai_engine_async.client.chat.completions,
            "create",
            mock_create
        )
        
        # 执行测试并验证异常
        with pytest.raises(OpenAIError):
            async for chunk in openai_engine_async.chat_stream(test_messages):
                pass

