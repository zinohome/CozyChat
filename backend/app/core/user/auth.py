"""
认证服务

提供用户认证、JWT生成和验证等功能
"""

# 标准库
from datetime import timedelta
from typing import Any, Dict, Optional

# 第三方库
from sqlalchemy.orm import Session
from sqlalchemy import or_

# 本地库
from app.models.user import User
from app.utils.logger import logger
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token
)


class AuthService:
    """认证服务
    
    提供用户认证、JWT生成和验证等功能
    """
    
    def __init__(self):
        """初始化认证服务"""
        logger.debug("AuthService initialized")
    
    def hash_password(self, password: str) -> str:
        """哈希密码
        
        Args:
            password: 明文密码
            
        Returns:
            str: 哈希后的密码
        """
        return hash_password(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希后的密码
            
        Returns:
            bool: 密码是否正确
        """
        return verify_password(plain_password, hashed_password)
    
    def create_access_token(
        self,
        user_id: str,
        username: str,
        role: str = "user",
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌
        
        Args:
            user_id: 用户ID
            username: 用户名
            role: 用户角色
            expires_delta: 过期时间差（可选）
            
        Returns:
            str: JWT访问令牌
        """
        data = {
            "sub": str(user_id),
            "username": username,
            "role": role,
            "type": "access"
        }
        return create_access_token(data, expires_delta)
    
    def create_refresh_token(
        self,
        user_id: str,
        username: str
    ) -> str:
        """创建刷新令牌
        
        Args:
            user_id: 用户ID
            username: 用户名
            
        Returns:
            str: JWT刷新令牌
        """
        data = {
            "sub": str(user_id),
            "username": username,
            "type": "refresh"  # 添加type字段，用于API验证
        }
        return create_refresh_token(data)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[Dict[str, Any]]: 解码后的数据，如果验证失败返回None
        """
        return verify_token(token)
    
    def authenticate_user(
        self,
        db: Session,
        username: str,
        password: str
    ) -> Optional[User]:
        """认证用户
        
        Args:
            db: 数据库会话
            username: 用户名或邮箱
            password: 明文密码
            
        Returns:
            Optional[User]: 用户对象，如果认证失败返回None
        """
        try:
            # 查找用户（支持用户名或邮箱登录）
            user = db.query(User).filter(
                or_(
                    User.username == username,
                    User.email == username
                )
            ).first()
            
            if not user:
                logger.warning(f"User not found: {username}")
                return None
            
            # 检查用户状态
            if user.status != "active":
                logger.warning(f"User is not active: {username}, status: {user.status}")
                return None
            
            # 验证密码
            if not self.verify_password(password, user.password_hash):
                logger.warning(f"Invalid password for user: {username}")
                return None
            
            logger.info(f"User authenticated: {username}")
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {e}", exc_info=True)
            return None
    
    def get_current_user_from_token(
        self,
        db: Session,
        token: str
    ) -> Optional[User]:
        """从令牌获取当前用户
        
        Args:
            db: 数据库会话
            token: JWT令牌
            
        Returns:
            Optional[User]: 用户对象，如果验证失败返回None
        """
        try:
            payload = self.verify_token(token)
            if not payload:
                return None
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            # 查询用户
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user or user.status != "active":
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Failed to get user from token: {e}", exc_info=True)
            return None

