"""
会话上下文模型

用于存储会话的历史摘要和其他上下文信息
"""

# 标准库
from datetime import datetime
from typing import Optional
from uuid import uuid4

# 第三方库
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UUID, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

# 本地库
from app.models.base import Base


class SessionContext(Base):
    """会话上下文表
    
    存储会话的历史摘要，用于智能上下文构建。
    
    Attributes:
        id: 主键UUID
        session_id: 关联的会话ID
        user_id: 关联的用户ID
        context_type: 上下文类型（如 'history_summary'）
        content: 摘要文本内容
        start_message_index: 起始消息索引
        end_message_index: 结束消息索引
        message_count: 包含的消息数量
        token_count: 摘要的token数量
        vector_id: Qdrant中的向量ID
        metadata: 额外的元数据（JSON格式）
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    __tablename__ = "session_contexts"
    
    # ===== 主键 =====
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="会话上下文ID"
    )
    
    # ===== 关联字段 =====
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="会话ID"
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    
    # ===== 上下文信息 =====
    context_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="上下文类型：history_summary"
    )
    
    content = Column(
        Text,
        nullable=False,
        comment="摘要文本内容"
    )
    
    # ===== 消息范围 =====
    start_message_index = Column(
        Integer,
        nullable=False,
        comment="起始消息索引"
    )
    
    end_message_index = Column(
        Integer,
        nullable=False,
        comment="结束消息索引"
    )
    
    message_count = Column(
        Integer,
        nullable=False,
        comment="包含的消息数量"
    )
    
    # ===== 统计信息 =====
    token_count = Column(
        Integer,
        nullable=True,
        comment="摘要的token数量"
    )
    
    # ===== 向量存储 =====
    vector_id = Column(
        String(255),
        nullable=True,
        comment="Qdrant中的向量ID"
    )
    
    # ===== 元数据 =====
    metadata = Column(
        JSONB,
        nullable=True,
        default={},
        comment="额外的元数据"
    )
    
    # ===== 时间戳 =====
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="创建时间"
    )
    
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # ===== 关系 =====
    # session = relationship("Session", back_populates="contexts")
    # user = relationship("User", back_populates="session_contexts")
    
    # ===== 索引 =====
    __table_args__ = (
        Index('idx_session_contexts_session_created', 'session_id', 'created_at'),
    )
    
    def __repr__(self):
        return (
            f"<SessionContext(id={self.id}, "
            f"session_id={self.session_id}, "
            f"type={self.context_type}, "
            f"messages={self.start_message_index}-{self.end_message_index})>"
        )

