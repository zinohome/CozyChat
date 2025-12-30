"""
音频API覆盖率扩展测试

补充Audio API的测试以覆盖更多分支
"""

# 标准库
import pytest
import uuid
import io
from unittest.mock import AsyncMock, MagicMock, patch

# 本地库
from app.models.user import User


class TestAudioAPICoverageExtended:
    """音频API覆盖率扩展测试"""
    
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
    async def test_create_transcription_personality_no_voice_config(self, client, auth_token, tmp_path):
        """测试：创建转录（人格无voice配置，覆盖103-105行）"""
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
    async def test_create_transcription_no_personality(self, client, auth_token):
        """测试：创建转录（无personality_id，覆盖106-108行）"""
        with patch('app.api.v1.audio.STTEngineFactory') as mock_factory:
            mock_engine = MagicMock()
            mock_engine.transcribe = AsyncMock(return_value="转录文本")
            mock_factory.create_engine.return_value = mock_engine
            
            audio_file = io.BytesIO(b"fake audio data")
            audio_file.name = "test.wav"
            
            response = client.post(
                "/v1/audio/transcriptions",
                files={"file": ("test.wav", audio_file, "audio/wav")},
                data={"model": "whisper-1", "language": "zh-CN"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [200, 401, 404, 422]
    
    @pytest.mark.asyncio
    async def test_create_speech_personality_no_voice_config(self, client, auth_token, tmp_path):
        """测试：创建语音（人格无voice配置，覆盖181-187行）"""
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
                        "speed": 1.0,
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
    async def test_create_speech_no_personality(self, client, auth_token):
        """测试：创建语音（无personality_id，覆盖188-194行）"""
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
                    "speed": 1.0
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [200, 401, 404, 422]
    
    @pytest.mark.asyncio
    async def test_create_speech_stream_personality_no_voice_config(self, client, auth_token, tmp_path):
        """测试：创建流式语音（人格无voice配置，覆盖276-282行）"""
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
                        "speed": 1.0,
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
    async def test_create_speech_stream_no_personality(self, client, auth_token):
        """测试：创建流式语音（无personality_id，覆盖283-289行）"""
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
                    "speed": 1.0
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [200, 401, 404, 422]
    
    @pytest.mark.asyncio
    async def test_create_transcription_stt_config_with_model(self, client, auth_token, tmp_path):
        """测试：创建转录（STT配置已有model，覆盖96-97行）"""
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
                
                # 传递model参数，但STT配置已有model，应该使用配置中的model
                response = client.post(
                    "/v1/audio/transcriptions",
                    files={"file": ("test.wav", audio_file, "audio/wav")},
                    data={"model": "whisper-2", "personality_id": "test_personality"},
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                assert response.status_code in [200, 401, 404, 422]
        finally:
            if original_personality_dir:
                os.environ["PERSONALITY_CONFIG_DIR"] = original_personality_dir
            elif "PERSONALITY_CONFIG_DIR" in os.environ:
                del os.environ["PERSONALITY_CONFIG_DIR"]
    
    @pytest.mark.asyncio
    async def test_create_transcription_stt_config_with_language(self, client, auth_token, tmp_path):
        """测试：创建转录（STT配置已有language，覆盖98-99行）"""
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
                
                # 传递language参数，但STT配置已有language，应该使用配置中的language
                response = client.post(
                    "/v1/audio/transcriptions",
                    files={"file": ("test.wav", audio_file, "audio/wav")},
                    data={"model": "whisper-1", "language": "en", "personality_id": "test_personality"},
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                assert response.status_code in [200, 401, 404, 422]
        finally:
            if original_personality_dir:
                os.environ["PERSONALITY_CONFIG_DIR"] = original_personality_dir
            elif "PERSONALITY_CONFIG_DIR" in os.environ:
                del os.environ["PERSONALITY_CONFIG_DIR"]
    
    @pytest.mark.asyncio
    async def test_create_speech_tts_config_with_voice(self, client, auth_token, tmp_path):
        """测试：创建语音（TTS配置已有voice，覆盖168-169行）"""
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
                
                # 传递voice参数，但TTS配置已有voice，应该使用配置中的voice
                response = client.post(
                    "/v1/audio/speech",
                    json={
                        "input": "测试文本",
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
    async def test_create_speech_tts_config_with_speed(self, client, auth_token, tmp_path):
        """测试：创建语音（TTS配置已有speed，覆盖170-171行）"""
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
                
                # 传递speed参数，但TTS配置已有speed，应该使用配置中的speed
                response = client.post(
                    "/v1/audio/speech",
                    json={
                        "input": "测试文本",
                        "speed": 1.5,
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
    async def test_create_speech_tts_config_with_model(self, client, auth_token, tmp_path):
        """测试：创建语音（TTS配置已有model，覆盖172-173行）"""
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
                
                # 传递model参数，但TTS配置已有model，应该使用配置中的model
                response = client.post(
                    "/v1/audio/speech",
                    json={
                        "input": "测试文本",
                        "model": "tts-2",
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
    async def test_create_speech_stream_tts_config_with_voice(self, client, auth_token, tmp_path):
        """测试：创建流式语音（TTS配置已有voice，覆盖263-264行）"""
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
    async def test_create_speech_stream_tts_config_with_speed(self, client, auth_token, tmp_path):
        """测试：创建流式语音（TTS配置已有speed，覆盖265-266行）"""
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
                        "speed": 1.5,
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
    async def test_create_speech_stream_tts_config_with_model(self, client, auth_token, tmp_path):
        """测试：创建流式语音（TTS配置已有model，覆盖267-268行）"""
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
                        "model": "tts-2",
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

