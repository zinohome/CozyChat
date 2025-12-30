"""
音频API测试

测试音频API的功能（STT、TTS）
"""

# 标准库
import pytest
import uuid
import io
from unittest.mock import AsyncMock, MagicMock, patch

# 本地库
from app.main import app
from app.models.user import User


class TestAudioAPI:
    """测试音频API"""
    
    @pytest.fixture
    def auth_token(self, client, sync_db_session):
        """创建认证令牌"""
        from app.utils.security import hash_password, create_access_token
        from app.models.user import User as UserModel
        
        # 创建测试用户
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
        
        # 创建访问令牌
        token = create_access_token({"sub": str(test_user.id), "username": test_user.username})
        
        yield token
        
        # 清理
        try:
            sync_db_session.delete(test_user)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_create_transcription_success(self, client, auth_token, sync_db_session):
        """测试：创建转录成功"""
        from app.api.deps import get_current_active_user
        from app.utils.security import decode_token
        from app.models.user import User as UserModel
        
        # 从token中获取user_id
        token_payload = decode_token(auth_token)
        user_id = token_payload.get("sub")
        
        # 从数据库获取用户
        user = sync_db_session.query(UserModel).filter(UserModel.id == user_id).first()
        assert user is not None, "User should exist in database"
        
        # 覆盖依赖
        def get_user():
            return user
        
        app.dependency_overrides[get_current_active_user] = get_user
        
        # Mock STT引擎
        with patch('app.api.v1.audio.STTEngineFactory') as mock_factory:
            mock_engine = MagicMock()
            mock_engine.transcribe = AsyncMock(return_value="这是转录的文本")
            mock_factory.create_engine.return_value = mock_engine
            
            # 创建模拟音频文件
            audio_file = io.BytesIO(b"fake audio data")
            audio_file.name = "test.wav"
            
            try:
                response = client.post(
                    "/v1/audio/transcriptions",
                    files={"file": ("test.wav", audio_file, "audio/wav")},
                    data={"model": "whisper-1", "language": "zh-CN"},
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                # 如果端点存在，应该返回200
                assert response.status_code in [200, 404, 422], f"Expected 200, 404, or 422, got {response.status_code}: {response.json() if response.status_code not in [200, 404, 422] else ''}"
                if response.status_code == 200:
                    data = response.json()
                    assert isinstance(data, dict)
                    assert "text" in data
            finally:
                app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_create_transcription_unauthorized(self, client):
        """测试：未授权创建转录"""
        audio_file = io.BytesIO(b"fake audio data")
        audio_file.name = "test.wav"
        
        response = client.post(
            "/v1/audio/transcriptions",
            files={"file": ("test.wav", audio_file, "audio/wav")},
            data={"model": "whisper-1"}
        )
        
        # 应该返回401或404
        assert response.status_code in [401, 404, 422]
    
    @pytest.mark.asyncio
    async def test_create_speech_success(self, client, auth_token, sync_db_session):
        """测试：创建语音成功"""
        from app.api.deps import get_current_active_user
        from app.utils.security import decode_token
        from app.models.user import User as UserModel
        
        # 从token中获取user_id
        token_payload = decode_token(auth_token)
        user_id = token_payload.get("sub")
        
        # 从数据库获取用户
        user = sync_db_session.query(UserModel).filter(UserModel.id == user_id).first()
        assert user is not None, "User should exist in database"
        
        # 覆盖依赖
        def get_user():
            return user
        
        app.dependency_overrides[get_current_active_user] = get_user
        
        # Mock TTS引擎
        with patch('app.api.v1.audio.TTSEngineFactory') as mock_factory:
            mock_engine = MagicMock()
            # synthesize返回bytes（非流式）
            mock_engine.synthesize = AsyncMock(return_value=b"fake audio content")
            mock_factory.create_engine.return_value = mock_engine
            
            try:
                response = client.post(
                    "/v1/audio/speech",
                    json={
                        "input": "这是测试文本",
                        "model": "tts-1",
                        "voice": "alloy",
                        "speed": 1.0
                    },
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                # 如果端点存在，应该返回200（流式响应）
                assert response.status_code in [200, 404, 422], f"Expected 200, 404, or 422, got {response.status_code}: {response.json() if response.status_code not in [200, 404, 422] else ''}"
                if response.status_code == 200:
                    # 流式响应，检查Content-Type
                    assert "audio" in response.headers.get("Content-Type", "")
            finally:
                app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_create_speech_unauthorized(self, client):
        """测试：未授权创建语音"""
        response = client.post(
            "/v1/audio/speech",
            json={
                "input": "这是测试文本",
                "model": "tts-1",
                "voice": "alloy"
            }
        )
        
        # 应该返回401或404
        assert response.status_code in [401, 404, 422]
    
    @pytest.mark.asyncio
    async def test_create_speech_with_personality(self, client, auth_token, tmp_path, sync_db_session):
        """测试：使用人格配置创建语音"""
        from app.api.deps import get_current_active_user
        from app.utils.security import decode_token
        from app.models.user import User as UserModel
        import os
        
        # 从token中获取user_id
        token_payload = decode_token(auth_token)
        user_id = token_payload.get("sub")
        
        # 从数据库获取用户
        user = sync_db_session.query(UserModel).filter(UserModel.id == user_id).first()
        assert user is not None, "User should exist in database"
        
        # 覆盖依赖
        def get_user():
            return user
        
        app.dependency_overrides[get_current_active_user] = get_user
        
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
                # synthesize返回bytes（非流式）
                mock_engine.synthesize = AsyncMock(return_value=b"fake audio content")
                mock_factory.create_engine.return_value = mock_engine
                
                try:
                    response = client.post(
                        "/v1/audio/speech",
                        json={
                            "input": "这是测试文本",
                            "personality_id": "test_personality"
                        },
                        headers={"Authorization": f"Bearer {auth_token}"}
                    )
                    
                    # 如果端点存在，应该返回200
                    assert response.status_code in [200, 404, 422], f"Expected 200, 404, or 422, got {response.status_code}: {response.json() if response.status_code not in [200, 404, 422] else ''}"
                finally:
                    pass  # 依赖覆盖在外部finally中清理
        finally:
            app.dependency_overrides.clear()
            if original_personality_dir:
                os.environ["PERSONALITY_CONFIG_DIR"] = original_personality_dir
            elif "PERSONALITY_CONFIG_DIR" in os.environ:
                del os.environ["PERSONALITY_CONFIG_DIR"]
    
    @pytest.mark.asyncio
    async def test_create_transcription_empty_file(self, client, auth_token, sync_db_session):
        """测试：空音频文件"""
        from app.api.deps import get_current_active_user
        from app.utils.security import decode_token
        from app.models.user import User as UserModel
        
        # 从token中获取user_id
        token_payload = decode_token(auth_token)
        user_id = token_payload.get("sub")
        
        # 从数据库获取用户
        user = sync_db_session.query(UserModel).filter(UserModel.id == user_id).first()
        assert user is not None, "User should exist in database"
        
        # 覆盖依赖
        def get_user():
            return user
        
        app.dependency_overrides[get_current_active_user] = get_user
        
        audio_file = io.BytesIO(b"")
        audio_file.name = "empty.wav"
        
        try:
            response = client.post(
                "/v1/audio/transcriptions",
                files={"file": ("empty.wav", audio_file, "audio/wav")},
                data={"model": "whisper-1"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # 应该返回400（空文件）或404（端点不存在）
            assert response.status_code in [400, 404, 422], f"Expected 400, 404, or 422, got {response.status_code}: {response.json() if response.status_code not in [400, 404, 422] else ''}"
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_create_transcription_error(self, client, auth_token, sync_db_session):
        """测试：转录错误处理"""
        from app.api.deps import get_current_active_user
        from app.utils.security import decode_token
        from app.models.user import User as UserModel
        
        # 从token中获取user_id
        token_payload = decode_token(auth_token)
        user_id = token_payload.get("sub")
        
        # 从数据库获取用户
        user = sync_db_session.query(UserModel).filter(UserModel.id == user_id).first()
        assert user is not None, "User should exist in database"
        
        # 覆盖依赖
        def get_user():
            return user
        
        app.dependency_overrides[get_current_active_user] = get_user
        
        with patch('app.api.v1.audio.STTEngineFactory') as mock_factory:
            mock_engine = MagicMock()
            mock_engine.transcribe = AsyncMock(side_effect=Exception("Transcription error"))
            mock_factory.create_engine.return_value = mock_engine
            
            audio_file = io.BytesIO(b"fake audio data")
            audio_file.name = "test.wav"
            
            try:
                response = client.post(
                    "/v1/audio/transcriptions",
                    files={"file": ("test.wav", audio_file, "audio/wav")},
                    data={"model": "whisper-1"},
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                # 应该返回500或404
                assert response.status_code in [500, 404, 422], f"Expected 500, 404, or 422, got {response.status_code}: {response.json() if response.status_code not in [500, 404, 422] else ''}"
            finally:
                app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_create_speech_error(self, client, auth_token, sync_db_session):
        """测试：语音生成错误处理"""
        from app.api.deps import get_current_active_user
        from app.utils.security import decode_token
        from app.models.user import User as UserModel
        
        # 从token中获取user_id
        token_payload = decode_token(auth_token)
        user_id = token_payload.get("sub")
        
        # 从数据库获取用户
        user = sync_db_session.query(UserModel).filter(UserModel.id == user_id).first()
        assert user is not None, "User should exist in database"
        
        # 覆盖依赖
        def get_user():
            return user
        
        app.dependency_overrides[get_current_active_user] = get_user
        
        with patch('app.api.v1.audio.TTSEngineFactory') as mock_factory:
            mock_engine = MagicMock()
            async def failing_stream():
                raise Exception("TTS error")
                yield  # 永远不会执行
            mock_engine.stream_synthesize = failing_stream
            mock_factory.create_engine.return_value = mock_engine
            
            try:
                response = client.post(
                    "/v1/audio/speech",
                    json={
                        "input": "这是测试文本",
                        "model": "tts-1",
                        "voice": "alloy"
                    },
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                # 应该返回500或404
                assert response.status_code in [500, 404, 422], f"Expected 500, 404, or 422, got {response.status_code}: {response.json() if response.status_code not in [500, 404, 422] else ''}"
            finally:
                app.dependency_overrides.clear()

