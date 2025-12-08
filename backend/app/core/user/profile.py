"""
用户画像管理器

提供用户画像生成、更新、查询等功能
"""

# 标准库
from typing import Any, Dict, List, Optional

# 第三方库
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# 本地库
from app.models.user import User
from app.models.user_profile import UserProfile
from app.utils.logger import logger


# ============================================================================
# 旧实现：UserProfileManagerLegacy（已移除）
# ============================================================================
# 创建时间：2024-XX-XX
# 移除时间：2025-01-XX
# 状态：✅ 已移除（新实现已验证通过）
# 替代：UserProfileManager (使用异步会话)
# 说明：Legacy类已在阶段三清理中移除，代码约230行
# 如需查看历史实现，请查看git历史记录
# ============================================================================
# 新实现：UserProfileManager
# ============================================================================
# 创建时间：2025-01-XX
# 状态：✅ 新实现，使用异步会话
# 替代：UserProfileManagerLegacy（已在 v2.0 移除）
# ============================================================================
class UserProfileManager:
    """用户画像管理器（异步版本）
    
    提供用户画像生成、更新、查询等功能
    使用异步数据库会话
    """
    
    def __init__(self, db: AsyncSession):
        """初始化用户画像管理器
        
        Args:
            db: 数据库会话（异步）
        """
        self.db = db
        
        logger.debug("UserProfileManager initialized")
    
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
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
    
    async def create_or_update_profile(
        self,
        user_id: str,
        interests: Optional[List[str]] = None,
        habits: Optional[Dict[str, Any]] = None,
        personality_insights: Optional[Dict[str, Any]] = None,
        statistics: Optional[Dict[str, Any]] = None
    ) -> UserProfile:
        """创建或更新用户画像（异步版本）
        
        Args:
            user_id: 用户ID
            interests: 兴趣标签（可选）
            habits: 使用习惯（可选）
            personality_insights: 人格洞察（可选）
            statistics: 统计数据（可选）
            
        Returns:
            UserProfile: 用户画像对象
        """
        try:
            profile = await self.get_profile(user_id)
            
            if not profile:
                # 创建新画像
                profile = UserProfile(user_id=user_id)
                self.db.add(profile)
            
            # 更新字段
            if interests is not None:
                profile.interests = interests  # type: ignore[assignment]
            
            if habits is not None:
                profile.update_habits(habits)
            
            if personality_insights is not None:
                profile.update_personality_insights(personality_insights)
            
            if statistics is not None:
                profile.update_statistics(statistics)
            
            await self.db.commit()
            await self.db.refresh(profile)
            
            logger.info(f"User profile created/updated: {user_id}", extra={"user_id": user_id})
            
            return profile
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create/update user profile: {e}", exc_info=True)
            raise

