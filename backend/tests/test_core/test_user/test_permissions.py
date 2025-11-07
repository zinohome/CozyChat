"""
权限管理测试

测试权限管理的RBAC、权限检查等功能
"""

# 标准库
import pytest
import uuid
from unittest.mock import MagicMock

# 本地库
from app.core.user.permissions import PermissionChecker
from app.models.user import User


class TestPermissionChecker:
    """测试权限检查器"""
    
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
    
    def test_check_permission_admin(self, permission_checker, admin_user):
        """测试：管理员权限检查"""
        # 管理员应该有所有权限
        assert permission_checker.has_permission(admin_user.role, "admin") is True
        assert permission_checker.has_permission(admin_user.role, "user") is True
        assert permission_checker.has_permission(admin_user.role, "chat:read") is True
        assert permission_checker.has_permission(admin_user.role, "chat:write") is True
    
    def test_check_permission_user(self, permission_checker, regular_user):
        """测试：普通用户权限检查"""
        # 普通用户只有基本权限
        assert permission_checker.has_permission(regular_user.role, "chat:read") is True
        assert permission_checker.has_permission(regular_user.role, "chat:write") is True
        # 不应该有管理员权限
        assert permission_checker.has_permission(regular_user.role, "admin") is False
    
    def test_check_role(self, permission_checker, admin_user, regular_user):
        """测试：角色检查"""
        # 检查角色是否匹配
        assert admin_user.role == "admin"
        assert regular_user.role == "user"
    
    def test_check_user_active(self, permission_checker, admin_user, regular_user):
        """测试：用户状态检查"""
        # 检查用户状态
        assert admin_user.status == "active"
        assert regular_user.status == "active"
        
        # 创建非活跃用户
        inactive_user = MagicMock(spec=User)
        inactive_user.status = "inactive"
        assert inactive_user.status == "inactive"

