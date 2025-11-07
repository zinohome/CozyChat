"""
STT引擎测试

测试STT引擎的功能
"""

# 标准库
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import io

# 本地库
from app.engines.voice.stt.openai_stt import OpenAISTTEngine
from app.engines.voice.stt.factory import STTEngineFactory


class TestOpenAISTTEngine:
    """测试OpenAI STT引擎"""
    
    @pytest.fixture
    def stt_engine(self):
        """创建STT引擎"""
        config = {
            "provider": "openai",
            "model": "whisper-1",
            "api_key": "test_key"
        }
        return OpenAISTTEngine(config)
    
    @pytest.fixture
    def mock_openai_client(self, mocker):
        """Mock OpenAI客户端"""
        mock_client = MagicMock()
        # OpenAI API当response_format="text"时直接返回字符串
        mock_client.audio.transcriptions.create = AsyncMock(
            return_value="这是转录的文本"
        )
        return mock_client
    
    @pytest.mark.asyncio
    async def test_transcribe_success(self, stt_engine, mock_openai_client):
        """测试：转录成功"""
        with patch.object(stt_engine, 'client', mock_openai_client):
            # 创建模拟音频数据（bytes）
            audio_data = b"fake audio data"
            
            result = await stt_engine.transcribe(
                audio_data=audio_data,
                language="zh-CN"
            )
            
            assert isinstance(result, str)
            assert result == "这是转录的文本"
            mock_openai_client.audio.transcriptions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transcribe_with_language(self, stt_engine, mock_openai_client):
        """测试：带语言参数的转录"""
        with patch.object(stt_engine, 'client', mock_openai_client):
            audio_data = b"fake audio data"
            
            result = await stt_engine.transcribe(
                audio_data=audio_data,
                language="en"
            )
            
            assert isinstance(result, str)
            # 验证语言参数被传递
            call_args = mock_openai_client.audio.transcriptions.create.call_args
            assert call_args.kwargs.get("language") == "en"
    
    @pytest.mark.asyncio
    async def test_transcribe_error(self, stt_engine, mock_openai_client):
        """测试：转录错误处理"""
        from openai import APIError
        
        mock_openai_client.audio.transcriptions.create = AsyncMock(
            side_effect=APIError(message="API Error")
        )
        
        with patch.object(stt_engine, 'client', mock_openai_client):
            audio_data = b"fake audio data"
            
            with pytest.raises(Exception):
                await stt_engine.transcribe(audio_data=audio_data)
    
    def test_engine_initialization(self):
        """测试：引擎初始化"""
        config = {
            "model": "whisper-1",
            "api_key": "test_key"
        }
        engine = OpenAISTTEngine(config)
        
        assert engine.model == "whisper-1"
        assert engine.config.get("api_key") == "test_key"
    
    @pytest.mark.asyncio
    async def test_health_check(self, stt_engine):
        """测试：健康检查"""
        # STT引擎的健康检查通常返回True（如果没有实际连接）
        health = await stt_engine.health_check()
        assert isinstance(health, bool)


class TestSTTEngineFactory:
    """测试STT引擎工厂"""
    
    def test_create_openai_engine(self):
        """测试：创建OpenAI引擎"""
        config = {
            "model": "whisper-1",
            "api_key": "test_key"
        }
        
        engine = STTEngineFactory.create_engine("openai", config)
        
        assert engine is not None
        assert isinstance(engine, OpenAISTTEngine)
    
    def test_create_engine_invalid_provider(self):
        """测试：创建无效提供商的引擎"""
        config = {
            "model": "whisper-1"
        }
        
        with pytest.raises(ValueError):
            STTEngineFactory.create_engine("invalid", config)

