"""
TTS引擎测试

测试TTS引擎的功能
"""

# 标准库
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import io

# 本地库
from app.engines.voice.tts.openai_tts import OpenAITTSEngine
from app.engines.voice.tts.factory import TTSEngineFactory


class TestOpenAITTSEngine:
    """测试OpenAI TTS引擎"""
    
    @pytest.fixture
    def tts_engine(self):
        """创建TTS引擎"""
        config = {
            "provider": "openai",
            "model": "tts-1",
            "voice": "alloy",
            "api_key": "test_key"
        }
        return OpenAITTSEngine(config)
    
    @pytest.fixture
    def mock_openai_client(self, mocker):
        """Mock OpenAI客户端"""
        mock_client = MagicMock()
        # 模拟音频响应
        mock_response = MagicMock()
        mock_response.content = b"fake audio content"
        mock_client.audio.speech.create = AsyncMock(return_value=mock_response)
        return mock_client
    
    @pytest.mark.asyncio
    async def test_synthesize_success(self, tts_engine, mock_openai_client):
        """测试：语音合成成功"""
        # 模拟响应对象，支持iter_bytes方法
        mock_response = MagicMock()
        async def mock_iter_bytes():
            yield b"fake audio content"
        mock_response.iter_bytes = mock_iter_bytes
        
        mock_openai_client.audio.speech.create = AsyncMock(return_value=mock_response)
        
        with patch.object(tts_engine, 'client', mock_openai_client):
            result = await tts_engine.synthesize(
                text="这是测试文本",
                voice="alloy",
                speed=1.0
            )
            
            assert isinstance(result, bytes)
            assert result == b"fake audio content"
            mock_openai_client.audio.speech.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_synthesize_stream(self, tts_engine, mock_openai_client):
        """测试：流式语音合成"""
        # 模拟流式响应
        mock_response = MagicMock()
        async def mock_iter_bytes():
            yield b"chunk1"
            yield b"chunk2"
            yield b"chunk3"
        mock_response.iter_bytes = mock_iter_bytes
        
        mock_openai_client.audio.speech.create = AsyncMock(return_value=mock_response)
        
        with patch.object(tts_engine, 'client', mock_openai_client):
            chunks = []
            async for chunk in tts_engine.stream_synthesize(
                text="这是测试文本",
                voice="alloy"
            ):
                chunks.append(chunk)
            
            assert len(chunks) > 0
            assert all(isinstance(chunk, bytes) for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_synthesize_with_parameters(self, tts_engine, mock_openai_client):
        """测试：带参数的语音合成"""
        mock_response = MagicMock()
        async def mock_iter_bytes():
            yield b"audio"
        mock_response.iter_bytes = mock_iter_bytes
        
        mock_openai_client.audio.speech.create = AsyncMock(return_value=mock_response)
        
        with patch.object(tts_engine, 'client', mock_openai_client):
            result = await tts_engine.synthesize(
                text="测试文本",
                voice="nova",
                speed=1.5
            )
            
            assert isinstance(result, bytes)
            # 验证参数被传递
            call_args = mock_openai_client.audio.speech.create.call_args
            assert call_args.kwargs.get("voice") == "nova"
            assert call_args.kwargs.get("speed") == 1.5
    
    @pytest.mark.asyncio
    async def test_synthesize_error(self, tts_engine, mock_openai_client):
        """测试：语音合成错误处理"""
        from openai import APIError
        from unittest.mock import Mock
        
        # APIError需要request和body参数
        mock_request = Mock()
        mock_body = Mock()
        mock_openai_client.audio.speech.create = AsyncMock(
            side_effect=APIError(message="API Error", request=mock_request, body=mock_body)
        )
        
        with patch.object(tts_engine, 'client', mock_openai_client):
            with pytest.raises(Exception):
                await tts_engine.synthesize(text="测试文本")
    
    def test_engine_initialization(self):
        """测试：引擎初始化"""
        config = {
            "model": "tts-1",
            "voice": "alloy",
            "api_key": "test_key"
        }
        engine = OpenAITTSEngine(config)
        
        assert engine.voice == "alloy"
        assert engine.config.get("api_key") == "test_key"
    
    @pytest.mark.asyncio
    async def test_health_check(self, tts_engine):
        """测试：健康检查"""
        health = await tts_engine.health_check()
        assert isinstance(health, bool)


class TestTTSEngineFactory:
    """测试TTS引擎工厂"""
    
    def test_create_openai_engine(self):
        """测试：创建OpenAI引擎"""
        config = {
            "model": "tts-1",
            "voice": "alloy",
            "api_key": "test_key"
        }
        
        engine = TTSEngineFactory.create_engine("openai", config)
        
        assert engine is not None
        assert isinstance(engine, OpenAITTSEngine)
    
    def test_create_engine_invalid_provider(self):
        """测试：创建无效提供商的引擎"""
        config = {
            "model": "tts-1"
        }
        
        with pytest.raises(ValueError):
            TTSEngineFactory.create_engine("invalid", config)

