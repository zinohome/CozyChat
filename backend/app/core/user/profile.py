"""
用户画像管理器

提供用户画像生成、更新、查询等功能
"""

# 标准库
from typing import Any, Dict, List, Optional

# 第三方库
from sqlalchemy.orm import Session

# 本地库
from app.models.user import User
from app.models.user_profile import UserProfile
from app.utils.logger import logger


class UserProfileManager:
    """用户画像管理器
    
    提供用户画像生成、更新、查询等功能
    """
    
    def __init__(self, db: Session):
        """初始化用户画像管理器
        
        Args:
            db: 数据库会话
        """
        self.db = db
        
        logger.debug("UserProfileManager initialized")
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[UserProfile]: 用户画像对象，如果不存在返回None
        """
        try:
            return self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}", exc_info=True)
            return None
    
    def create_or_update_profile(
        self,
        user_id: str,
        interests: Optional[List[str]] = None,
        habits: Optional[Dict[str, Any]] = None,
        personality_insights: Optional[Dict[str, Any]] = None,
        statistics: Optional[Dict[str, Any]] = None
    ) -> UserProfile:
        """创建或更新用户画像
        
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
            profile = self.get_profile(user_id)
            
            if not profile:
                # 创建新画像
                profile = UserProfile(user_id=user_id)
                self.db.add(profile)
            
            # 更新字段
            if interests is not None:
                profile.interests = interests
            
            if habits is not None:
                profile.update_habits(habits)
            
            if personality_insights is not None:
                profile.update_personality_insights(personality_insights)
            
            if statistics is not None:
                profile.update_statistics(statistics)
            
            self.db.commit()
            self.db.refresh(profile)
            
            logger.info(f"User profile created/updated: {user_id}", extra={"user_id": user_id})
            
            return profile
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create/update user profile: {e}", exc_info=True)
            raise
    
    def add_interest(self, user_id: str, interest: str) -> bool:
        """添加兴趣标签
        
        Args:
            user_id: 用户ID
            interest: 兴趣标签
            
        Returns:
            bool: 是否添加成功
        """
        try:
            profile = self.get_profile(user_id)
            
            if not profile:
                profile = UserProfile(user_id=user_id)
                # 确保interests字段被初始化
                if profile.interests is None:
                    profile.interests = []
                self.db.add(profile)
            
            # 确保interests字段存在
            if profile.interests is None:
                profile.interests = []
            
            if interest not in profile.interests:
                profile.interests.append(interest)
                self.db.commit()
                self.db.refresh(profile)  # 刷新对象以获取最新数据
                logger.info(f"Interest added: {interest}", extra={"user_id": user_id})
                return True
            
            return False
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add interest: {e}", exc_info=True)
            return False
    
    def update_habits(
        self,
        user_id: str,
        most_active_time: Optional[str] = None,
        avg_session_duration: Optional[float] = None,
        favorite_topics: Optional[List[str]] = None
    ) -> bool:
        """更新使用习惯
        
        Args:
            user_id: 用户ID
            most_active_time: 最活跃时间（可选）
            avg_session_duration: 平均会话时长（分钟，可选）
            favorite_topics: 喜欢的话题（可选）
            
        Returns:
            bool: 是否更新成功
        """
        try:
            profile = self.get_profile(user_id)
            
            if not profile:
                profile = UserProfile(user_id=user_id)
                self.db.add(profile)
            
            habits = profile.get_habits()
            
            if most_active_time is not None:
                habits["most_active_time"] = most_active_time
            
            if avg_session_duration is not None:
                habits["avg_session_duration_minutes"] = avg_session_duration
            
            if favorite_topics is not None:
                habits["favorite_topics"] = favorite_topics
            
            profile.update_habits(habits)
            self.db.commit()
            self.db.refresh(profile)  # 刷新对象以获取最新数据
            
            logger.info(f"User habits updated: {user_id}", extra={"user_id": user_id})
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update habits: {e}", exc_info=True)
            return False
    
    def generate_profile_from_behavior(
        self,
        user_id: str,
        behavior_data: Dict[str, Any]
    ) -> UserProfile:
        """从行为数据生成用户画像
        
        Args:
            user_id: 用户ID
            behavior_data: 行为数据字典
            
        Returns:
            UserProfile: 用户画像对象
        """
        try:
            # 提取兴趣标签
            interests = behavior_data.get("interests", [])
            
            # 提取使用习惯
            habits = {
                "most_active_time": behavior_data.get("most_active_time", "evening"),
                "avg_session_duration_minutes": behavior_data.get("avg_session_duration", 0),
                "favorite_topics": behavior_data.get("favorite_topics", [])
            }
            
            # 提取人格洞察
            personality_insights = {
                "communication_style": behavior_data.get("communication_style", ""),
                "question_types": behavior_data.get("question_types", []),
                "interaction_patterns": behavior_data.get("interaction_patterns", {})
            }
            
            # 提取统计数据
            statistics = behavior_data.get("statistics", {})
            
            # 创建或更新画像
            profile = self.create_or_update_profile(
                user_id=user_id,
                interests=interests,
                habits=habits,
                personality_insights=personality_insights,
                statistics=statistics
            )
            
            logger.info(
                f"User profile generated from behavior: {user_id}",
                extra={"user_id": user_id}
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to generate profile from behavior: {e}", exc_info=True)
            raise

