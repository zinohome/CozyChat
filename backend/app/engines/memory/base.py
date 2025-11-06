"""
记忆引擎基类

定义所有记忆引擎的统一接口
"""

# 标准库
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# 本地库
from app.utils.logger import logger
from .models import Memory, MemorySearchResult, MemoryType


class MemoryEngineBase(ABC):
    """记忆引擎基类
    
    所有记忆引擎实现必须继承此类并实现抽象方法
    
    Attributes:
        engine_name: 引擎名称
        config: 配置信息
    """
    
    def __init__(self, engine_name: str, config: Dict[str, Any]):
        """初始化记忆引擎
        
        Args:
            engine_name: 引擎名称
            config: 配置信息
        """
        self.engine_name = engine_name
        self.config = config
        
        logger.info(
            f"Initializing {engine_name} memory engine",
            extra={"engine": engine_name, "config": config}
        )
    
    @abstractmethod
    async def add_memory(self, memory: Memory) -> str:
        """添加记忆
        
        Args:
            memory: 记忆对象
            
        Returns:
            str: 记忆ID
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError
    
    @abstractmethod
    async def search_memories(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[MemorySearchResult]:
        """搜索相关记忆
        
        Args:
            query: 查询文本
            user_id: 用户ID
            session_id: 会话ID（可选）
            memory_type: 记忆类型（可选）
            limit: 返回结果数量限制
            similarity_threshold: 相似度阈值
            
        Returns:
            List[MemorySearchResult]: 搜索结果列表
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError
    
    @abstractmethod
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """删除记忆
        
        Args:
            memory_id: 记忆ID
            user_id: 用户ID（用于验证权限）
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError
    
    @abstractmethod
    async def delete_session_memories(
        self,
        user_id: str,
        session_id: str
    ) -> int:
        """删除会话的所有记忆
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            int: 删除的记忆数量
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError
    
    @abstractmethod
    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """获取记忆统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 统计信息
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 引擎是否健康
        """
        try:
            # 尝试获取统计信息（轻量级操作）
            await self.get_memory_stats("health_check_user")
            return True
        except Exception as e:
            logger.error(f"Health check failed for {self.engine_name}: {e}")
            return False
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.engine_name})>"

