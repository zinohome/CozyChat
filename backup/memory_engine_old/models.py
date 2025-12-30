"""
记忆数据模型

定义记忆对象和相关数据结构
"""

# 标准库
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MemoryType(str, Enum):
    """记忆类型枚举"""
    USER = "user"           # 用户记忆（用户说的话）
    ASSISTANT = "assistant"  # AI记忆（AI说的话）
    SYSTEM = "system"       # 系统记忆


@dataclass
class Memory:
    """记忆对象
    
    Attributes:
        id: 记忆ID
        user_id: 用户ID
        session_id: 会话ID
        memory_type: 记忆类型
        content: 记忆内容
        embedding: 向量嵌入（可选，由向量数据库生成）
        importance: 重要性分数（0-1）
        metadata: 额外元数据
        created_at: 创建时间
        expires_at: 过期时间
    """
    
    id: str
    user_id: str
    session_id: str
    memory_type: MemoryType
    content: str
    embedding: Optional[List[float]] = None
    importance: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict: 字典表示
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "importance": self.importance,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """从字典创建Memory对象
        
        Args:
            data: 字典数据
            
        Returns:
            Memory: Memory对象
        """
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            session_id=data["session_id"],
            memory_type=MemoryType(data["memory_type"]),
            content=data["content"],
            embedding=data.get("embedding"),
            importance=data.get("importance", 0.5),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) 
                if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.utcnow()),
            expires_at=datetime.fromisoformat(data["expires_at"]) 
                if data.get("expires_at") else None
        )


@dataclass
class MemorySearchResult:
    """记忆搜索结果
    
    Attributes:
        memory: 记忆对象
        similarity: 相似度分数（0-1）
        distance: 距离分数（越小越相似）
    """
    memory: Memory
    similarity: float
    distance: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            **self.memory.to_dict(),
            "similarity": self.similarity
        }
        if self.distance is not None:
            result["distance"] = self.distance
        return result

