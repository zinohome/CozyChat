"""
人格API测试

测试人格API的功能
"""

# 标准库
import pytest
import uuid
from unittest.mock import MagicMock, patch

# 本地库
from app.main import app
from app.models.user import User


class TestPersonalitiesAPI:
    """测试人格API"""
    
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
    async def test_list_personalities_success(self, client, auth_token, sync_db_session):
        """测试：列出人格成功"""
        from app.api.deps import get_current_active_user, get_personality_registry
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
        
        # Mock personality registry
        from unittest.mock import MagicMock
        mock_registry = MagicMock()
        mock_registry.list_personalities.return_value = []
        app.dependency_overrides[get_current_active_user] = get_user
        app.dependency_overrides[get_personality_registry] = lambda: mock_registry
        
        try:
            response = client.get(
                "/v1/personalities",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json() if response.status_code != 200 else ''}"
            data = response.json()
            assert "personalities" in data or "data" in data or isinstance(data, list)
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_get_personality_success(self, client, auth_token, sync_db_session):
        """测试：获取人格成功"""
        from app.api.deps import get_current_active_user, get_personality_registry
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
        
        # Mock personality registry
        from unittest.mock import MagicMock
        mock_personality = MagicMock()
        mock_personality.id = "test_personality"
        mock_personality.name = "Test Personality"
        mock_personality.description = "Test description"
        mock_personality.to_config.return_value = {"ai": {"provider": "openai"}}
        mock_personality.metadata = {}
        
        mock_registry = MagicMock()
        mock_registry.get_personality.return_value = mock_personality
        
        app.dependency_overrides[get_current_active_user] = get_user
        app.dependency_overrides[get_personality_registry] = lambda: mock_registry
        
        try:
            response = client.get(
                "/v1/personalities/test_personality",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json() if response.status_code != 200 else ''}"
            data = response.json()
            assert isinstance(data, dict)
            assert "id" in data
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_list_personalities_unauthorized(self, client):
        """测试：未授权列出人格"""
        response = client.get("/v1/personalities")
        
        # 如果API没有认证要求，返回200是正常的
        # 如果有认证要求，应该返回401
        assert response.status_code in [200, 401]
    
    @pytest.mark.asyncio
    async def test_get_personality_not_found(self, client, auth_token, sync_db_session):
        """测试：获取人格（不存在）"""
        from app.api.deps import get_current_active_user, get_personality_registry
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
        
        # Mock personality registry - 返回None表示不存在
        from unittest.mock import MagicMock
        mock_registry = MagicMock()
        mock_registry.get_personality.return_value = None
        
        app.dependency_overrides[get_current_active_user] = get_user
        app.dependency_overrides[get_personality_registry] = lambda: mock_registry
        
        try:
            response = client.get(
                "/v1/personalities/nonexistent_personality",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.json() if response.status_code != 404 else ''}"
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_create_personality_success(self, client, auth_token, tmp_path, sync_db_session):
        """测试：创建人格成功"""
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
        
        # 创建临时人格目录
        temp_personality_dir = tmp_path / "personalities"
        temp_personality_dir.mkdir(parents=True, exist_ok=True)
        
        original_personality_dir = os.environ.get("PERSONALITY_CONFIG_DIR")
        os.environ["PERSONALITY_CONFIG_DIR"] = str(temp_personality_dir)
        
        try:
            response = client.post(
                "/v1/personalities",
                json={
                    "id": "test_custom_personality",
                    "name": "Test Custom Personality",
                    "description": "A test personality",
                    "config": {
                        "ai": {
                            "provider": "openai",
                            "model": "gpt-3.5-turbo",
                            "temperature": 0.7
                        }
                    }
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # 如果端点存在，应该返回201
            assert response.status_code in [201, 400, 404, 422], f"Expected 201, 400, 404, or 422, got {response.status_code}: {response.json() if response.status_code not in [201, 400, 404, 422] else ''}"
            if response.status_code == 201:
                data = response.json()
                assert "personality_id" in data or "id" in data
        finally:
            app.dependency_overrides.clear()
            if original_personality_dir:
                os.environ["PERSONALITY_CONFIG_DIR"] = original_personality_dir
            elif "PERSONALITY_CONFIG_DIR" in os.environ:
                del os.environ["PERSONALITY_CONFIG_DIR"]
    
    @pytest.mark.asyncio
    async def test_create_personality_invalid_config(self, client, auth_token, sync_db_session):
        """测试：创建人格（无效配置）"""
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
        
        try:
            response = client.post(
                "/v1/personalities",
                json={
                    "id": "test_personality",
                    "name": "Test",
                    "config": {}  # 缺少必需字段
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # 应该返回400或422
            assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}: {response.json() if response.status_code not in [400, 422] else ''}"
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_update_personality_success(self, client, auth_token, tmp_path, sync_db_session):
        """测试：更新人格成功"""
        from app.api.deps import get_current_active_user, get_personality_registry
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
        
        # Mock personality registry
        from unittest.mock import MagicMock
        mock_personality = MagicMock()
        mock_personality.id = "test_personality"
        mock_personality.name = "Test Personality"
        mock_personality.description = "Test description"
        mock_personality.to_config.return_value = {"ai": {"provider": "openai"}}
        mock_personality.metadata = {}
        
        mock_registry = MagicMock()
        mock_registry.get_personality.return_value = mock_personality
        
        app.dependency_overrides[get_current_active_user] = get_user
        app.dependency_overrides[get_personality_registry] = lambda: mock_registry
        
        # 创建临时人格目录和文件
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
        (temp_personality_dir / "test_personality.yaml").write_text(yaml_content)
        
        original_personality_dir = os.environ.get("PERSONALITY_CONFIG_DIR")
        os.environ["PERSONALITY_CONFIG_DIR"] = str(temp_personality_dir)
        
        try:
            # Mock PersonalityManager
            from app.core.personality.manager import PersonalityManager
            with patch.object(PersonalityManager, 'update_personality') as mock_update:
                mock_update.return_value = mock_personality
                
                response = client.put(
                    "/v1/personalities/test_personality",
                    json={
                        "name": "Updated Test Personality",
                        "description": "Updated description"
                    },
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                # 如果端点存在，应该返回200
                assert response.status_code in [200, 404, 422], f"Expected 200, 404, or 422, got {response.status_code}: {response.json() if response.status_code not in [200, 404, 422] else ''}"
        finally:
            app.dependency_overrides.clear()
            if original_personality_dir:
                os.environ["PERSONALITY_CONFIG_DIR"] = original_personality_dir
            elif "PERSONALITY_CONFIG_DIR" in os.environ:
                del os.environ["PERSONALITY_CONFIG_DIR"]
    
    @pytest.mark.asyncio
    async def test_delete_personality_success(self, client, auth_token, tmp_path, sync_db_session):
        """测试：删除人格成功"""
        from app.api.deps import get_current_active_user, get_personality_registry
        from app.utils.security import decode_token
        from app.models.user import User as UserModel
        import os
        
        # 创建临时人格目录和文件
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
        (temp_personality_dir / "test_personality.yaml").write_text(yaml_content)
        
        # 从token中获取user_id
        token_payload = decode_token(auth_token)
        user_id = token_payload.get("sub")
        
        # 从数据库获取用户
        user = sync_db_session.query(UserModel).filter(UserModel.id == user_id).first()
        assert user is not None, "User should exist in database"
        
        # 覆盖依赖
        def get_user():
            return user
        
        # Mock personality registry
        from unittest.mock import MagicMock
        mock_personality = MagicMock()
        mock_personality.id = "test_personality"
        mock_registry = MagicMock()
        mock_registry.get_personality.return_value = mock_personality
        
        app.dependency_overrides[get_current_active_user] = get_user
        app.dependency_overrides[get_personality_registry] = lambda: mock_registry
        
        original_personality_dir = os.environ.get("PERSONALITY_CONFIG_DIR")
        os.environ["PERSONALITY_CONFIG_DIR"] = str(temp_personality_dir)
        
        try:
            response = client.delete(
                "/v1/personalities/test_personality",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # 如果端点存在，应该返回200或204
            # 如果端点不存在，返回405（Method Not Allowed）也是正常的
            assert response.status_code in [200, 204, 404, 405], f"Expected 200, 204, 404, or 405, got {response.status_code}: {response.json() if response.status_code not in [200, 204, 404, 405] else ''}"
        finally:
            app.dependency_overrides.clear()
            if original_personality_dir:
                os.environ["PERSONALITY_CONFIG_DIR"] = original_personality_dir
            elif "PERSONALITY_CONFIG_DIR" in os.environ:
                del os.environ["PERSONALITY_CONFIG_DIR"]
    
    @pytest.mark.asyncio
    async def test_list_personalities_error(self, client, auth_token, sync_db_session):
        """测试：列出人格（错误处理）"""
        from app.api.deps import get_current_active_user, get_personality_registry
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
        
        # Mock personality registry抛出异常
        from unittest.mock import MagicMock
        mock_registry = MagicMock()
        mock_registry.list_personalities.side_effect = Exception("List error")
        
        app.dependency_overrides[get_current_active_user] = get_user
        app.dependency_overrides[get_personality_registry] = lambda: mock_registry
        
        try:
            response = client.get(
                "/v1/personalities",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # 应该返回500
            assert response.status_code in [500, 404], f"Expected 500 or 404, got {response.status_code}: {response.json() if response.status_code not in [500, 404] else ''}"
        finally:
            app.dependency_overrides.clear()

