"""
用户画像加载服务

负责从数据库加载用户画像信息
"""

# 标准库
from typing import Dict, Optional
from uuid import UUID

# 第三方库
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 本地库
from app.models.user import User
from app.utils.logger import logger


class UserProfileLoader:
    """用户画像加载器
    
    负责从数据库加载用户画像信息
    """
    
    def __init__(self, db: AsyncSession):
        """初始化UserProfileLoader
        
        Args:
            db: 数据库会话（异步）
        """
        self.db = db
    
    async def load_user_profile(
        self,
        user_id: str
    ) -> Optional[Dict[str, any]]:
        """加载用户画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict[str, Any]]: 用户画像信息
        """
        try:
            # 查询用户信息
            stmt = select(User).where(User.id == UUID(user_id))
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                logger.debug(f"User not found: {user_id}")
                return None
            
            # 构建用户画像
            profile = {
                "username": str(user.username),  # type: ignore[arg-type]
                "preferences": user.preferences or {},  # type: ignore[arg-type]
            }
            
            logger.debug(
                f"Loaded user profile",
                extra={"user_id": user_id, "username": profile["username"]}
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to load user profile: {e}", exc_info=True)
            return None
