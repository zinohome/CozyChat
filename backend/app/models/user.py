"""
用户数据模型

定义用户相关的数据库表结构
"""

# 标准库
import json
from datetime import datetime
from typing import Any, Dict, Optional

# 第三方库
from sqlalchemy import (
    Boolean, Column, DateTime, Integer, String, Text, 
    CheckConstraint, BigInteger, Index
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, INET, ARRAY
from sqlalchemy.orm import relationship
import uuid

# 本地库
from sqlalchemy.orm import DeclarativeBase
from .base import Base
from app.utils.logger import logger


# User模型使用独立的基类，因为id字段类型不同（UUID vs Integer）
# 使用Base的registry，确保关系可以正确解析
class UserBase(DeclarativeBase):
    """User模型基类，使用Base的metadata和registry"""
    metadata = Base.metadata
    registry = Base.registry


class User(UserBase):
    """用户模型
    
    存储用户基本信息和认证信息
    
    Attributes:
        username: 用户名（唯一）
        email: 邮箱地址（唯一）
        password_hash: 哈希后的密码
        role: 用户角色（admin/user/guest）
        status: 用户状态（active/suspended/deleted）
        display_name: 显示名称
        avatar_url: 头像URL
        bio: 个人简介
        preferences: 偏好设置（JSONB）
        email_verified: 邮箱是否已验证
        email_verified_at: 邮箱验证时间
        last_login_at: 最后登录时间
        last_login_ip: 最后登录IP
        total_sessions: 总会话数
        total_messages: 总消息数
        total_tokens_used: 总Token使用量
    """
    
    __tablename__ = "users"
    
    # 使用UUID作为主键（PostgreSQL）
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # 基本信息
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # 角色和状态
    role = Column(
        String(20),
        nullable=False,
        default="user",
        index=True
    )
    status = Column(
        String(20),
        nullable=False,
        default="active",
        index=True
    )
    
    # 个人资料
    display_name = Column(String(100), nullable=True)
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    
    # 偏好设置（JSONB）
    preferences = Column(
        JSONB,
        nullable=False,
        default=lambda: {
            "default_personality": "health_assistant",
            "language": "zh-CN",
            "theme": "blue",  # 使用颜色主题系统：blue, green, purple, orange, pink, cyan
            "auto_tts": False,
            "always_show_voice_input": False,  # 总是显示语音输入按钮（宽屏幕下也显示）
            "timezone": "Asia/Shanghai",  # 默认时区：上海
            "show_reasoning": False
        }
    )
    
    # 认证相关
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(INET, nullable=True)
    
    # 统计信息
    total_sessions = Column(Integer, default=0, nullable=False)
    total_messages = Column(Integer, default=0, nullable=False)
    total_tokens_used = Column(BigInteger, default=0, nullable=False)
    
    # 时间戳（手动添加，因为不继承Base）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)
    
    # 约束
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'user', 'guest')", name="check_role"),
        CheckConstraint("status IN ('active', 'suspended', 'deleted')", name="check_status"),
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_status", "status"),
        Index("idx_users_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    @property
    def is_authenticated(self) -> bool:
        """用户是否已认证"""
        return self.status == "active"
    
    @property
    def is_active(self) -> bool:
        """用户是否激活"""
        return self.status == "active"
    
    @property
    def is_admin(self) -> bool:
        """用户是否为管理员"""
        return self.role == "admin"
    
    def update_last_login(self, ip_address: Optional[str] = None) -> None:
        """更新最后登录时间和IP
        
        Args:
            ip_address: IP地址（可选）
        """
        self.last_login_at = datetime.utcnow()
        if ip_address:
            self.last_login_ip = ip_address
    
    def get_preferences(self) -> Dict[str, Any]:
        """获取用户偏好设置
        
        返回合并了默认值的偏好设置，确保所有字段都存在。
        
        Returns:
            Dict[str, Any]: 偏好设置字典
        """
        # 默认偏好设置
        default_preferences = {
            "default_personality": "health_assistant",
            "language": "zh-CN",
            "theme": "blue",  # 使用颜色主题系统：blue, green, purple, orange, pink, cyan
            "auto_tts": False,
            "always_show_voice_input": False,
            "timezone": "Asia/Shanghai",  # 默认时区：上海
            "show_reasoning": False
        }
        
        # 获取当前偏好设置
        current_prefs = {}
        if isinstance(self.preferences, dict):
            current_prefs = self.preferences
        elif isinstance(self.preferences, str):
            try:
                current_prefs = json.loads(self.preferences)
            except (json.JSONDecodeError, TypeError):
                current_prefs = {}
        
        # 合并默认值和当前值（当前值优先）
        merged_prefs = {**default_preferences, **current_prefs}
        
        # 迁移旧数据：如果 theme 是 "light"，转换为 "blue"
        if merged_prefs.get("theme") == "light":
            merged_prefs["theme"] = "blue"
        
        return merged_prefs
    
    def update_preferences(self, updates: Dict[str, Any]) -> None:
        """更新用户偏好设置
        
        Args:
            updates: 更新的偏好设置
        """
        current_prefs = self.get_preferences()
        logger.info(f"User.update_preferences: current_prefs={current_prefs}, updates={updates}")
        
        # 创建新的字典，确保更新生效
        updated_prefs = {**current_prefs, **updates}
        logger.info(f"User.update_preferences: merged_prefs={updated_prefs}")
        
        # 直接赋值，确保 SQLAlchemy 检测到变化
        self.preferences = updated_prefs
        
        # 验证更新后的偏好
        logger.info(f"User.update_preferences: self.preferences={self.preferences}, get_preferences()={self.get_preferences()}")


