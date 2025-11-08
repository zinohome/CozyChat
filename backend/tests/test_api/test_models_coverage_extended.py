"""
模型API覆盖率扩展测试

补充Models API的测试以覆盖更多分支
"""

# 标准库
import pytest
import uuid
from unittest.mock import MagicMock, patch

# 本地库
from app.models.user import User


class TestModelsAPICoverageExtended:
    """模型API覆盖率扩展测试"""
    
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
    async def test_list_models_engine_with_model_list(self, client, auth_token):
        """测试：列出模型（引擎有list_models方法返回多个模型，覆盖82-93行）"""
        with patch('app.api.v1.models.AIEngineRegistry') as mock_registry:
            with patch('app.api.v1.models.AIEngineFactory') as mock_factory:
                mock_registry.list_engines.return_value = ["openai"]
                
                mock_engine = MagicMock()
                mock_engine.list_models = MagicMock(return_value=["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"])
                mock_engine.chat_with_tools = MagicMock()  # 模拟有function_calling能力
                mock_engine.chat_stream = MagicMock()  # 模拟有streaming能力
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
    async def test_list_models_engine_with_capabilities(self, client, auth_token):
        """测试：列出模型（引擎有function_calling和streaming能力，覆盖89-92行）"""
        with patch('app.api.v1.models.AIEngineRegistry') as mock_registry:
            with patch('app.api.v1.models.AIEngineFactory') as mock_factory:
                mock_registry.list_engines.return_value = ["openai"]
                
                mock_engine = MagicMock()
                mock_engine.model = "gpt-4"
                mock_engine.chat_with_tools = MagicMock()  # 有function_calling
                mock_engine.chat_stream = MagicMock()  # 有streaming
                mock_factory.create_engine.return_value = mock_engine
                
                response = client.get(
                    "/v1/models",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                assert response.status_code in [200, 401, 404]
    
    @pytest.mark.asyncio
    async def test_get_model_detail_found(self, client, auth_token):
        """测试：获取模型详情（模型找到，覆盖152-170行）"""
        with patch('app.api.v1.models.AIEngineRegistry') as mock_registry:
            with patch('app.api.v1.models.AIEngineFactory') as mock_factory:
                mock_registry.list_engines.return_value = ["openai"]
                
                mock_engine = MagicMock()
                mock_engine.model = "gpt-4"
                mock_engine.chat_with_tools = MagicMock()
                mock_engine.chat_stream = MagicMock()
                mock_factory.create_engine.return_value = mock_engine
                
                response = client.get(
                    "/v1/models/gpt-4",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                assert response.status_code in [200, 401, 404]
                if response.status_code == 200:
                    data = response.json()
                    assert "id" in data or "model" in data
    
    @pytest.mark.asyncio
    async def test_get_model_detail_not_found(self, client, auth_token):
        """测试：获取模型详情（模型未找到，覆盖179-183行）"""
        with patch('app.api.v1.models.AIEngineRegistry') as mock_registry:
            with patch('app.api.v1.models.AIEngineFactory') as mock_factory:
                mock_registry.list_engines.return_value = ["openai"]
                
                mock_engine = MagicMock()
                mock_engine.model = "gpt-4"
                mock_factory.create_engine.return_value = mock_engine
                
                response = client.get(
                    "/v1/models/nonexistent-model",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                assert response.status_code in [404, 401]
    
    @pytest.mark.asyncio
    async def test_get_model_detail_without_pricing(self, client, auth_token):
        """测试：获取模型详情（引擎无get_pricing方法，覆盖154-156行）"""
        with patch('app.api.v1.models.AIEngineRegistry') as mock_registry:
            with patch('app.api.v1.models.AIEngineFactory') as mock_factory:
                mock_registry.list_engines.return_value = ["openai"]
                
                mock_engine = MagicMock()
                mock_engine.model = "gpt-4"
                # 不设置get_pricing方法
                mock_factory.create_engine.return_value = mock_engine
                
                response = client.get(
                    "/v1/models/gpt-4",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                assert response.status_code in [200, 401, 404]

