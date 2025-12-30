"""
会话记忆引擎数据模型
"""

# 标准库
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ConversationMemory:
    """会话记忆
    
    Attributes:
        memory: 记忆内容
        score: 相关度分数
        created_at: 创建时间
        session: 所属会话类型（current/cross）
        metadata: 元数据
    """
    memory: str
    score: float
    created_at: Optional[str] = None
    session: str = "current"
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict: 字典格式的记忆
        """
        return {
            "memory": self.memory,
            "score": self.score,
            "created_at": self.created_at,
            "session": self.session,
            "metadata": self.metadata or {}
        }


@dataclass
class MemoryAddRequest:
    """记忆添加请求
    
    Attributes:
        user_id: 用户ID
        session_id: 会话ID
        messages: 消息列表
        metadata: 元数据
    """
    user_id: str
    session_id: str
    messages: List[Dict[str, str]]
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict: 字典格式的请求
        """
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "messages": self.messages,
            "metadata": self.metadata or {}
        }

