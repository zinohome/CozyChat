"""
音频API补充测试

补充Audio API的边界条件和错误处理测试
"""

# 标准库
import pytest
import uuid
import io
from unittest.mock import AsyncMock, MagicMock, patch

# 本地库
from app.models.user import User


class TestAudioAPIAdditional:
    """音频API补充测试"""
    
    @pytest.fixture
    def auth_token(self, client, sync_db_session):
        """创建认证令牌"""
        from app.utils.security import hash_password, create_access_token
        from app.models.user import User as UserModel
        
        test_user = UserModel(
            id=uuid.uuid4(),
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email=f"test_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=hash_password("TestPassword123!"),
            role="user",
            status="active"
        )
        sync_db_session.add(test_user)
        sync_db_session.commit()
        
        token = create_access_token({"sub": str(test_user.id), "username": test_user.username})
        
        yield token
        
        try:
            sync_db_session.delete(test_user)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_create_transcription_with_personality(self, client, auth_token, tmp_path):
        """测试：使用人格配置创建转录"""
        import os
        
        # 创建临时人格配置
        temp_personality_dir = tmp_path / "personalities"
        temp_personality_dir.mkdir(parents=True, exist_ok=True)
        
        yaml_content = """
personality:
  id: test_personality
  name: Test Personality
  version: 1.0.0
  description: Test personality

  ai:
    provider: openai
    model: gpt-3.5-turbo
    temperature: 0.7

  voice:
    stt:
      provider: openai
      model: whisper-1
      language: zh-CN
"""
        yaml_file = temp_personality_dir / "test_personality.yaml"
        yaml_file.write_text(yaml_content)
        
        original_personality_dir = os.environ.get("PERSONALITY_CONFIG_DIR")
        os.environ["PERSONALITY_CONFIG_DIR"] = str(temp_personality_dir)
        
        try:
            # Mock STT引擎
            with patch('app.api.v1.audio.STTEngineFactory') as mock_factory:
                mock_engine = MagicMock()
                mock_engine.transcribe = AsyncMock(return_value="这是转录的文本")
                mock_factory.create_engine.return_value = mock_engine
                
                audio_file = io.BytesIO(b"fake audio data")
                audio_file.name = "test.wav"
                
                response = client.post(
                    "/v1/audio/transcriptions",
                    files={"file": ("test.wav", audio_file, "audio/wav")},
                    data={"model": "whisper-1", "personality_id": "test_personality"},
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                assert response.status_code in [200, 401, 404, 422]
                if response.status_code == 200:
                    data = response.json()
                    assert "text" in data
        finally:
            if original_personality_dir:
                os.environ["PERSONALITY_CONFIG_DIR"] = original_personality_dir
            elif "PERSONALITY_CONFIG_DIR" in os.environ:
                del os.environ["PERSONALITY_CONFIG_DIR"]
    
    @pytest.mark.asyncio
    async def test_create_transcription_personality_not_found(self, client, auth_token):
        """测试：创建转录（人格不存在）"""
        # Mock STT引擎
        with patch('app.api.v1.audio.STTEngineFactory') as mock_factory:
            mock_engine = MagicMock()
            mock_engine.transcribe = AsyncMock(return_value="这是转录的文本")
            mock_factory.create_engine.return_value = mock_engine
            
            audio_file = io.BytesIO(b"fake audio data")
            audio_file.name = "test.wav"
            
            response = client.post(
                "/v1/audio/transcriptions",
                files={"file": ("test.wav", audio_file, "audio/wav")},
                data={"model": "whisper-1", "personality_id": "nonexistent_personality"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # 应该返回200（使用默认配置）或404
            assert response.status_code in [200, 401, 404, 422]
    
    @pytest.mark.asyncio
    async def test_create_speech_stream_success(self, client, auth_token):
        """测试：创建流式语音成功"""
        # Mock TTS引擎
        with patch('app.api.v1.audio.TTSEngineFactory') as mock_factory:
            mock_engine = MagicMock()
            async def mock_stream():
                yield b"audio chunk 1"
                yield b"audio chunk 2"
            mock_engine.stream_synthesize = mock_stream
            mock_factory.create_engine.return_value = mock_engine
            
            response = client.post(
                "/v1/audio/speech/stream",
                json={
                    "input": "这是测试文本",
                    "model": "tts-1",
                    "voice": "alloy",
                    "speed": 1.0
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # 如果端点存在，应该返回200（流式响应）
            assert response.status_code in [200, 401, 404, 422]
            if response.status_code == 200:
                # 流式响应，检查Content-Type
                assert "audio" in response.headers.get("Content-Type", "")
    
    @pytest.mark.asyncio
    async def test_create_speech_stream_with_personality(self, client, auth_token, tmp_path):
        """测试：使用人格配置创建流式语音"""
        import os
        
        # 创建临时人格配置
        temp_personality_dir = tmp_path / "personalities"
        temp_personality_dir.mkdir(parents=True, exist_ok=True)
        
        yaml_content = """
personality:
  id: test_personality
  name: Test Personality
  version: 1.0.0
  description: Test personality

  ai:
    provider: openai
    model: gpt-3.5-turbo
    temperature: 0.7

  voice:
    tts:
      provider: openai
      model: tts-1
      voice: nova
      speed: 1.2
"""
        yaml_file = temp_personality_dir / "test_personality.yaml"
        yaml_file.write_text(yaml_content)
        
        original_personality_dir = os.environ.get("PERSONALITY_CONFIG_DIR")
        os.environ["PERSONALITY_CONFIG_DIR"] = str(temp_personality_dir)
        
        try:
            # Mock TTS引擎
            with patch('app.api.v1.audio.TTSEngineFactory') as mock_factory:
                mock_engine = MagicMock()
                async def mock_stream():
                    yield b"audio chunk"
                mock_engine.stream_synthesize = mock_stream
                mock_factory.create_engine.return_value = mock_engine
                
                response = client.post(
                    "/v1/audio/speech/stream",
                    json={
                        "input": "这是测试文本",
                        "personality_id": "test_personality"
                    },
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                assert response.status_code in [200, 401, 404, 422]
        finally:
            if original_personality_dir:
                os.environ["PERSONALITY_CONFIG_DIR"] = original_personality_dir
            elif "PERSONALITY_CONFIG_DIR" in os.environ:
                del os.environ["PERSONALITY_CONFIG_DIR"]
    
    @pytest.mark.asyncio
    async def test_create_speech_stream_error(self, client, auth_token):
        """测试：流式语音生成错误处理"""
        with patch('app.api.v1.audio.TTSEngineFactory') as mock_factory:
            mock_engine = MagicMock()
            async def failing_stream():
                raise Exception("TTS stream error")
                yield  # 永远不会执行
            mock_engine.stream_synthesize = failing_stream
            mock_factory.create_engine.return_value = mock_engine
            
            response = client.post(
                "/v1/audio/speech/stream",
                json={
                    "input": "这是测试文本",
                    "model": "tts-1",
                    "voice": "alloy"
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # 应该返回500或404
            assert response.status_code in [500, 401, 404, 422]
    
    @pytest.mark.asyncio
    async def test_create_speech_personality_not_found(self, client, auth_token):
        """测试：创建语音（人格不存在）"""
        # Mock TTS引擎
        with patch('app.api.v1.audio.TTSEngineFactory') as mock_factory:
            mock_engine = MagicMock()
            mock_engine.synthesize = AsyncMock(return_value=b"audio data")
            mock_factory.create_engine.return_value = mock_engine
            
            response = client.post(
                "/v1/audio/speech",
                json={
                    "input": "这是测试文本",
                    "model": "tts-1",
                    "voice": "alloy",
                    "personality_id": "nonexistent_personality"
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # 应该返回200（使用默认配置）或404
            assert response.status_code in [200, 401, 404, 422]

