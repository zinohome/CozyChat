"""
用户统计管理器

提供用户使用数据统计和报表生成功能
"""

# 标准库
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# 第三方库
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, select

# 本地库
from app.models.user import User
from app.models.user_profile import UserProfile
from app.utils.logger import logger
from app.utils.type_helpers import (
    get_user_status,
    get_user_role,
    safe_int,
    safe_str
)
from typing import cast
from datetime import datetime


# ============================================================================
# 旧实现：UserStatsManagerLegacy（已移除）
# ============================================================================
# 创建时间：2024-XX-XX
# 移除时间：2025-01-XX
# 状态：✅ 已移除（新实现已验证通过）
# 替代：UserStatsManager (使用异步会话)
# 说明：Legacy类已在阶段三清理中移除，代码约200行
# 如需查看历史实现，请查看git历史记录
# ============================================================================


# ============================================================================
# 新实现：UserStatsManager
# ============================================================================
# 创建时间：2025-01-XX
# 状态：✅ 新实现，使用异步会话
# 替代：UserStatsManagerLegacy（已在 v2.0 移除）
# ============================================================================
class UserStatsManager:
    """用户统计管理器（异步版本）
    
    提供用户使用数据统计和报表生成功能
    使用异步数据库会话
    """
    
    def __init__(self, db: AsyncSession):
        """初始化用户统计管理器
        
        Args:
            db: 数据库会话（异步）
        """
        self.db = db
        
        logger.debug("UserStatsManager initialized")
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户统计信息（异步版本）
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        try:
            stmt = select(User).where(User.id == user_id)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return {}
            
            stmt = select(UserProfile).where(UserProfile.user_id == user_id)
            result = await self.db.execute(stmt)
            profile = result.scalar_one_or_none()
            
            return {
                "user_id": str(user.id),
                "username": safe_str(user.username),
                "email": safe_str(user.email),
                "display_name": safe_str(user.display_name) if user.display_name else None,
                "role": get_user_role(user),
                "status": get_user_status(user),
                "total_sessions": safe_int(user.total_sessions),
                "total_messages": safe_int(user.total_messages),
                "total_tokens_used": safe_int(user.total_tokens_used),
                "last_login_at": cast(datetime, user.last_login_at).isoformat() if user.last_login_at is not None else None,
                "created_at": user.created_at.isoformat(),
                "profile": {
                    "interests": profile.interests if profile else [],
                    "habits": profile.get_habits() if profile else {},
                    "personality_insights": profile.get_personality_insights() if profile else {},
                    "statistics": profile.get_statistics() if profile else {}
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}", exc_info=True)
            return {}
    
    async def get_user_activity(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取用户活动统计（异步版本）
        
        Args:
            user_id: 用户ID
            days: 统计天数（默认30天）
            
        Returns:
            Dict[str, Any]: 活动统计字典
        """
        try:
            stmt = select(User).where(User.id == user_id)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return {}
            
            # 计算日期范围
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 这里应该查询会话和消息表，但表还未创建
            # 简化实现：返回基础统计
            total_sessions = safe_int(user.total_sessions)
            total_messages = safe_int(user.total_messages)
            total_tokens_used = safe_int(user.total_tokens_used)
            
            return {
                "user_id": str(user.id),
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "total_tokens_used": total_tokens_used,
                "avg_messages_per_session": (
                    total_messages / total_sessions
                    if total_sessions > 0 else 0
                ),
                "avg_tokens_per_message": (
                    total_tokens_used / total_messages
                    if total_messages > 0 else 0
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get user activity: {e}", exc_info=True)
            return {}
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息（异步版本）
        
        Returns:
            Dict[str, Any]: 系统统计字典
        """
        try:
            # 统计用户总数
            stmt = select(func.count(User.id)).where(User.status != "deleted")
            result = await self.db.execute(stmt)
            total_users = result.scalar_one() or 0
            
            # 统计活跃用户（最近30天登录）
            # 注意：SQLAlchemy Column类型在查询中可以直接与值比较，这是SQLAlchemy的正常用法
            # 类型检查器无法理解这一点，因此需要type: ignore
            stmt = select(func.count(User.id)).where(
                and_(
                    User.status == "active",  # type: ignore[arg-type]  # SQLAlchemy查询语法
                    User.last_login_at >= datetime.utcnow() - timedelta(days=30)  # type: ignore[arg-type]  # SQLAlchemy查询语法
                )
            )
            result = await self.db.execute(stmt)
            active_users = result.scalar_one() or 0
            
            # 统计总会话数
            stmt = select(func.sum(User.total_sessions))
            result = await self.db.execute(stmt)
            total_sessions = result.scalar_one() or 0
            
            # 统计总消息数
            stmt = select(func.sum(User.total_messages))
            result = await self.db.execute(stmt)
            total_messages = result.scalar_one() or 0
            
            # 统计总Token使用量
            stmt = select(func.sum(User.total_tokens_used))
            result = await self.db.execute(stmt)
            total_tokens = result.scalar_one() or 0
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "total_tokens_used": total_tokens,
                "avg_sessions_per_user": (
                    total_sessions / total_users if total_users > 0 else 0
                ),
                "avg_messages_per_user": (
                    total_messages / total_users if total_users > 0 else 0
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}", exc_info=True)
            return {}
    
    async def update_user_stats(
        self,
        user_id: str,
        sessions: int = 0,
        messages: int = 0,
        tokens: int = 0
    ) -> bool:
        """更新用户统计信息（异步版本）
        
        Args:
            user_id: 用户ID
            sessions: 新增会话数（可选）
            messages: 新增消息数（可选）
            tokens: 新增Token数（可选）
            
        Returns:
            bool: 是否更新成功
        """
        try:
            stmt = select(User).where(User.id == user_id)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            if sessions > 0:
                # SQLAlchemy ORM属性赋值，使用cast明确类型
                current_sessions = safe_int(user.total_sessions)
                user.total_sessions = cast(int, current_sessions + sessions)
            
            if messages > 0:
                current_messages = safe_int(user.total_messages)
                user.total_messages = cast(int, current_messages + messages)
            
            if tokens > 0:
                current_tokens = safe_int(user.total_tokens_used)
                user.total_tokens_used = cast(int, current_tokens + tokens)
            
            await self.db.commit()
            
            logger.debug(
                f"User stats updated: {user_id}",
                extra={"user_id": user_id, "sessions": sessions, "messages": messages, "tokens": tokens}
            )
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update user stats: {e}", exc_info=True)
            return False
