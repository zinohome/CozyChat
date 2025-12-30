"""
用户ID标准化服务

确保所有引擎使用统一的用户标识符（CozyChat User.id - UUID）
"""

# 标准库
import uuid
from typing import Optional

# 第三方库
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

# 本地库
from app.models.user import User
from app.utils.logger import logger


class UserIDNormalizer:
    """用户ID标准化服务
    
    确保所有引擎使用统一的用户标识符（CozyChat User.id - UUID）
    
    功能：
    1. 如果传入的是UUID字符串，直接返回
    2. 如果传入的是username或email，查询数据库获取User.id
    3. 如果用户不存在，返回None并记录警告
    """
    
    @staticmethod
    async def normalize_user_id(
        user_id: str,
        db_session: AsyncSession
    ) -> Optional[str]:
        """标准化用户ID
        
        如果传入的是username或email，查询数据库获取User.id
        如果传入的是UUID，直接返回
        
        Args:
            user_id: 用户标识符（可能是UUID、username或email）
            db_session: 数据库会话（异步）
        
        Returns:
            str: 标准化的用户ID（UUID字符串），如果用户不存在返回None
        
        Example:
            >>> # UUID格式，直接返回
            >>> normalized = await UserIDNormalizer.normalize_user_id(
            ...     "550e8400-e29b-41d4-a716-446655440000",
            ...     db_session
            ... )
            >>> # 返回: "550e8400-e29b-41d4-a716-446655440000"
            
            >>> # username格式，查询数据库
            >>> normalized = await UserIDNormalizer.normalize_user_id(
            ...     "alice",
            ...     db_session
            ... )
            >>> # 返回: "550e8400-e29b-41d4-a716-446655440000" (User.id)
        """
        if not user_id:
            logger.warning("Empty user_id provided to normalize")
            return None
        
        # 1. 检查是否是有效的UUID格式
        try:
            # 尝试解析为UUID
            uuid_obj = uuid.UUID(user_id)
            # 是有效的UUID，直接返回（标准化格式）
            normalized = str(uuid_obj)
            logger.debug(
                f"User ID is already UUID format: {normalized}",
                extra={"user_id": user_id, "normalized": normalized}
            )
            return normalized
        except ValueError:
            # 不是UUID格式，可能是username或email
            logger.debug(
                f"User ID is not UUID format, querying database: {user_id}",
                extra={"user_id": user_id}
            )
        
        # 2. 查询数据库（按username或email）
        try:
            stmt = select(User).where(
                or_(
                    User.username == user_id,
                    User.email == user_id
                )
            )
            result = await db_session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                normalized = str(user.id)
                logger.info(
                    f"User ID normalized: {user_id} -> {normalized}",
                    extra={
                        "original": user_id,
                        "normalized": normalized,
                        "username": user.username
                    }
                )
                return normalized
            else:
                logger.warning(
                    f"User not found: {user_id}",
                    extra={"user_id": user_id}
                )
                return None
                
        except Exception as e:
            logger.error(
                f"Failed to normalize user ID: {e}",
                exc_info=True,
                extra={"user_id": user_id}
            )
            return None
    
    @staticmethod
    def is_uuid(user_id: str) -> bool:
        """检查字符串是否是有效的UUID格式
        
        Args:
            user_id: 用户标识符
        
        Returns:
            bool: 是否是有效的UUID格式
        """
        try:
            uuid.UUID(user_id)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def normalize_uuid_string(uuid_str: str) -> Optional[str]:
        """标准化UUID字符串格式（不查询数据库）
        
        只处理UUID格式的字符串，确保格式一致（小写，带连字符）
        
        Args:
            uuid_str: UUID字符串
        
        Returns:
            str: 标准化的UUID字符串，如果格式无效返回None
        """
        try:
            uuid_obj = uuid.UUID(uuid_str)
            return str(uuid_obj)
        except ValueError:
            return None

