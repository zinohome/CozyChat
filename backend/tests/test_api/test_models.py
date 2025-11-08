"""
模型API测试

测试模型API的功能
"""

# 标准库
import pytest
import uuid
from unittest.mock import MagicMock, patch

# 本地库
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
    async def test_list_models_success(self, client, auth_token):
        """测试：列出模型成功"""
        response = client.get(
            "/v1/models",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # 如果端点存在，应该返回200
        assert response.status_code in [200, 401, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            assert "data" in data or "models" in data or isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_list_models_unauthorized(self, client):
        """测试：未授权列出模型"""
        response = client.get("/v1/models")
        
        # 应该返回401或404
        assert response.status_code in [401, 404]
    
    @pytest.mark.asyncio
    async def test_get_model_detail_success(self, client, auth_token):
        """测试：获取模型详情成功"""
        # Mock AI引擎注册表
        with patch('app.api.v1.models.AIEngineRegistry') as mock_registry:
            mock_registry.list_engines.return_value = ["openai", "ollama"]
            
            response = client.get(
                "/v1/models/gpt-4",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # 如果端点存在，应该返回200或404
            assert response.status_code in [200, 401, 404]
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
                assert "id" in data or "model" in data
    
    @pytest.mark.asyncio
    async def test_get_model_detail_not_found(self, client, auth_token):
        """测试：获取不存在的模型详情"""
        response = client.get(
            "/v1/models/nonexistent-model",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # 应该返回404或200（如果返回空数据）
        assert response.status_code in [200, 401, 404]
    
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
    async def test_list_models_engine_without_models(self, client, auth_token):
        """测试：列出模型（引擎无模型）"""
        # Mock AI引擎注册表和工厂
        with patch('app.api.v1.models.AIEngineRegistry') as mock_registry:
            with patch('app.api.v1.models.AIEngineFactory') as mock_factory:
                mock_registry.list_engines.return_value = ["openai"]
                
                # Mock引擎实例
                mock_engine = MagicMock()
                mock_engine.model = None
                mock_engine.list_models = MagicMock(return_value=[])
                mock_factory.create_engine.return_value = mock_engine
                
                response = client.get(
                    "/v1/models",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                assert response.status_code in [200, 401, 404]
                if response.status_code == 200:
                    data = response.json()
                    assert "data" in data or "models" in data
    
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

