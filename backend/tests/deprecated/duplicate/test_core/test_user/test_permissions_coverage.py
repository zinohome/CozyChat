"""
权限管理覆盖率测试

补充user/permissions.py的未覆盖行测试
"""

# 标准库
import pytest
import uuid
from unittest.mock import MagicMock, patch

# 本地库
from app.core.user.permissions import PermissionChecker, get_current_user, require_admin
from app.models.user import User
from fastapi.security import HTTPAuthorizationCredentials


class TestPermissionsCoverage:
    """权限管理覆盖率测试"""
    
    @pytest.fixture
    def permission_checker(self):
        """创建权限检查器实例"""
        return PermissionChecker()
    
    @pytest.fixture
    def admin_user(self):
        """创建管理员用户"""
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        user.role = "admin"
        user.status = "active"
        return user
    
    @pytest.fixture
    def regular_user(self):
        """创建普通用户"""
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        user.role = "user"
        user.status = "active"
        return user
    
    @pytest.fixture
    def mock_credentials(self):
        """创建Mock凭证"""
        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = "test_token"
        return credentials
    
    def test_require_role_success(self, permission_checker, admin_user, mock_credentials):
        """测试：要求角色（成功，覆盖86-107行）"""
        # Mock get_current_user返回用户
        with patch.object(permission_checker, 'get_current_user', return_value=admin_user):
            role_checker = permission_checker.require_role("admin")
            user = role_checker(mock_credentials)
            assert user == admin_user
    
    def test_require_role_unauthorized(self, permission_checker, mock_credentials):
        """测试：要求角色（未授权，覆盖93-97行）"""
        # Mock get_current_user返回None
        with patch.object(permission_checker, 'get_current_user', return_value=None):
            role_checker = permission_checker.require_role("admin")
            with pytest.raises(Exception):  # HTTPException
                role_checker(mock_credentials)
    
    def test_require_role_forbidden(self, permission_checker, regular_user, mock_credentials):
        """测试：要求角色（禁止，覆盖99-103行）"""
        # Mock get_current_user返回普通用户
        with patch.object(permission_checker, 'get_current_user', return_value=regular_user):
            role_checker = permission_checker.require_role("admin")
            with pytest.raises(Exception):  # HTTPException
                role_checker(mock_credentials)
    
    def test_require_permission_success(self, permission_checker, regular_user, mock_credentials):
        """测试：要求权限（成功，覆盖118-139行）"""
        # Mock get_current_user返回用户
        with patch.object(permission_checker, 'get_current_user', return_value=regular_user):
            permission_checker_func = permission_checker.require_permission("chat:read")
            user = permission_checker_func(mock_credentials)
            assert user == regular_user
    
    def test_require_permission_unauthorized(self, permission_checker, mock_credentials):
        """测试：要求权限（未授权，覆盖125-129行）"""
        # Mock get_current_user返回None
        with patch.object(permission_checker, 'get_current_user', return_value=None):
            permission_checker_func = permission_checker.require_permission("chat:read")
            with pytest.raises(Exception):  # HTTPException
                permission_checker_func(mock_credentials)
    
    def test_require_permission_forbidden(self, permission_checker, regular_user, mock_credentials):
        """测试：要求权限（禁止，覆盖131-135行）"""
        # Mock get_current_user返回用户，但没有权限
        with patch.object(permission_checker, 'get_current_user', return_value=regular_user):
            permission_checker_func = permission_checker.require_permission("admin")
            with pytest.raises(Exception):  # HTTPException
                permission_checker_func(mock_credentials)
    
    def test_get_current_user_with_payload(self, permission_checker, sync_db_session):
        """测试：获取当前用户（有payload，覆盖155-161行）"""
        # Mock verify_token返回payload
        mock_payload = {"sub": str(uuid.uuid4()), "username": "testuser"}
        with patch.object(permission_checker.auth_service, 'verify_token', return_value=mock_payload):
            # 注意：get_current_user需要数据库会话，但这里简化实现返回None
            user = permission_checker.get_current_user("test_token")
            # 由于简化实现，应该返回None
            assert user is None
    
    def test_get_current_user_no_payload(self, permission_checker):
        """测试：获取当前用户（无payload，覆盖155-157行）"""
        # Mock verify_token返回None
        with patch.object(permission_checker.auth_service, 'verify_token', return_value=None):
            user = permission_checker.get_current_user("test_token")
            assert user is None
    
    def test_get_current_user_function_success(self, mock_credentials):
        """测试：get_current_user函数（成功，覆盖182-192行）"""
        from app.core.user.permissions import permission_checker
        
        # Mock verify_token返回payload
        mock_payload = {"sub": str(uuid.uuid4()), "username": "testuser"}
        with patch.object(permission_checker.auth_service, 'verify_token', return_value=mock_payload):
            payload = get_current_user(mock_credentials)
            assert payload == mock_payload
    
    def test_get_current_user_function_unauthorized(self, mock_credentials):
        """测试：get_current_user函数（未授权，覆盖185-190行）"""
        from app.core.user.permissions import permission_checker
        
        # Mock verify_token返回None
        with patch.object(permission_checker.auth_service, 'verify_token', return_value=None):
            with pytest.raises(Exception):  # HTTPException
                get_current_user(mock_credentials)
    
    def test_require_admin_success(self, mock_credentials):
        """测试：require_admin函数（成功，覆盖209-217行）"""
        from app.core.user.permissions import permission_checker
        
        # Mock get_current_user返回管理员payload
        mock_payload = {"sub": str(uuid.uuid4()), "username": "admin", "role": "admin"}
        with patch('app.core.user.permissions.get_current_user', return_value=mock_payload):
            payload = require_admin(mock_credentials)
            assert payload == mock_payload
    
    def test_require_admin_forbidden(self, mock_credentials):
        """测试：require_admin函数（禁止，覆盖211-215行）"""
        from app.core.user.permissions import permission_checker
        
        # Mock get_current_user返回普通用户payload
        mock_payload = {"sub": str(uuid.uuid4()), "username": "user", "role": "user"}
        with patch('app.core.user.permissions.get_current_user', return_value=mock_payload):
            with pytest.raises(Exception):  # HTTPException
                require_admin(mock_credentials)

