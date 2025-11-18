"""
上下文相关的Pydantic模型

用于智能上下文构建和历史摘要
"""

# 标准库
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

# 第三方库
from pydantic import BaseModel, Field

# 本地库
from app.schemas.message import MessageResponse
from app.engines.memory.models import Memory


# ===== 历史摘要 =====

class HistorySummaryBase(BaseModel):
    """历史摘要基础模型"""
    
    content: str = Field(..., description="摘要文本内容")
    start_message_index: int = Field(..., description="起始消息索引")
    end_message_index: int = Field(..., description="结束消息索引")
    message_count: int = Field(..., description="包含的消息数量")
    token_count: Optional[int] = Field(None, description="摘要的token数量")


class HistorySummaryCreate(HistorySummaryBase):
    """创建历史摘要请求"""
    
    session_id: UUID = Field(..., description="会话ID")
    user_id: UUID = Field(..., description="用户ID")
    context_type: str = Field(default="history_summary", description="上下文类型")
    vector_id: Optional[str] = Field(None, description="Qdrant中的向量ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")


class HistorySummaryResponse(HistorySummaryBase):
    """历史摘要响应"""
    
    id: UUID = Field(..., description="摘要ID")
    session_id: UUID = Field(..., description="会话ID")
    user_id: UUID = Field(..., description="用户ID")
    context_type: str = Field(..., description="上下文类型")
    vector_id: Optional[str] = Field(None, description="Qdrant中的向量ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


# ===== 上下文构建 =====

class ContextBundle(BaseModel):
    """上下文包
    
    包含构建LLM prompt所需的所有上下文信息
    """
    
    system_prompts: List[str] = Field(
        default_factory=list,
        description="系统提示词列表"
    )
    
    recent_messages: List[MessageResponse] = Field(
        default_factory=list,
        description="最近的原文对话"
    )
    
    summarized_history: List[str] = Field(
        default_factory=list,
        description="历史摘要片段"
    )
    
    retrieved_memories: List[Memory] = Field(
        default_factory=list,
        description="检索到的长期记忆"
    )
    
    user_profile: Optional[Dict[str, Any]] = Field(
        None,
        description="用户画像信息"
    )
    
    total_tokens: Optional[int] = Field(
        None,
        description="估算的总token数"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="额外的元数据"
    )


class ContextBuildRequest(BaseModel):
    """构建上下文请求"""
    
    user_id: UUID = Field(..., description="用户ID")
    session_id: UUID = Field(..., description="会话ID")
    current_message: str = Field(..., description="当前用户消息")
    personality_id: str = Field(..., description="人格ID")
    recent_message_count: int = Field(
        default=6,
        description="保留的最近消息数量"
    )
    include_memories: bool = Field(
        default=True,
        description="是否包含长期记忆"
    )
    include_summaries: bool = Field(
        default=True,
        description="是否包含历史摘要"
    )
    max_tokens: int = Field(
        default=8000,
        description="最大token数量"
    )


class SummaryGenerationRequest(BaseModel):
    """生成摘要请求"""
    
    session_id: UUID = Field(..., description="会话ID")
    user_id: UUID = Field(..., description="用户ID")
    start_message_index: int = Field(..., description="起始消息索引")
    end_message_index: int = Field(..., description="结束消息索引")
    force: bool = Field(
        default=False,
        description="是否强制重新生成（即使已存在）"
    )


class SummaryGenerationResponse(BaseModel):
    """生成摘要响应"""
    
    session_id: UUID = Field(..., description="会话ID")
    summary: HistorySummaryResponse = Field(..., description="生成的摘要")
    generation_time: float = Field(..., description="生成耗时（秒）")


# ===== 上下文统计 =====

class ContextStats(BaseModel):
    """上下文统计信息"""
    
    session_id: UUID = Field(..., description="会话ID")
    total_messages: int = Field(..., description="总消息数")
    summary_count: int = Field(..., description="摘要数量")
    summarized_message_count: int = Field(..., description="已摘要的消息数")
    unsummarized_message_count: int = Field(..., description="未摘要的消息数")
    last_summary_at: Optional[datetime] = Field(None, description="最后摘要时间")
    should_generate_summary: bool = Field(..., description="是否应该生成新摘要")

