"""
用户管理器

提供用户CRUD、认证、偏好管理等功能
"""

# 标准库
from datetime import datetime
from typing import Any, Dict, List, Optional

# 第三方库
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

# 本地库
from app.models.user import User
from app.models import UserProfile  # 从__init__导入，确保模型已初始化
from app.utils.logger import logger
from .auth import AuthService


class UserManager:
    """用户管理器
    
    统一管理用户相关功能，包括注册、认证、偏好管理等
    """
    
    def __init__(self, db: Session):
        """初始化用户管理器
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.auth_service = AuthService()
        
        logger.debug("UserManager initialized")
    
    async def register_user(
        self,
        username: str,
        email: str,
        password: str,
        **kwargs: Any
    ) -> User:
        """注册新用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 明文密码
            **kwargs: 其他参数（display_name, role等）
            
        Returns:
            User: 用户对象
            
        Raises:
            ValueError: 如果用户名或邮箱已存在
        """
        try:
            # 检查用户名或邮箱是否已存在
            existing = self.db.query(User).filter(
                or_(
                    User.username == username,
                    User.email == email
                )
            ).first()
            
            if existing:
                raise ValueError("用户名或邮箱已存在")
            
            # 哈希密码
            password_hash = self.auth_service.hash_password(password)
            
            # 创建用户
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=kwargs.get("role", "user"),
                display_name=kwargs.get("display_name", username),
                avatar_url=kwargs.get("avatar_url"),
                bio=kwargs.get("bio"),
                status="active"
            )
            
            # 设置偏好（如果提供）
            if "preferences" in kwargs:
                user.update_preferences(kwargs["preferences"])
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            # 创建用户画像
            profile = UserProfile(user_id=user.id)
            self.db.add(profile)
            self.db.commit()
            
            logger.info(
                f"User registered: {username}",
                extra={"user_id": str(user.id), "username": username, "email": email}
            )
            
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to register user: {e}", exc_info=True)
            raise
    
    async def authenticate(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """用户认证
        
        Args:
            username: 用户名或邮箱
            password: 明文密码
            ip_address: IP地址（可选）
            
        Returns:
            Optional[Dict[str, Any]]: 认证成功返回包含token的字典，失败返回None
        """
        try:
            user = self.auth_service.authenticate_user(
                self.db,
                username,
                password
            )
            
            if not user:
                return None
            
            # 更新最后登录信息
            user.update_last_login(ip_address)
            self.db.commit()
            
            # 生成token
            access_token = self.auth_service.create_access_token(
                user_id=str(user.id),
                username=user.username,
                role=user.role
            )
            
            refresh_token = self.auth_service.create_refresh_token(
                user_id=str(user.id),
                username=user.username
            )
            
            logger.info(
                f"User authenticated: {username}",
                extra={"user_id": str(user.id), "ip_address": ip_address}
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": 30 * 24 * 60 * 60,  # 30天（秒）
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "display_name": user.display_name,
                    "preferences": user.get_preferences()
                }
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {e}", exc_info=True)
            return None
    
    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[User]: 用户对象，如果不存在返回None
        """
        try:
            return self.db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Failed to get user: {e}", exc_info=True)
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            Optional[User]: 用户对象，如果不存在返回None
        """
        try:
            return self.db.query(User).filter(User.username == username).first()
        except Exception as e:
            logger.error(f"Failed to get user by username: {e}", exc_info=True)
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户
        
        Args:
            email: 邮箱地址
            
        Returns:
            Optional[User]: 用户对象，如果不存在返回None
        """
        try:
            return self.db.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}", exc_info=True)
            return None
    
    async def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[User]:
        """更新用户信息
        
        Args:
            user_id: 用户ID
            updates: 更新字典
            
        Returns:
            Optional[User]: 更新后的用户对象，如果不存在返回None
        """
        try:
            user = self.get_user(user_id)
            if not user:
                return None
            
            # 更新字段
            allowed_fields = [
                "display_name", "avatar_url", "bio", "email",
                "role", "status"
            ]
            
            for field in allowed_fields:
                if field in updates:
                    setattr(user, field, updates[field])
            
            # 更新偏好
            if "preferences" in updates:
                user.update_preferences(updates["preferences"])
            
            # 更新密码（如果提供）
            if "password" in updates:
                user.password_hash = self.auth_service.hash_password(updates["password"])
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User updated: {user_id}", extra={"user_id": user_id})
            
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user: {e}", exc_info=True)
            raise
    
    async def delete_user(self, user_id: str, soft_delete: bool = True) -> bool:
        """删除用户
        
        Args:
            user_id: 用户ID
            soft_delete: 是否软删除（默认True）
            
        Returns:
            bool: 是否删除成功
        """
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            if soft_delete:
                # 软删除
                user.status = "deleted"
                user.deleted_at = datetime.utcnow()
            else:
                # 硬删除
                self.db.delete(user)
            
            self.db.commit()
            
            logger.info(f"User deleted: {user_id}", extra={"user_id": user_id, "soft_delete": soft_delete})
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete user: {e}", exc_info=True)
            return False
    
    def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[User]:
        """列出用户
        
        Args:
            skip: 跳过数量
            limit: 返回数量
            status: 状态过滤（可选）
            
        Returns:
            List[User]: 用户列表
        """
        try:
            query = self.db.query(User)
            
            if status:
                query = query.filter(User.status == status)
            else:
                # 默认不包含已删除用户
                query = query.filter(User.status != "deleted")
            
            return query.offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}", exc_info=True)
            return []
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[UserProfile]: 用户画像对象，如果不存在返回None
        """
        try:
            return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}", exc_info=True)
            return None
    
    async def update_user_profile(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[UserProfile]:
        """更新用户画像
        
        Args:
            user_id: 用户ID
            updates: 更新字典
            
        Returns:
            Optional[UserProfile]: 更新后的用户画像对象
        """
        try:
            profile = self.get_user_profile(user_id)
            
            if not profile:
                # 创建新画像
                profile = UserProfile(user_id=user_id)
                self.db.add(profile)
            
            # 更新字段
            if "interests" in updates:
                profile.interests = updates["interests"]
            
            if "habits" in updates:
                profile.update_habits(updates["habits"])
            
            if "personality_insights" in updates:
                profile.update_personality_insights(updates["personality_insights"])
            
            if "statistics" in updates:
                profile.update_statistics(updates["statistics"])
            
            self.db.commit()
            self.db.refresh(profile)
            
            logger.info(f"User profile updated: {user_id}", extra={"user_id": user_id})
            
            return profile
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user profile: {e}", exc_info=True)
            raise
    
    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """获取用户统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        try:
            user = self.get_user(user_id)
            if not user:
                return {}
            
            profile = self.get_user_profile(user_id)
            
            return {
                "user_id": str(user.id),
                "username": user.username,
                "total_sessions": user.total_sessions,
                "total_messages": user.total_messages,
                "total_tokens_used": user.total_tokens_used,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                "created_at": user.created_at.isoformat(),
                "profile": {
                    "interests": profile.interests if profile else [],
                    "habits": profile.get_habits() if profile else {},
                    "statistics": profile.get_statistics() if profile else {}
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get user statistics: {e}", exc_info=True)
            return {}

