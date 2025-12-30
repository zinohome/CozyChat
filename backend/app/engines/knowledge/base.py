"""
知识引擎基类

定义知识引擎的统一接口，用于知识图谱的构建和检索
"""

# 标准库
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# 本地库
from app.engines.base import BaseEngine, EngineType
from app.utils.logger import logger


class KnowledgeEngineBase(BaseEngine, ABC):
    """知识引擎基类
    
    提供知识图谱的统一接口，包括：
    - 知识搜索
    - 知识添加
    - 数据集管理
    
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
        """初始化知识引擎
        
        Args:
            engine_name: 引擎名称
            config: 引擎配置
            **kwargs: 其他参数
        """
        super().__init__(
            engine_name=engine_name,
            engine_type=EngineType.KNOWLEDGE,
            **kwargs
        )
        self.config = config
        self._initialized = False
        
        logger.info(
            f"Initializing knowledge engine: {engine_name}",
            extra={"engine_name": engine_name, "config": config}
        )
    
    @abstractmethod
    async def search_knowledge(
        self,
        query: str,
        dataset_names: Optional[List[str]] = None,
        top_k: int = 5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """搜索知识
        
        Args:
            query: 查询文本
            dataset_names: 数据集名称列表
            top_k: 返回结果数量
            **kwargs: 其他参数
        
        Returns:
            List[Dict]: 知识搜索结果列表，每个结果包含：
                - content: 知识内容
                - score: 相关度分数
                - source: 来源数据集
                - metadata: 元数据（可选）
        
        Raises:
            NotImplementedError: 子类未实现此方法
        """
        raise NotImplementedError("Subclass must implement search_knowledge()")
    
    @abstractmethod
    async def add_knowledge(
        self,
        content: str,
        dataset_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """添加知识
        
        Args:
            content: 知识内容
            dataset_name: 数据集名称
            metadata: 元数据
            **kwargs: 其他参数
        
        Returns:
            str: 知识ID
        
        Raises:
            NotImplementedError: 子类未实现此方法
        """
        raise NotImplementedError("Subclass must implement add_knowledge()")
    
    async def shutdown(self) -> None:
        """关闭引擎"""
        await super().shutdown()
        logger.info(f"Knowledge engine shutdown: {self.engine_name}")

