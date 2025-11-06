"""
用户系统模块

提供用户管理、认证、权限等功能
"""

from .auth import AuthService
from .manager import UserManager
from .permissions import PermissionChecker, Role
from .profile import UserProfileManager
from .stats import UserStatsManager

__all__ = [
    "AuthService",
    "UserManager",
    "PermissionChecker",
    "Role",
    "UserProfileManager",
    "UserStatsManager",
]

