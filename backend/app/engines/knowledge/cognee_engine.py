"""
Cognee知识引擎实现

通过cognee_sdk连接Cognee后端服务，实现知识图谱的构建和检索
"""

# 标准库
import time
from typing import Any, Dict, List, Optional

# 第三方库
from cognee_sdk import CogneeClient, SearchType

# 本地库
from app.engines.knowledge.base import KnowledgeEngineBase
from app.utils.logger import logger


class CogneeKnowledgeEngine(KnowledgeEngineBase):
    """Cognee知识引擎实现
    
    使用cognee_sdk连接Cognee后端服务，提供：
    - 知识图谱检索（支持CHUNKS和GRAPH_COMPLETION模式）
    - 知识添加
    - 数据集管理
    
    Attributes:
        api_url: Cognee API服务地址
        api_token: Cognee API Token
        client: CogneeClient实例
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化Cognee引擎
        
        Args:
            config: 引擎配置，包含：
                - api_url: API服务地址
                - api_token: API Token（可选）
        """
        super().__init__(engine_name="cognee", config=config)
        
        self.api_url = config.get("api_url", "http://localhost:8000")
        self.api_token = config.get("api_token")
        self.client: Optional[CogneeClient] = None
    
    async def initialize(self) -> bool:
        """初始化Cognee客户端
        
        Returns:
            bool: 初始化是否成功
        """
        if self._initialized:
            return True
        
        try:
            start_time = time.time()
            
            # 创建Cognee客户端
            self.client = CogneeClient(
                api_url=self.api_url,
                api_token=self.api_token
            )
            
            # 执行健康检查
            is_healthy = await self.health_check()
            
            if is_healthy:
                self._initialized = True
                processing_time = time.time() - start_time
                self.update_metrics(success=True, processing_time=processing_time)
                
                logger.info(
                    f"Cognee knowledge engine initialized successfully",
                    extra={
                        "api_url": self.api_url,
                        "processing_time": processing_time
                    }
                )
            else:
                logger.error("Cognee health check failed during initialization")
            
            return is_healthy
            
        except Exception as e:
            logger.error(
                f"Failed to initialize Cognee engine: {e}",
                exc_info=True,
                extra={"api_url": self.api_url}
            )
            return False
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 引擎是否健康
        """
        if not self.client:
            return False
        
        try:
            # Cognee SDK的health_check方法
            health = await self.client.health_check()
            # Cognee返回的status可能是 "ok" 或 "ready"，都视为健康
            is_healthy = health.status in ("ok", "ready")
            
            if is_healthy:
                logger.debug(f"Cognee health check passed (status: {health.status})")
            else:
                logger.warning(
                    f"Cognee health check failed: {health.status}",
                    extra={"status": health.status}
                )
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"Cognee health check error: {e}", exc_info=True)
            return False
    
    async def search_knowledge(
        self,
        query: str,
        dataset_names: Optional[List[str]] = None,
        top_k: int = 5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """搜索知识
        
        使用多策略搜索：
        1. 优先使用CHUNKS模式（快速）
        2. 如果失败或返回空，降级到GRAPH_COMPLETION模式（稳定）
        
        Args:
            query: 查询文本
            dataset_names: 数据集名称列表
            top_k: 返回结果数量
            **kwargs: 其他参数
        
        Returns:
            List[Dict]: 知识搜索结果列表
        """
        # 确保引擎已初始化
        await self.initialize()
        
        if not dataset_names:
            logger.warning("No dataset names provided for knowledge search")
            return []
        
        start_time = time.time()
        
        try:
            results = None
            
            # 策略1: 尝试CHUNKS模式（快速）
            try:
                logger.debug(f"Trying CHUNKS mode for query: {query}")
                results = await self.client.search(  # type: ignore[union-attr]
                    query=query,
                    datasets=dataset_names,
                    search_type=SearchType.CHUNKS,
                    top_k=top_k
                )
                
                if results and len(results) > 0:
                    logger.debug(f"CHUNKS mode returned {len(results)} results")
                else:
                    logger.debug("CHUNKS mode returned empty, fallback to GRAPH_COMPLETION")
                    results = None
                    
            except Exception as e:
                logger.debug(f"CHUNKS mode failed: {e}, fallback to GRAPH_COMPLETION")
                results = None
            
            # 策略2: 使用GRAPH_COMPLETION模式（稳定）
            if not results:
                logger.debug(f"Using GRAPH_COMPLETION mode for query: {query}")
                results = await self.client.search(  # type: ignore[union-attr]
                    query=query,
                    datasets=dataset_names,
                    search_type=SearchType.GRAPH_COMPLETION,
                    top_k=top_k
                )
            
            # 解析结果
            knowledge_results = self._parse_search_results(results, dataset_names)
            
            # 更新指标
            processing_time = time.time() - start_time
            self.update_metrics(success=True, processing_time=processing_time)
            
            logger.info(
                f"Knowledge search completed",
                extra={
                    "query": query[:50],
                    "datasets": dataset_names,
                    "results_count": len(knowledge_results),
                    "processing_time": processing_time
                }
            )
            
            return knowledge_results
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.update_metrics(success=False, processing_time=processing_time)
            
            # 判断是否是数据集不存在错误
            error_msg = str(e)
            if "DatasetNotFoundError" in error_msg or "No datasets found" in error_msg:
                logger.warning(
                    f"Dataset not found: {dataset_names}",
                    extra={"error": error_msg}
                )
            else:
                logger.error(
                    f"Knowledge search error: {e}",
                    exc_info=True,
                    extra={
                        "query": query[:50],
                        "datasets": dataset_names
                    }
                )
            
            return []
    
    def _parse_search_results(
        self,
        results: Any,
        dataset_names: List[str]
    ) -> List[Dict[str, Any]]:
        """解析搜索结果
        
        Args:
            results: Cognee SDK返回的原始结果
            dataset_names: 数据集名称列表
        
        Returns:
            List[Dict]: 解析后的结果列表
        """
        knowledge_results = []
        
        for i, result in enumerate(results):
            content = None
            default_score = 1.0 - (i * 0.1)  # 按顺序递减分数
            score = default_score
            
            # 解析不同格式的结果
            if isinstance(result, str):
                # 字符串格式（GRAPH_COMPLETION模式）
                content = result
            elif hasattr(result, 'text'):
                # SearchResult对象格式（CHUNKS模式）
                content = result.text  # type: ignore[attr-defined]
                result_score = getattr(result, 'score', None)
                score = result_score if result_score is not None else default_score
            elif hasattr(result, 'content'):
                # 其他对象格式
                content = result.content  # type: ignore[attr-defined]
                result_score = getattr(result, 'score', None)
                score = result_score if result_score is not None else default_score
            elif isinstance(result, dict):
                # 字典格式
                content = result.get("text") or result.get("content") or str(result)
                result_score = result.get("score")
                score = result_score if result_score is not None else default_score
            
            if content:
                knowledge_results.append({
                    "content": content,
                    "score": score,
                    "source": dataset_names[0] if dataset_names else "unknown",
                    "metadata": {}
                })
            else:
                logger.debug(
                    f"Failed to parse result {i+1}",
                    extra={"result_type": type(result).__name__}
                )
        
        return knowledge_results
    
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
        """
        # 确保引擎已初始化
        await self.initialize()
        
        start_time = time.time()
        
        try:
            result = await self.client.add(  # type: ignore[union-attr]
                data=content,
                dataset_name=dataset_name,
                metadata=metadata,
                **kwargs
            )
            
            # 更新指标
            processing_time = time.time() - start_time
            self.update_metrics(success=True, processing_time=processing_time)
            
            logger.info(
                f"Knowledge added successfully",
                extra={
                    "dataset": dataset_name,
                    "data_id": result.data_id,  # type: ignore[attr-defined]
                    "processing_time": processing_time
                }
            )
            
            return result.data_id  # type: ignore[attr-defined,return-value]
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.update_metrics(success=False, processing_time=processing_time)
            
            logger.error(
                f"Failed to add knowledge: {e}",
                exc_info=True,
                extra={"dataset": dataset_name}
            )
            raise
    
    async def shutdown(self) -> None:
        """关闭引擎"""
        if self.client:
            # Cognee SDK可能没有显式close方法
            self.client = None
        
        await super().shutdown()

