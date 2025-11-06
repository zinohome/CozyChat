"""
用户统计管理器

提供用户使用数据统计和报表生成功能
"""

# 标准库
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# 第三方库
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

# 本地库
from app.models.user import User
from app.models.user_profile import UserProfile
from app.utils.logger import logger


class UserStatsManager:
    """用户统计管理器
    
    提供用户使用数据统计和报表生成功能
    """
    
    def __init__(self, db: Session):
        """初始化用户统计管理器
        
        Args:
            db: 数据库会话
        """
        self.db = db
        
        logger.debug("UserStatsManager initialized")
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            return {
                "user_id": str(user.id),
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name,
                "role": user.role,
                "status": user.status,
                "total_sessions": user.total_sessions,
                "total_messages": user.total_messages,
                "total_tokens_used": user.total_tokens_used,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
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
    
    def get_user_activity(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取用户活动统计
        
        Args:
            user_id: 用户ID
            days: 统计天数（默认30天）
            
        Returns:
            Dict[str, Any]: 活动统计字典
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            # 计算日期范围
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 这里应该查询会话和消息表，但表还未创建
            # 简化实现：返回基础统计
            return {
                "user_id": str(user.id),
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_sessions": user.total_sessions,
                "total_messages": user.total_messages,
                "total_tokens_used": user.total_tokens_used,
                "avg_messages_per_session": (
                    user.total_messages / user.total_sessions
                    if user.total_sessions > 0 else 0
                ),
                "avg_tokens_per_message": (
                    user.total_tokens_used / user.total_messages
                    if user.total_messages > 0 else 0
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get user activity: {e}", exc_info=True)
            return {}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息
        
        Returns:
            Dict[str, Any]: 系统统计字典
        """
        try:
            # 统计用户总数
            total_users = self.db.query(func.count(User.id)).filter(
                User.status != "deleted"
            ).scalar() or 0
            
            # 统计活跃用户（最近30天登录）
            active_users = self.db.query(func.count(User.id)).filter(
                and_(
                    User.status == "active",
                    User.last_login_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).scalar() or 0
            
            # 统计总会话数
            total_sessions = self.db.query(func.sum(User.total_sessions)).scalar() or 0
            
            # 统计总消息数
            total_messages = self.db.query(func.sum(User.total_messages)).scalar() or 0
            
            # 统计总Token使用量
            total_tokens = self.db.query(func.sum(User.total_tokens_used)).scalar() or 0
            
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
    
    def update_user_stats(
        self,
        user_id: str,
        sessions: int = 0,
        messages: int = 0,
        tokens: int = 0
    ) -> bool:
        """更新用户统计信息
        
        Args:
            user_id: 用户ID
            sessions: 新增会话数（可选）
            messages: 新增消息数（可选）
            tokens: 新增Token数（可选）
            
        Returns:
            bool: 是否更新成功
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            if sessions > 0:
                user.total_sessions += sessions
            
            if messages > 0:
                user.total_messages += messages
            
            if tokens > 0:
                user.total_tokens_used += tokens
            
            self.db.commit()
            
            logger.debug(
                f"User stats updated: {user_id}",
                extra={"user_id": user_id, "sessions": sessions, "messages": messages, "tokens": tokens}
            )
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user stats: {e}", exc_info=True)
            return False

