"""
RealTime引擎测试

测试RealTime引擎的功能
"""

# 标准库
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# 本地库
from app.engines.voice.realtime.openai_realtime import OpenAIRealtimeEngine
from app.engines.voice.realtime.factory import RealtimeEngineFactory


class TestOpenAIRealtimeEngine:
    """测试OpenAI RealTime引擎"""
    
    @pytest.fixture
    def realtime_engine(self):
        """创建RealTime引擎"""
        config = {
            "provider": "openai",
            "voice": "alloy",
            "api_key": "test_key"
        }
        return OpenAIRealtimeEngine(config)
    
    @pytest.mark.asyncio
    async def test_connect_success(self, realtime_engine):
        """测试：建立连接成功"""
        session_id = await realtime_engine.connect()
        
        assert isinstance(session_id, str)
        assert len(session_id) > 0
        assert realtime_engine.session_id == session_id
    
    @pytest.mark.asyncio
    async def test_send_audio(self, realtime_engine):
        """测试：发送音频数据"""
        # 先建立连接
        await realtime_engine.connect()
        
        # 发送音频数据（简化实现，只验证不抛出异常）
        audio_data = b"fake audio data"
        await realtime_engine.send_audio(audio_data)
        
        # 验证方法执行成功（不抛出异常）
        assert True
    
    @pytest.mark.asyncio
    async def test_receive_audio(self, realtime_engine):
        """测试：接收音频数据"""
        # 先建立连接
        await realtime_engine.connect()
        
        # 接收音频数据（简化实现）
        async for audio_chunk in realtime_engine.receive_audio():
            assert isinstance(audio_chunk, bytes)
            break  # 只测试一次
    
    @pytest.mark.asyncio
    async def test_disconnect(self, realtime_engine):
        """测试：断开连接"""
        # 先建立连接
        await realtime_engine.connect()
        
        # 断开连接
        await realtime_engine.disconnect()
        
        # 验证方法执行成功（不抛出异常）
        assert True
    
    def test_engine_initialization(self):
        """测试：引擎初始化"""
        config = {
            "voice": "alloy",
            "api_key": "test_key"
        }
        engine = OpenAIRealtimeEngine(config)
        
        assert engine.voice == "alloy"
        assert engine.config.get("api_key") == "test_key"
    
    @pytest.mark.asyncio
    async def test_health_check(self, realtime_engine):
        """测试：健康检查"""
        health = await realtime_engine.health_check()
        assert isinstance(health, bool)


class TestRealtimeEngineFactory:
    """测试RealTime引擎工厂"""
    
    def test_create_openai_engine(self):
        """测试：创建OpenAI引擎"""
        config = {
            "voice": "alloy",
            "api_key": "test_key"
        }
        
        engine = RealtimeEngineFactory.create_engine("openai", config)
        
        assert engine is not None
        assert isinstance(engine, OpenAIRealtimeEngine)
    
    def test_create_engine_invalid_provider(self):
        """测试：创建无效提供商的引擎"""
        config = {
            "voice": "alloy"
        }
        
        with pytest.raises(ValueError):
            RealtimeEngineFactory.create_engine("invalid", config)

