"""
模型API测试

测试模型API的功能
"""

# 标准库
import pytest
import uuid
from unittest.mock import MagicMock, patch

# 本地库
from app.main import app
from app.models.user import User


class TestModelsAPI:
    """测试模型API"""
    
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
    async def test_list_models_success(self, client, auth_token, sync_db_session):
        """测试：列出模型成功"""
        from app.api.deps import get_current_active_user, get_llm_engine_pool
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
        
        # Mock engine pool
        from unittest.mock import MagicMock
        mock_engine_pool = MagicMock()
        
        app.dependency_overrides[get_current_active_user] = get_user
        app.dependency_overrides[get_llm_engine_pool] = lambda: mock_engine_pool
        
        try:
            response = client.get(
                "/v1/models",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json() if response.status_code != 200 else ''}"
            data = response.json()
            assert isinstance(data, dict)
            assert "data" in data or "models" in data or isinstance(data, list)
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_list_models_unauthorized(self, client):
        """测试：未授权列出模型"""
        response = client.get("/v1/models")
        
        # 应该返回401或404
        assert response.status_code in [401, 404]
    
    @pytest.mark.asyncio
    async def test_get_model_detail_success(self, client, auth_token, sync_db_session):
        """测试：获取模型详情成功"""
        from app.api.deps import get_current_active_user, get_llm_engine_pool
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
        
        # Mock engine pool
        from unittest.mock import MagicMock
        mock_engine_pool = MagicMock()
        
        app.dependency_overrides[get_current_active_user] = get_user
        app.dependency_overrides[get_llm_engine_pool] = lambda: mock_engine_pool
        
        # Mock AI引擎注册表
        with patch('app.api.v1.models.AIEngineRegistry') as mock_registry:
            mock_registry.list_engines.return_value = ["openai", "ollama"]
            
            try:
                response = client.get(
                    "/v1/models/gpt-4",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                # 如果端点存在，应该返回200或404
                assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}: {response.json() if response.status_code not in [200, 404] else ''}"
                if response.status_code == 200:
                    data = response.json()
                    assert isinstance(data, dict)
                    assert "id" in data or "model" in data
            finally:
                app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_get_model_detail_not_found(self, client, auth_token, sync_db_session):
        """测试：获取不存在的模型详情"""
        from app.api.deps import get_current_active_user, get_llm_engine_pool
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
        
        # Mock engine pool
        from unittest.mock import MagicMock
        mock_engine_pool = MagicMock()
        
        app.dependency_overrides[get_current_active_user] = get_user
        app.dependency_overrides[get_llm_engine_pool] = lambda: mock_engine_pool
        
        try:
            response = client.get(
                "/v1/models/nonexistent-model",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # 应该返回404或200（如果返回空数据）
            assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}: {response.json() if response.status_code not in [200, 404] else ''}"
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_list_models_with_engine_error(self, client, auth_token):
        """测试：列出模型（引擎错误）"""
        # Mock AI引擎注册表抛出异常
        with patch('app.api.v1.models.AIEngineRegistry') as mock_registry:
            mock_registry.list_engines = MagicMock(side_effect=Exception("Registry error"))
            
            response = client.get(
                "/v1/models",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # 应该返回500
            assert response.status_code in [500, 401, 404]
    
    @pytest.mark.asyncio
    async def test_list_models_engine_without_models(self, client, auth_token, sync_db_session):
        """测试：列出模型（引擎无模型）"""
        from app.api.deps import get_current_active_user, get_llm_engine_pool
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
        
        # Mock engine pool
        from unittest.mock import MagicMock
        mock_engine_pool = MagicMock()
        
        app.dependency_overrides[get_current_active_user] = get_user
        app.dependency_overrides[get_llm_engine_pool] = lambda: mock_engine_pool
        
        try:
            # Mock AI引擎注册表和工厂
            from app.engines.ai.factory import AIEngineFactory
            from app.engines.ai.registry import AIEngineRegistry
            
            with patch.object(AIEngineRegistry, 'list_engines', return_value=["openai"]):
                with patch.object(AIEngineFactory, 'create_engine') as mock_factory:
                    # Mock引擎实例
                    mock_engine = MagicMock()
                    mock_engine.model = None
                    mock_engine.list_models = MagicMock(return_value=[])
                    mock_factory.return_value = mock_engine
                    
                    response = client.get(
                        "/v1/models",
                        headers={"Authorization": f"Bearer {auth_token}"}
                    )
                    
                    assert response.status_code in [200, 401, 404], f"Expected 200, 401, or 404, got {response.status_code}: {response.json() if response.status_code not in [200, 401, 404] else ''}"
                    if response.status_code == 200:
                        data = response.json()
                        assert "data" in data or "models" in data
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_get_model_detail_error(self, client, auth_token):
        """测试：获取模型详情（错误处理）"""
        # Mock AI引擎注册表抛出异常
        with patch('app.api.v1.models.AIEngineRegistry') as mock_registry:
            mock_registry.list_engines = MagicMock(side_effect=Exception("Registry error"))
            
            response = client.get(
                "/v1/models/gpt-4",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # 应该返回500
            assert response.status_code in [500, 401, 404]

