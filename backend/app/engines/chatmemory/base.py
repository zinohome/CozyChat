"""
会话记忆引擎基类

定义会话记忆引擎的统一接口，用于短期对话记忆管理
"""

# 标准库
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# 本地库
from app.engines.base import BaseEngine, EngineType
from app.utils.logger import logger


class ChatMemoryEngineBase(BaseEngine, ABC):
    """会话记忆引擎基类
    
    提供会话记忆的统一接口，包括：
    - 记忆搜索
    - 记忆添加
    - 会话管理
    
    Attributes:
        engine_name: 引擎名称
        config: 引擎配置字典
    """
    
    def __init__(
        self,
        engine_name: str,
        config: Dict[str, Any],
        **kwargs
    ):
        """初始化会话记忆引擎
        
        Args:
            engine_name: 引擎名称
            config: 引擎配置
            **kwargs: 其他参数
        """
        super().__init__(
            engine_name=engine_name,
            engine_type=EngineType.CHATMEMORY,
            **kwargs
        )
        self.config = config
        self._initialized = False
        
        logger.info(
            f"Initializing chatmemory engine: {engine_name}",
            extra={"engine_name": engine_name, "config": config}
        )
    
    @abstractmethod
    async def search_memories(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        top_k: int = 5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """搜索会话记忆
        
        Args:
            query: 查询文本
            user_id: 用户ID
            session_id: 会话ID（可选）
            top_k: 返回结果数量
            **kwargs: 其他参数
        
        Returns:
            List[Dict]: 记忆搜索结果列表，每个结果包含：
                - memory: 记忆内容
                - score: 相关度分数
                - created_at: 创建时间
                - session: 所属会话（current/cross）
        
        Raises:
            NotImplementedError: 子类未实现此方法
        """
        raise NotImplementedError("Subclass must implement search_memories()")
    
    @abstractmethod
    async def add_memory(
        self,
        user_id: str,
        session_id: str,
        messages: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """添加会话记忆
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            messages: 消息列表
            metadata: 元数据
            **kwargs: 其他参数
        
        Returns:
            str: 记忆ID
        
        Raises:
            NotImplementedError: 子类未实现此方法
        """
        raise NotImplementedError("Subclass must implement add_memory()")
    
    async def shutdown(self) -> None:
        """关闭引擎"""
        await super().shutdown()
        logger.info(f"ChatMemory engine shutdown: {self.engine_name}")

