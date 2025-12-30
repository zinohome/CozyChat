"""
用户画像模型

定义用户画像相关的数据库表结构
"""

# 标准库
import json
from datetime import datetime
from typing import Any, Dict, TYPE_CHECKING

# 第三方库
from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from sqlalchemy.orm import DeclarativeBase, relationship

# 本地库
from .base import Base

# 类型检查时导入，避免循环导入
if TYPE_CHECKING:
    from .user import User


# 创建独立的基类，不包含id字段，但使用Base的metadata和registry
class ProfileBase(DeclarativeBase):
    """用户画像基类，不包含id字段"""
    # 使用Base的metadata和registry，确保所有表在同一个metadata中，关系可以正确解析
    metadata = Base.metadata
    registry = Base.registry


class UserProfile(ProfileBase):
    """用户画像模型
    
    存储用户画像和行为数据
    
    Attributes:
        user_id: 用户ID（外键，也是主键）
        interests: 兴趣标签
        habits: 使用习惯（JSONB）
        personality_insights: 人格洞察（JSONB）
        statistics: 统计数据（JSONB）
    """
    
    __tablename__ = "user_profiles"
    
    # 主键和外键
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        index=True
    )
    
    # 兴趣标签
    interests = Column(
        ARRAY(Text),
        nullable=False,
        default=[]
    )
    
    # 使用习惯（JSONB）
    habits = Column(
        JSONB,
        nullable=False,
        default=lambda: {
            "most_active_time": "evening",
            "avg_session_duration_minutes": 0,
            "favorite_topics": []
        }
    )
    
    # 人格洞察（JSONB）
    personality_insights = Column(
        JSONB,
        nullable=False,
        default=lambda: {
            "communication_style": "",
            "question_types": [],
            "interaction_patterns": {}
        }
    )
    
    # 统计数据（JSONB）
    statistics = Column(
        JSONB,
        nullable=False,
        default={}
    )
    
    # 时间戳（手动添加，不继承Base）
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系（延迟配置，在模型导入完成后配置）
    # 注意：使用字符串引用，SQLAlchemy会在所有模型定义完成后解析
    user = relationship(
        "User",
        backref="profile",
        lazy="select",
        uselist=False
    )
    
    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id})>"
    
    def get_habits(self) -> Dict[str, Any]:
        """获取使用习惯
        
        Returns:
            Dict[str, Any]: 使用习惯字典
        """
        if isinstance(self.habits, dict):
            return self.habits
        elif isinstance(self.habits, str):
            return json.loads(self.habits)
        return {}
    
    def update_habits(self, updates: Dict[str, Any]) -> None:
        """更新使用习惯
        
        Args:
            updates: 更新的习惯数据
        """
        current_habits = self.get_habits()
        current_habits.update(updates)
        self.habits = current_habits
    
    def get_personality_insights(self) -> Dict[str, Any]:
        """获取人格洞察
        
        Returns:
            Dict[str, Any]: 人格洞察字典
        """
        if isinstance(self.personality_insights, dict):
            return self.personality_insights
        elif isinstance(self.personality_insights, str):
            return json.loads(self.personality_insights)
        return {}
    
    def update_personality_insights(self, updates: Dict[str, Any]) -> None:
        """更新人格洞察
        
        Args:
            updates: 更新的洞察数据
        """
        current_insights = self.get_personality_insights()
        current_insights.update(updates)
        self.personality_insights = current_insights
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计数据
        
        Returns:
            Dict[str, Any]: 统计数据字典
        """
        if isinstance(self.statistics, dict):
            return self.statistics
        elif isinstance(self.statistics, str):
            return json.loads(self.statistics)
        return {}
    
    def update_statistics(self, updates: Dict[str, Any]) -> None:
        """更新统计数据
        
        Args:
            updates: 更新的统计数据
        """
        current_stats = self.get_statistics()
        current_stats.update(updates)
        self.statistics = current_stats

