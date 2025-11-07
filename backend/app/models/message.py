"""
消息数据模型

定义消息相关的数据库表结构
"""

# 标准库
from datetime import datetime
from typing import Any, Dict, Optional
import uuid

# 第三方库
from sqlalchemy import (
    Column, DateTime, String, Text, Float, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, DeclarativeBase

# 本地库
from .base import Base


# Message模型使用独立的基类，因为id字段类型不同（UUID vs Integer）
# 使用Base的registry，确保关系可以正确解析
class MessageBase(DeclarativeBase):
    """Message模型基类，使用Base的metadata和registry"""
    metadata = Base.metadata
    registry = Base.registry


class Message(MessageBase):
    """消息表
    
    存储会话中的消息内容
    """
    __tablename__ = "messages"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 外键
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 消息内容
    role = Column(String(20), nullable=False, index=True)  # user / assistant / system / tool
    content = Column(Text, nullable=False)
    
    # AI生成信息（仅role=assistant时）
    model = Column(String(100), nullable=True)
    temperature = Column(Float, nullable=True)
    tokens_used = Column(JSONB, nullable=True)  # {"prompt": 100, "completion": 50, "total": 150}
    
    # 工具调用（JSONB）
    tool_calls = Column(JSONB, nullable=True)
    
    # 记忆使用（JSONB）
    memories_used = Column(JSONB, nullable=True)  # [{"id": "mem_123", "similarity": 0.85}]
    
    # 元数据
    message_metadata = Column("metadata", JSONB, nullable=False, default={})
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关系
    session = relationship("Session", back_populates="messages")
    
    # 约束和索引
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system', 'tool')", name="check_role"),
        Index("idx_messages_session_id", "session_id"),
        Index("idx_messages_user_id", "user_id"),
        Index("idx_messages_created_at", "created_at"),
        Index("idx_messages_role", "role"),
        Index("idx_messages_session_created", "session_id", "created_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "user_id": str(self.user_id),
            "role": self.role,
            "content": self.content,
            "model": self.model,
            "temperature": self.temperature,
            "tokens_used": self.tokens_used or {},
            "tool_calls": self.tool_calls or [],
            "memories_used": self.memories_used or [],
            "metadata": self.message_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

