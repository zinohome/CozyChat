"""
记忆相关的Pydantic schemas

定义Memory API的请求和响应数据模型
"""

# 标准库
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

# 第三方库
from pydantic import BaseModel, Field


class MemoryCreate(BaseModel):
    """创建记忆请求"""
    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    content: str = Field(..., description="记忆内容")
    memory_type: Literal["user", "assistant", "system"] = Field(..., description="记忆类型")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="重要性分数")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="额外元数据")


class MemoryResponse(BaseModel):
    """记忆响应"""
    id: str
    user_id: str
    session_id: str
    memory_type: str
    content: str
    importance: float
    metadata: Dict[str, Any]
    created_at: str


class MemorySearchRequest(BaseModel):
    """记忆搜索请求"""
    query: str = Field(..., description="查询文本")
    user_id: str = Field(..., description="用户ID")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    memory_type: Optional[Literal["user", "assistant", "both"]] = Field(
        default="both",
        description="记忆类型"
    )
    limit: int = Field(default=5, gt=0, le=50, description="返回结果数量限制")
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="相似度阈值"
    )


class MemorySearchResult(BaseModel):
    """记忆搜索结果"""
    memory: MemoryResponse
    similarity: float
    distance: Optional[float] = None


class MemorySearchResponse(BaseModel):
    """记忆搜索响应"""
    results: List[MemorySearchResult]
    total_count: int


class MemoryStatsResponse(BaseModel):
    """记忆统计响应"""
    user_id: str
    user_memories_count: int
    assistant_memories_count: int
    total_memories_count: int
    cache_size: Optional[int] = None
    pending_saves: Optional[int] = None

