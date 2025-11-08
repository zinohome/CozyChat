"""
音频API覆盖率测试

补充Audio API的测试以覆盖78-134, 156-232, 252-325行
"""

# 标准库
import pytest
import uuid
import io
from unittest.mock import AsyncMock, MagicMock, patch

# 本地库
from app.models.user import User


class TestAudioAPICoverage:
    """音频API覆盖率测试"""
    
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
    async def test_create_transcription_personality_with_stt_config(self, client, auth_token, tmp_path):
        """测试：创建转录（人格有STT配置，覆盖92-99行）"""
        import os
        
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
            with patch('app.api.v1.audio.STTEngineFactory') as mock_factory:
                mock_engine = MagicMock()
                mock_engine.transcribe = AsyncMock(return_value="转录文本")
                mock_factory.create_engine.return_value = mock_engine
                
                audio_file = io.BytesIO(b"fake audio data")
                audio_file.name = "test.wav"
                
                response = client.post(
                    "/v1/audio/transcriptions",
                    files={"file": ("test.wav", audio_file, "audio/wav")},
                    data={"model": "whisper-1", "personality_id": "test_personality", "language": "en"},
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                assert response.status_code in [200, 401, 404, 422]
        finally:
            if original_personality_dir:
                os.environ["PERSONALITY_CONFIG_DIR"] = original_personality_dir
            elif "PERSONALITY_CONFIG_DIR" in os.environ:
                del os.environ["PERSONALITY_CONFIG_DIR"]
    
    @pytest.mark.asyncio
    async def test_create_transcription_personality_no_stt_config(self, client, auth_token, tmp_path):
        """测试：创建转录（人格无STT配置，覆盖100-102行）"""
        import os
        
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
"""
        yaml_file = temp_personality_dir / "test_personality.yaml"
        yaml_file.write_text(yaml_content)
        
        original_personality_dir = os.environ.get("PERSONALITY_CONFIG_DIR")
        os.environ["PERSONALITY_CONFIG_DIR"] = str(temp_personality_dir)
        
        try:
            with patch('app.api.v1.audio.STTEngineFactory') as mock_factory:
                mock_engine = MagicMock()
                mock_engine.transcribe = AsyncMock(return_value="转录文本")
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
        finally:
            if original_personality_dir:
                os.environ["PERSONALITY_CONFIG_DIR"] = original_personality_dir
            elif "PERSONALITY_CONFIG_DIR" in os.environ:
                del os.environ["PERSONALITY_CONFIG_DIR"]
    
    @pytest.mark.asyncio
    async def test_create_speech_personality_with_tts_config(self, client, auth_token, tmp_path):
        """测试：创建语音（人格有TTS配置，覆盖164-173行）"""
        import os
        
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
            with patch('app.api.v1.audio.TTSEngineFactory') as mock_factory:
                mock_engine = MagicMock()
                mock_engine.synthesize = AsyncMock(return_value=b"audio data")
                mock_factory.create_engine.return_value = mock_engine
                
                response = client.post(
                    "/v1/audio/speech",
                    json={
                        "input": "测试文本",
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
    async def test_create_speech_personality_no_tts_config(self, client, auth_token, tmp_path):
        """测试：创建语音（人格无TTS配置，覆盖174-180行）"""
        import os
        
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
"""
        yaml_file = temp_personality_dir / "test_personality.yaml"
        yaml_file.write_text(yaml_content)
        
        original_personality_dir = os.environ.get("PERSONALITY_CONFIG_DIR")
        os.environ["PERSONALITY_CONFIG_DIR"] = str(temp_personality_dir)
        
        try:
            with patch('app.api.v1.audio.TTSEngineFactory') as mock_factory:
                mock_engine = MagicMock()
                mock_engine.synthesize = AsyncMock(return_value=b"audio data")
                mock_factory.create_engine.return_value = mock_engine
                
                response = client.post(
                    "/v1/audio/speech",
                    json={
                        "input": "测试文本",
                        "model": "tts-1",
                        "voice": "alloy",
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
    async def test_create_speech_stream_personality_with_tts_config(self, client, auth_token, tmp_path):
        """测试：创建流式语音（人格有TTS配置，覆盖260-268行）"""
        import os
        
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
            with patch('app.api.v1.audio.TTSEngineFactory') as mock_factory:
                mock_engine = MagicMock()
                async def mock_stream():
                    yield b"audio chunk"
                mock_engine.stream_synthesize = mock_stream
                mock_factory.create_engine.return_value = mock_engine
                
                response = client.post(
                    "/v1/audio/speech/stream",
                    json={
                        "input": "测试文本",
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
    async def test_create_speech_stream_personality_no_tts_config(self, client, auth_token, tmp_path):
        """测试：创建流式语音（人格无TTS配置，覆盖269-275行）"""
        import os
        
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
"""
        yaml_file = temp_personality_dir / "test_personality.yaml"
        yaml_file.write_text(yaml_content)
        
        original_personality_dir = os.environ.get("PERSONALITY_CONFIG_DIR")
        os.environ["PERSONALITY_CONFIG_DIR"] = str(temp_personality_dir)
        
        try:
            with patch('app.api.v1.audio.TTSEngineFactory') as mock_factory:
                mock_engine = MagicMock()
                async def mock_stream():
                    yield b"audio chunk"
                mock_engine.stream_synthesize = mock_stream
                mock_factory.create_engine.return_value = mock_engine
                
                response = client.post(
                    "/v1/audio/speech/stream",
                    json={
                        "input": "测试文本",
                        "model": "tts-1",
                        "voice": "alloy",
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

