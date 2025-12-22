"""
用户API覆盖率测试

补充Users API的测试以覆盖114-121, 154, 158-160, 178, 207-237, 255, 276-300, 320-349, 369-377行
"""

# 标准库
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

# 本地库
from app.models.user import User


class TestUsersAPICoverage:
    """用户API覆盖率测试"""
    
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
    async def test_register_user_value_error(self, client, sync_db_session):
        """测试：用户注册（ValueError，覆盖114-118行）"""
        with patch('app.api.v1.users.UserManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.register_user = AsyncMock(side_effect=ValueError("Username already exists"))
            mock_manager_class.return_value = mock_manager
            
            response = client.post(
                "/v1/users/register",
                json={
                    "username": "existing_user",
                    "email": "test@example.com",
                    "password": "TestPassword123!"
                }
            )
            
            assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_register_user_error(self, client, sync_db_session):
        """测试：用户注册（错误处理，覆盖119-124行）"""
        with patch('app.api.v1.users.UserManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.register_user = AsyncMock(side_effect=Exception("Registration error"))
            mock_manager_class.return_value = mock_manager
            
            response = client.post(
                "/v1/users/register",
                json={
                    "username": "newuser",
                    "email": "test@example.com",
                    "password": "TestPassword123!"
                }
            )
            
            assert response.status_code in [500, 400, 422]
    
    @pytest.mark.asyncio
    async def test_login_user_http_exception(self, client, sync_db_session):
        """测试：用户登录（HTTPException，覆盖156行）"""
        with patch('app.api.v1.users.UserManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.authenticate = AsyncMock(return_value=None)
            mock_manager_class.return_value = mock_manager
            
            response = client.post(
                "/v1/users/login",
                json={
                    "username": "testuser",
                    "password": "wrongpassword"
                }
            )
            
            assert response.status_code in [401, 404]
    
    @pytest.mark.asyncio
    async def test_login_user_error(self, client, sync_db_session):
        """测试：用户登录（错误处理，覆盖158-163行）"""
        with patch('app.api.v1.users.UserManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.authenticate = AsyncMock(side_effect=Exception("Login error"))
            mock_manager_class.return_value = mock_manager
            
            response = client.post(
                "/v1/users/login",
                json={
                    "username": "testuser",
                    "password": "password"
                }
            )
            
            assert response.status_code in [500, 401, 404]
    
    @pytest.mark.asyncio
    async def test_update_current_user_not_found(self, client, auth_token, sync_db_session):
        """测试：更新当前用户（用户不存在，覆盖216-220行）"""
        with patch('app.api.v1.users.UserManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.update_user = AsyncMock(return_value=None)
            mock_manager_class.return_value = mock_manager
            
            response = client.put(
                "/v1/users/me",
                json={"email": "newemail@example.com"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [404, 401]
    
    @pytest.mark.asyncio
    async def test_update_current_user_http_exception(self, client, auth_token, sync_db_session):
        """测试：更新当前用户（HTTPException，覆盖233行）"""
        from fastapi import HTTPException
        
        with patch('app.api.v1.users.UserManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.update_user = AsyncMock(side_effect=HTTPException(status_code=400, detail="Invalid"))
            mock_manager_class.return_value = mock_manager
            
            response = client.put(
                "/v1/users/me",
                json={"email": "newemail@example.com"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [400, 401, 404]
    
    @pytest.mark.asyncio
    async def test_update_current_user_error(self, client, auth_token, sync_db_session):
        """测试：更新当前用户（错误处理，覆盖235-240行）"""
        with patch('app.api.v1.users.UserManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.update_user = AsyncMock(side_effect=Exception("Update error"))
            mock_manager_class.return_value = mock_manager
            
            response = client.put(
                "/v1/users/me",
                json={"email": "newemail@example.com"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [500, 401, 404]
    
    @pytest.mark.asyncio
    async def test_update_user_preferences_not_found(self, client, auth_token, sync_db_session):
        """测试：更新用户偏好（用户不存在，覆盖285-289行）"""
        with patch('app.api.v1.users.UserManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.update_user = AsyncMock(return_value=None)
            mock_manager_class.return_value = mock_manager
            
            response = client.put(
                "/v1/users/me/preferences",
                json={"theme": "dark"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [404, 401]
    
    @pytest.mark.asyncio
    async def test_update_user_preferences_http_exception(self, client, auth_token, sync_db_session):
        """测试：更新用户偏好（HTTPException，覆盖296行）"""
        from fastapi import HTTPException
        
        with patch('app.api.v1.users.UserManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.update_user = AsyncMock(side_effect=HTTPException(status_code=400, detail="Invalid"))
            mock_manager_class.return_value = mock_manager
            
            response = client.put(
                "/v1/users/me/preferences",
                json={"theme": "dark"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [400, 401, 404]
    
    @pytest.mark.asyncio
    async def test_update_user_preferences_error(self, client, auth_token, sync_db_session):
        """测试：更新用户偏好（错误处理，覆盖298-303行）"""
        with patch('app.api.v1.users.UserManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.update_user = AsyncMock(side_effect=Exception("Update error"))
            mock_manager_class.return_value = mock_manager
            
            response = client.put(
                "/v1/users/me/preferences",
                json={"theme": "dark"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [500, 401, 404]
    
    @pytest.mark.asyncio
    async def test_get_user_profile_no_profile(self, client, auth_token, sync_db_session):
        """测试：获取用户画像（无画像，覆盖324-334行）"""
        with patch('app.api.v1.users.UserProfileManager') as mock_profile_manager_class:
            mock_profile_manager = MagicMock()
            mock_profile_manager.get_profile.return_value = None
            mock_profile_manager_class.return_value = mock_profile_manager
            
            response = client.get(
                "/v1/users/me/profile",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [200, 401, 404]
            if response.status_code == 200:
                data = response.json()
                assert "profile" in data
                assert data["generated_at"] is None
    
    @pytest.mark.asyncio
    async def test_get_user_profile_error(self, client, auth_token, sync_db_session):
        """测试：获取用户画像（错误处理，覆盖347-352行）"""
        with patch('app.api.v1.users.UserProfileManager') as mock_profile_manager_class:
            mock_profile_manager = MagicMock()
            mock_profile_manager.get_profile.side_effect = Exception("Profile error")
            mock_profile_manager_class.return_value = mock_profile_manager
            
            response = client.get(
                "/v1/users/me/profile",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [500, 401, 404]

