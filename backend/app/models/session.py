"""
会话数据模型

定义会话相关的数据库表结构
"""

# 标准库
from datetime import datetime
from typing import Any, Dict, Optional
import uuid

# 第三方库
from sqlalchemy import (
    Column, DateTime, Integer, String, BigInteger,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, DeclarativeBase

# 本地库
from .base import Base


# Session模型使用独立的基类，因为id字段类型不同（UUID vs Integer）
class SessionBase(DeclarativeBase):
    """Session模型基类，使用Base的metadata"""
    metadata = Base.metadata


class Session(SessionBase):
    """会话表
    
    存储用户的聊天会话信息
    """
    __tablename__ = "sessions"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    personality_id = Column(String(100), nullable=False, index=True)
    
    # 会话信息
    title = Column(String(255), nullable=False, default="新会话")
    
    # 元数据（JSONB）
    session_metadata = Column("metadata", JSONB, nullable=False, default={})
    
    # 统计信息
    message_count = Column(Integer, nullable=False, default=0)
    total_tokens_used = Column(BigInteger, nullable=False, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # 关系
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index("idx_sessions_user_id", "user_id"),
        Index("idx_sessions_personality_id", "personality_id"),
        Index("idx_sessions_created_at", "created_at"),
        Index("idx_sessions_last_message_at", "last_message_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "personality_id": self.personality_id,
            "title": self.title,
            "metadata": self.session_metadata or {},
            "message_count": self.message_count,
            "total_tokens_used": self.total_tokens_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
        }

