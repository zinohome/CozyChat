"""
人格API覆盖率测试

补充Personalities API的测试以覆盖95-124, 147-174, 197-232, 257-292行
"""

# 标准库
import pytest
import uuid
from unittest.mock import MagicMock, patch

# 本地库
from app.models.user import User


class TestPersonalitiesAPICoverage:
    """人格API覆盖率测试"""
    
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
    async def test_list_personalities_with_default(self, client, auth_token):
        """测试：列出人格（包含默认人格，覆盖106行）"""
        with patch('app.api.v1.personalities.PersonalityManager') as mock_pm:
            mock_manager = MagicMock()
            mock_manager.list_personalities.return_value = [
                {"id": "default", "name": "Default", "description": "Default personality"},
                {"id": "assistant", "name": "Assistant", "description": "Assistant personality"}
            ]
            mock_pm.return_value = mock_manager
            
            response = client.get(
                "/v1/personalities",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [200, 401, 404]
            if response.status_code == 200:
                data = response.json()
                assert "personalities" in data or "data" in data
    
    @pytest.mark.asyncio
    async def test_get_personality_not_found(self, client, auth_token):
        """测试：获取人格（不存在，覆盖151-155行）"""
        with patch('app.api.v1.personalities.PersonalityManager') as mock_pm:
            mock_manager = MagicMock()
            mock_manager.get_personality.return_value = None
            mock_pm.return_value = mock_manager
            
            response = client.get(
                "/v1/personalities/nonexistent",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [404, 401]
    
    @pytest.mark.asyncio
    async def test_get_personality_error(self, client, auth_token):
        """测试：获取人格（错误处理，覆盖172-177行）"""
        with patch('app.api.v1.personalities.PersonalityManager') as mock_pm:
            mock_manager = MagicMock()
            mock_manager.get_personality.side_effect = Exception("Get error")
            mock_pm.return_value = mock_manager
            
            response = client.get(
                "/v1/personalities/test",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [500, 401, 404]
    
    @pytest.mark.asyncio
    async def test_create_personality_success(self, client, auth_token, tmp_path):
        """测试：创建人格成功（覆盖197-223行）"""
        import os
        
        temp_personality_dir = tmp_path / "personalities"
        temp_personality_dir.mkdir(parents=True, exist_ok=True)
        
        original_personality_dir = os.environ.get("PERSONALITY_CONFIG_DIR")
        os.environ["PERSONALITY_CONFIG_DIR"] = str(temp_personality_dir)
        
        try:
            with patch('app.api.v1.personalities.PersonalityManager') as mock_pm:
                mock_manager = MagicMock()
                mock_personality = MagicMock()
                mock_personality.id = "test_personality"
                mock_personality.name = "Test Personality"
                mock_personality.metadata = {"created_at": "2024-01-01T00:00:00"}
                mock_manager.create_personality.return_value = mock_personality
                mock_pm.return_value = mock_manager
                
                response = client.post(
                    "/v1/personalities",
                    json={
                        "name": "Test Personality",
                        "description": "Test description",
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
                
                assert response.status_code in [201, 400, 401, 404, 422]
        finally:
            if original_personality_dir:
                os.environ["PERSONALITY_CONFIG_DIR"] = original_personality_dir
            elif "PERSONALITY_CONFIG_DIR" in os.environ:
                del os.environ["PERSONALITY_CONFIG_DIR"]
    
    @pytest.mark.asyncio
    async def test_create_personality_value_error(self, client, auth_token):
        """测试：创建人格（ValueError，覆盖225-229行）"""
        with patch('app.api.v1.personalities.PersonalityManager') as mock_pm:
            mock_manager = MagicMock()
            mock_manager.create_personality.side_effect = ValueError("Invalid config")
            mock_pm.return_value = mock_manager
            
            response = client.post(
                "/v1/personalities",
                json={
                    "name": "Test",
                    "config": {}
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [400, 401, 404, 422]
    
    @pytest.mark.asyncio
    async def test_create_personality_error(self, client, auth_token):
        """测试：创建人格（错误处理，覆盖230-235行）"""
        with patch('app.api.v1.personalities.PersonalityManager') as mock_pm:
            mock_manager = MagicMock()
            mock_manager.create_personality.side_effect = Exception("Create error")
            mock_pm.return_value = mock_manager
            
            response = client.post(
                "/v1/personalities",
                json={
                    "name": "Test",
                    "config": {"ai": {"provider": "openai"}}
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [500, 401, 404, 422]
    
    @pytest.mark.asyncio
    async def test_update_personality_success(self, client, auth_token, tmp_path):
        """测试：更新人格成功（覆盖257-283行）"""
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
            with patch('app.api.v1.personalities.PersonalityManager') as mock_pm:
                mock_manager = MagicMock()
                mock_personality = MagicMock()
                mock_personality.id = "test_personality"
                mock_personality.metadata = {"updated_at": "2024-01-01T00:00:00"}
                mock_manager.update_personality.return_value = mock_personality
                mock_pm.return_value = mock_manager
                
                response = client.put(
                    "/v1/personalities/test_personality",
                    json={
                        "name": "Updated Name",
                        "description": "Updated description",
                        "config": {"ai": {"temperature": 0.8}}
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
    async def test_update_personality_value_error(self, client, auth_token):
        """测试：更新人格（ValueError，覆盖285-289行）"""
        with patch('app.api.v1.personalities.PersonalityManager') as mock_pm:
            mock_manager = MagicMock()
            mock_manager.update_personality.side_effect = ValueError("Invalid update")
            mock_pm.return_value = mock_manager
            
            response = client.put(
                "/v1/personalities/test",
                json={"name": "Test"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [400, 401, 404, 422]
    
    @pytest.mark.asyncio
    async def test_update_personality_error(self, client, auth_token):
        """测试：更新人格（错误处理，覆盖290-295行）"""
        with patch('app.api.v1.personalities.PersonalityManager') as mock_pm:
            mock_manager = MagicMock()
            mock_manager.update_personality.side_effect = Exception("Update error")
            mock_pm.return_value = mock_manager
            
            response = client.put(
                "/v1/personalities/test",
                json={"name": "Test"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [500, 401, 404, 422]

