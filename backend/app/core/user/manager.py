"""
用户管理器

提供用户CRUD、认证、偏好管理等功能
"""

# 标准库
from datetime import datetime
from typing import Any, Dict, List, Optional

# 第三方库
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, func, select

# 本地库
from app.models.user import User
from app.models import UserProfile  # 从__init__导入，确保模型已初始化
from app.utils.logger import logger
from .auth import AuthService


# ============================================================================
# 旧实现：UserManagerLegacy（已移除）
# ============================================================================
# 创建时间：2024-XX-XX
# 移除时间：2025-01-XX
# 状态：✅ 已移除（新实现已验证通过）
# 替代：UserManager (使用异步会话)
# 说明：Legacy类已在阶段三清理中移除，代码约400行
# 如需查看历史实现，请查看git历史记录
# ============================================================================


# ============================================================================
# 新实现：UserManager
# ============================================================================
# 创建时间：2025-01-XX
# 状态：✅ 新实现，使用异步会话
# 替代：UserManagerLegacy（已在 v2.0 移除）
# ============================================================================
class UserManager:
    """用户管理器（异步版本）
    
    统一管理用户相关功能，包括注册、认证、偏好管理等
    使用异步数据库会话
    """
    
    def __init__(self, db: AsyncSession):
        """初始化用户管理器
        
        Args:
            db: 数据库会话（异步）
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
            # 检查用户名或邮箱是否已存在（异步）
            stmt = select(User).where(
                or_(
                    User.username == username,
                    User.email == email
                )
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            
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
            await self.db.commit()
            await self.db.refresh(user)
            
            # 创建用户画像
            profile = UserProfile(user_id=user.id)
            self.db.add(profile)
            await self.db.commit()
            
            logger.info(
                f"User registered: {username}",
                extra={"user_id": str(user.id), "username": username, "email": email}
            )
            
            return user
            
        except Exception as e:
            await self.db.rollback()
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
            # 使用AuthService的同步方法，但传入异步会话需要适配
            # 暂时使用同步查询，因为AuthService使用同步会话
            # TODO: 创建异步版本的AuthService
            from app.core.user.auth import AuthService
            auth_service = AuthService()
            
            # 查询用户（异步）
            stmt = select(User).where(
                or_(
                    User.username == username,
                    User.email == username
                )
            )
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # 检查用户状态
            if str(user.status) != "active":  # type: ignore[arg-type]
                return None
            
            # 验证密码
            if not auth_service.verify_password(password, user.password_hash):  # type: ignore[arg-type]
                return None
            
            # 更新最后登录信息
            user.update_last_login(ip_address)
            await self.db.commit()
            
            # 生成token
            access_token = self.auth_service.create_access_token(
                user_id=str(user.id),
                username=str(user.username),  # type: ignore[arg-type]
                role=str(user.role)  # type: ignore[arg-type]
            )
            
            refresh_token = self.auth_service.create_refresh_token(
                user_id=str(user.id),
                username=str(user.username)  # type: ignore[arg-type]
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
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """获取用户（异步版本）
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[User]: 用户对象，如果不存在返回None
        """
        try:
            stmt = select(User).where(User.id == user_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user: {e}", exc_info=True)
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户（异步版本）
        
        Args:
            username: 用户名
            
        Returns:
            Optional[User]: 用户对象，如果不存在返回None
        """
        try:
            stmt = select(User).where(User.username == username)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by username: {e}", exc_info=True)
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户（异步版本）
        
        Args:
            email: 邮箱地址
            
        Returns:
            Optional[User]: 用户对象，如果不存在返回None
        """
        try:
            stmt = select(User).where(User.email == email)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}", exc_info=True)
            return None
    
    async def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[User]:
        """更新用户信息（异步版本）
        
        Args:
            user_id: 用户ID
            updates: 更新字典
            
        Returns:
            Optional[User]: 更新后的用户对象，如果不存在返回None
        """
        try:
            user = await self.get_user(user_id)
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
                logger.info(f"Updating preferences: user_id={user_id}, updates={updates['preferences']}")
                user.update_preferences(updates["preferences"])
                logger.info(f"Preferences after update: {user.get_preferences()}")
            
            # 更新密码（如果提供）
            if "password" in updates:
                user.password_hash = self.auth_service.hash_password(updates["password"])  # type: ignore[assignment]
            
            await self.db.commit()
            await self.db.refresh(user)
            
            # 验证更新后的偏好
            final_preferences = user.get_preferences()
            logger.info(f"Final preferences after commit and refresh: user_id={user_id}, preferences={final_preferences}")
            
            logger.info(f"User updated: {user_id}", extra={"user_id": user_id})
            
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update user: {e}", exc_info=True)
            raise
    
    async def delete_user(self, user_id: str, soft_delete: bool = True) -> bool:
        """删除用户（异步版本）
        
        Args:
            user_id: 用户ID
            soft_delete: 是否软删除（默认True）
            
        Returns:
            bool: 是否删除成功
        """
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            if soft_delete:
                # 软删除
                user.status = "deleted"  # type: ignore[assignment]
                user.deleted_at = datetime.utcnow()  # type: ignore[assignment]
            else:
                # 硬删除
                await self.db.delete(user)
            
            await self.db.commit()
            
            logger.info(f"User deleted: {user_id}", extra={"user_id": user_id, "soft_delete": soft_delete})
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete user: {e}", exc_info=True)
            return False
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[User]:
        """列出用户（异步版本）
        
        Args:
            skip: 跳过数量
            limit: 返回数量
            status: 状态过滤（可选）
            
        Returns:
            List[User]: 用户列表
        """
        try:
            stmt = select(User)
            
            if status:
                stmt = stmt.where(User.status == status)
            else:
                # 默认不包含已删除用户
                stmt = stmt.where(User.status != "deleted")
            
            stmt = stmt.offset(skip).limit(limit)
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}", exc_info=True)
            return []
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户画像（异步版本）
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[UserProfile]: 用户画像对象，如果不存在返回None
        """
        try:
            stmt = select(UserProfile).where(UserProfile.user_id == user_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}", exc_info=True)
            return None
    
    async def update_user_profile(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[UserProfile]:
        """更新用户画像（异步版本）
        
        Args:
            user_id: 用户ID
            updates: 更新字典
            
        Returns:
            Optional[UserProfile]: 更新后的用户画像对象
        """
        try:
            profile = await self.get_user_profile(user_id)
            
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
            
            await self.db.commit()
            await self.db.refresh(profile)
            
            logger.info(f"User profile updated: {user_id}", extra={"user_id": user_id})
            
            return profile
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update user profile: {e}", exc_info=True)
            raise
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """获取用户统计信息（异步版本）
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        try:
            user = await self.get_user(user_id)
            if not user:
                return {}
            
            profile = await self.get_user_profile(user_id)
            
            return {
                "user_id": str(user.id),
                "username": user.username,
                "total_sessions": user.total_sessions,
                "total_messages": user.total_messages,
                "total_tokens_used": user.total_tokens_used,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at is not None else None,  # type: ignore[arg-type]
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

