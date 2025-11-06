"""
权限管理

提供RBAC权限检查和路由守卫
"""

# 标准库
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# 第三方库
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# 本地库
from app.models.user import User
from app.utils.logger import logger
from .auth import AuthService

# HTTP Bearer认证
security = HTTPBearer()


class Role(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class PermissionChecker:
    """权限检查器
    
    提供RBAC权限检查和路由守卫功能
    """
    
    def __init__(self):
        """初始化权限检查器"""
        self.auth_service = AuthService()
        
        # 角色权限映射
        self.role_permissions: Dict[str, List[str]] = {
            "admin": ["*"],  # 管理员拥有所有权限
            "user": [
                "chat:read",
                "chat:write",
                "memory:read",
                "memory:write",
                "personality:read",
                "tool:use"
            ],
            "guest": [
                "chat:read"
            ]
        }
        
        logger.debug("PermissionChecker initialized")
    
    def has_permission(self, role: str, permission: str) -> bool:
        """检查角色是否有权限
        
        Args:
            role: 用户角色
            permission: 权限名称
            
        Returns:
            bool: 是否有权限
        """
        permissions = self.role_permissions.get(role, [])
        
        # 管理员拥有所有权限
        if "*" in permissions:
            return True
        
        return permission in permissions
    
    def require_role(self, *allowed_roles: str) -> Callable:
        """要求特定角色的装饰器
        
        Args:
            *allowed_roles: 允许的角色列表
            
        Returns:
            Callable: 依赖函数
        """
        def role_checker(
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ) -> User:
            """角色检查依赖"""
            token = credentials.credentials
            user = self.get_current_user(token)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证或令牌无效"
                )
            
            if user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要以下角色之一: {', '.join(allowed_roles)}"
                )
            
            return user
        
        return role_checker
    
    def require_permission(self, permission: str) -> Callable:
        """要求特定权限的装饰器
        
        Args:
            permission: 权限名称
            
        Returns:
            Callable: 依赖函数
        """
        def permission_checker(
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ) -> User:
            """权限检查依赖"""
            token = credentials.credentials
            user = self.get_current_user(token)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证或令牌无效"
                )
            
            if not self.has_permission(user.role, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要权限: {permission}"
                )
            
            return user
        
        return permission_checker
    
    def get_current_user(
        self,
        token: str
    ) -> Optional[User]:
        """从令牌获取当前用户
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[User]: 用户对象，如果验证失败返回None
        """
        # 这里需要数据库会话，实际使用时通过依赖注入获取
        # 简化实现：返回None，实际使用时需要传入db参数
        payload = self.auth_service.verify_token(token)
        if not payload:
            return None
        
        # 注意：这里需要数据库会话，实际使用时应该通过依赖注入
        # 这里只是返回验证结果，实际用户对象需要从数据库查询
        return None


# 全局权限检查器实例
permission_checker = PermissionChecker()

# 常用依赖
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """获取当前用户（从令牌）
    
    Args:
        credentials: HTTP Bearer凭证
        
    Returns:
        Dict[str, Any]: 用户信息字典
        
    Raises:
        HTTPException: 如果认证失败
    """
    token = credentials.credentials
    payload = permission_checker.auth_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证或令牌无效",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return payload


def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """要求管理员角色
    
    Args:
        credentials: HTTP Bearer凭证
        
    Returns:
        Dict[str, Any]: 用户信息字典
        
    Raises:
        HTTPException: 如果认证失败或不是管理员
    """
    payload = get_current_user(credentials)
    
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    return payload

