"""
记忆写入任务模型

定义异步记忆写入任务的数据结构。
"""

# 标准库
from datetime import datetime
from typing import Dict, Any, Literal
from enum import Enum

# 第三方库
from pydantic import BaseModel, Field


class MemoryWriteJobStatus(str, Enum):
    """记忆写入任务状态"""
    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class MemoryWriteJob(BaseModel):
    """记忆写入任务
    
    用于异步批量写入记忆到向量数据库。
    """
    
    job_id: str = Field(..., description="任务ID")
    memory_id: str = Field(..., description="记忆ID")
    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    role: Literal["user", "assistant"] = Field(..., description="角色类型")
    content: str = Field(..., description="记忆内容")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="重要性评分")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    source: Literal["chat", "voice", "tool"] = Field(default="chat", description="来源类型")
    status: MemoryWriteJobStatus = Field(default=MemoryWriteJobStatus.PENDING, description="任务状态")
    
    # 可选：用于去重的指纹
    content_hash: str = Field(default="", description="内容hash，用于去重")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_12345",
                "memory_id": "mem_67890",
                "user_id": "user_abc",
                "session_id": "session_xyz",
                "role": "user",
                "content": "用户提到他喜欢游泳",
                "importance": 0.8,
                "metadata": {"topic": "health", "activity": "swimming"},
                "source": "chat",
                "status": "pending"
            }
        }


class MemoryWriteBatch(BaseModel):
    """记忆写入批次
    
    用于批量处理多个写入任务。
    """
    
    batch_id: str = Field(..., description="批次ID")
    jobs: list[MemoryWriteJob] = Field(default_factory=list, description="任务列表")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    
    def add_job(self, job: MemoryWriteJob) -> None:
        """添加任务到批次
        
        Args:
            job: 写入任务
        """
        self.jobs.append(job)
    
    def get_jobs_by_collection(self) -> Dict[str, list[MemoryWriteJob]]:
        """按collection分组任务
        
        Returns:
            Dict[str, list[MemoryWriteJob]]: 分组后的任务
        """
        groups: Dict[str, list[MemoryWriteJob]] = {
            "user": [],
            "assistant": [],
            "mixed": []
        }
        
        for job in self.jobs:
            if job.role == "user":
                groups["user"].append(job)
            elif job.role == "assistant":
                groups["assistant"].append(job)
            
            # 所有记忆都写入mixed collection
            groups["mixed"].append(job)
        
        return groups

