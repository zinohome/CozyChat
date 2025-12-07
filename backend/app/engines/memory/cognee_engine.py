"""
Cognee 记忆引擎实现

使用 Cognee 知识图谱框架存储和检索记忆
"""

# 标准库
import asyncio
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# 第三方库
try:
    import cognee
    from cognee.modules.search.types import SearchType
    COGNEE_AVAILABLE = True
except ImportError:
    COGNEE_AVAILABLE = False
    cognee = None  # type: ignore
    SearchType = None  # type: ignore

# 本地库
from app.utils.logger import logger
from .base import MemoryEngineBase
from .models import Memory, MemorySearchResult, MemoryType


class CogneeMemoryEngine(MemoryEngineBase):
    """Cognee 记忆引擎适配器
    
    将 CozyChat 的记忆接口适配到 Cognee 知识图谱框架
    
    Attributes:
        _initialized: Cognee 是否已初始化
        queue: 异步写入队列
        async_enabled: 是否启用异步写入
        database_url: PostgreSQL 数据库 URL
        vector_db_provider: 向量数据库提供商
        graph_database_provider: 图数据库提供商
        graph_database_url: 图数据库 URL
        graph_database_username: 图数据库用户名
        graph_database_password: 图数据库密码
        redis_url: Redis URL（用于异步队列）
        user_dataset_pattern: 用户数据集命名模式
        user_node_set_pattern: 用户节点集命名模式
        assistant_node_set_pattern: AI助手节点集命名模式
        default_top_k: 默认返回结果数量
        similarity_threshold: 相似度阈值
        enable_cognify: 是否启用知识图谱构建
        enable_graph_search: 是否启用图遍历搜索
    """
    
    def __init__(self, engine_name: str, config: Dict[str, Any]):
        """初始化 Cognee 引擎
        
        Args:
            engine_name: 引擎名称
            config: 配置信息（从 YAML 读取）
        """
        # 检查依赖
        if not COGNEE_AVAILABLE:
            raise ImportError(
                "Cognee is not installed. "
                "Install it with: pip install cognee"
            )
        
        super().__init__(engine_name, config)
        
        # ✅ 从配置读取所有参数（不硬编码）
        # 数据库配置
        self.database_url = config.get("database_url")
        if not self.database_url:
            raise ValueError("Cognee database_url is required in config")
        
        self.vector_db_provider = config.get("vector_db_provider", "pgvector")
        
        # 图数据库配置
        self.graph_database_provider = config.get("graph_database_provider")
        self.graph_database_url = config.get("graph_database_url")
        self.graph_database_username = config.get("graph_database_username")
        self.graph_database_password = config.get("graph_database_password")
        
        # Redis 配置（Cognee 内部使用，不用于队列）
        redis_url = config.get("redis_url")
        if not redis_url:
            raise ValueError("Cognee redis_url is required in config")
        self.redis_url = redis_url
        
        # S3/MinIO 配置
        self.s3_endpoint = config.get("s3_endpoint")
        self.s3_access_key = config.get("s3_access_key")
        self.s3_secret_key = config.get("s3_secret_key")
        self.s3_bucket_name = config.get("s3_bucket_name", "cognee-storage")
        self.s3_use_ssl = config.get("s3_use_ssl", False)
        
        # 数据目录配置（⚠️ 重要：避免数据存储在 venv 目录下）
        # 默认使用项目根目录下的 data/cognee 目录
        self.data_dir = config.get("data_dir", "./data/cognee")
        # 转换为绝对路径
        if not os.path.isabs(self.data_dir):
            # 相对于 backend 目录
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.data_dir = os.path.join(backend_dir, self.data_dir.lstrip("./"))
        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # LLM 配置
        llm_config = config.get("llm", {})
        self.llm_provider = llm_config.get("provider", "openai")
        self.llm_model = llm_config.get("model", "gpt-4o-mini")
        self.llm_api_key = llm_config.get("api_key", "")  # 优先使用环境变量
        self.llm_endpoint = llm_config.get("endpoint", "")  # 优先使用环境变量
        self.llm_max_tokens = llm_config.get("max_tokens", 16384)
        
        # Embedding 配置
        embedding_config = config.get("embedding", {})
        self.embedding_provider = embedding_config.get("provider", "openai")
        self.embedding_api_key = embedding_config.get("api_key", "")  # 优先使用环境变量
        self.embedding_endpoint = embedding_config.get("endpoint", "")  # 优先使用环境变量
        self.embedding_model = embedding_config.get("model", "openai/text-embedding-3-large")
        self.embedding_dimensions = embedding_config.get("dimensions", 3072)
        
        # 数据集和节点集配置
        datasets_config = config.get("datasets", {})
        self.user_dataset_pattern = datasets_config.get("user_pattern", "conversation_{user_id}")
        
        node_sets_config = config.get("node_sets", {})
        self.user_node_set_pattern = node_sets_config.get("user", "user_{user_id}_conversations")
        self.assistant_node_set_pattern = node_sets_config.get("assistant", "assistant_{user_id}_conversations")
        
        # 性能配置
        performance_config = config.get("performance", {})
        self.async_enabled = performance_config.get("async_write", True)  # ✅ 优先使用异步写入
        self.enable_cognify = performance_config.get("enable_cognify", False)
        self.enable_graph_search = performance_config.get("enable_graph_search", False)
        self.batch_size = performance_config.get("batch_size", 10)
        
        # 搜索配置
        search_config = config.get("search", {})
        self.default_top_k = search_config.get("default_top_k", 5)
        self.similarity_threshold = search_config.get("similarity_threshold", 0.7)
        self.use_graph_completion = search_config.get("use_graph_completion", False)
        self.use_combined_context = search_config.get("use_combined_context", True)
        
        self._initialized = False
        
        logger.info(
            "Cognee memory engine initialized",
            extra={
                "database_url": self.database_url.split("@")[-1] if "@" in self.database_url else "***",  # 隐藏密码
                "vector_db_provider": self.vector_db_provider,
                "graph_database_provider": self.graph_database_provider,
                "data_dir": self.data_dir,  # 显示数据目录路径
                "async_enabled": self.async_enabled,
                "enable_cognify": self.enable_cognify,
                "enable_graph_search": self.enable_graph_search
            }
        )
    
    async def initialize(self) -> bool:
        """初始化 Cognee（从配置读取所有参数）"""
        if self._initialized:
            return True
        
        try:
            # ✅ 从配置读取所有环境变量，不硬编码
            # ⚠️ 重要：先设置数据目录，避免数据存储在 venv 目录下
            os.environ["COGNEE_DATA_DIR"] = self.data_dir
            os.environ["DATA_ROOT_DIRECTORY"] = self.data_dir
            
            # 设置 Cognee 环境变量（从配置读取）
            os.environ["DATABASE_URL"] = self.database_url
            os.environ["VECTOR_DB_PROVIDER"] = self.vector_db_provider
            
            if self.graph_database_provider:
                os.environ["GRAPH_DATABASE_PROVIDER"] = self.graph_database_provider
                if self.graph_database_url:
                    os.environ["GRAPH_DATABASE_URL"] = self.graph_database_url
                if self.graph_database_username:
                    os.environ["GRAPH_DATABASE_USERNAME"] = self.graph_database_username
                if self.graph_database_password:
                    os.environ["GRAPH_DATABASE_PASSWORD"] = self.graph_database_password
            
            # Redis 配置（Cognee 内部使用）
            os.environ["REDIS_URL"] = self.redis_url
            
            # S3/MinIO 配置
            if self.s3_endpoint:
                os.environ["S3_ENDPOINT"] = self.s3_endpoint
                os.environ["S3_ACCESS_KEY"] = self.s3_access_key or ""
                os.environ["S3_SECRET_KEY"] = self.s3_secret_key or ""
                os.environ["S3_BUCKET_NAME"] = self.s3_bucket_name
                os.environ["S3_USE_SSL"] = str(self.s3_use_ssl)
            
            # LLM 配置（优先使用环境变量，如果没有则使用配置）
            llm_api_key = os.getenv("LLM_API_KEY", self.llm_api_key)
            if llm_api_key:
                os.environ["LLM_API_KEY"] = llm_api_key
            os.environ["LLM_PROVIDER"] = self.llm_provider
            os.environ["LLM_MODEL"] = self.llm_model
            if self.llm_endpoint:
                llm_endpoint = os.getenv("LLM_ENDPOINT", self.llm_endpoint)
                if llm_endpoint:
                    os.environ["LLM_ENDPOINT"] = llm_endpoint
            os.environ["LLM_MAX_TOKENS"] = str(self.llm_max_tokens)
            
            # Embedding 配置（优先使用环境变量，如果没有则使用配置）
            embedding_api_key = os.getenv("EMBEDDING_API_KEY", self.embedding_api_key)
            if embedding_api_key:
                os.environ["EMBEDDING_API_KEY"] = embedding_api_key
            os.environ["EMBEDDING_PROVIDER"] = self.embedding_provider
            os.environ["EMBEDDING_MODEL"] = self.embedding_model
            if self.embedding_endpoint:
                embedding_endpoint = os.getenv("EMBEDDING_ENDPOINT", self.embedding_endpoint)
                if embedding_endpoint:
                    os.environ["EMBEDDING_ENDPOINT"] = embedding_endpoint
            os.environ["EMBEDDING_DIMENSIONS"] = str(self.embedding_dimensions)
            
            # 初始化 Cognee
            await cognee.setup()
            self._initialized = True
            
            logger.info(
                "Cognee initialized successfully",
                extra={
                    "data_dir": self.data_dir,
                    "database_url": self.database_url.split("@")[-1] if "@" in self.database_url else "***"
                }
            )
            return True
            
        except Exception as e:
            logger.error(f"Cognee initialization failed: {e}", exc_info=True)
            raise
    
    async def add_memory(self, memory: Memory) -> str:
        """添加记忆
        
        注意：异步写入由 MemoryManager 的队列机制处理，
        这里直接写入 Cognee（Worker 会调用此方法）
        """
        return await self._add_to_cognee(memory)
    
    async def _add_to_cognee(self, memory: Memory) -> str:
        """实际写入 Cognee（Worker 中调用）"""
        await self.initialize()
        
        # ✅ 从配置读取数据集和节点集命名模式
        dataset_name = self.user_dataset_pattern.format(user_id=memory.user_id)
        
        if memory.memory_type == MemoryType.USER:
            node_set_pattern = self.user_node_set_pattern
        else:
            node_set_pattern = self.assistant_node_set_pattern
        
        node_set = [node_set_pattern.format(user_id=memory.user_id)]
        
        # 准备元数据
        metadata = {
            "memory_id": memory.id,
            "session_id": memory.session_id,
            "importance": memory.importance,
            "created_at": memory.created_at.isoformat(),
            **memory.metadata
        }
        
        if memory.expires_at:
            metadata["expires_at"] = memory.expires_at.isoformat()
        
        # 添加到 Cognee
        await cognee.add(
            data=memory.content,
            dataset_name=dataset_name,
            node_set=node_set,
            metadata=metadata
        )
        
        # 可选：认知化处理（异步，不阻塞）
        if self.enable_cognify:
            asyncio.create_task(self._cognify_async(dataset_name))
        
        logger.debug(f"Memory added to Cognee: {memory.id}")
        return memory.id
    
    async def _cognify_async(self, dataset_name: str):
        """异步认知化处理（不阻塞主流程）"""
        try:
            await cognee.cognify(dataset_name=dataset_name)
            logger.debug(f"Cognify completed for dataset: {dataset_name}")
        except Exception as e:
            logger.warning(f"Cognify failed for {dataset_name}: {e}", exc_info=False)
    
    async def search_memories(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[MemorySearchResult]:
        """搜索记忆"""
        await self.initialize()
        
        # ✅ 从配置读取参数
        dataset_name = self.user_dataset_pattern.format(user_id=user_id)
        top_k = limit if limit else self.default_top_k
        threshold = similarity_threshold if similarity_threshold else self.similarity_threshold
        
        # 根据配置选择搜索类型
        if self.enable_graph_search and self.use_graph_completion:
            query_type = SearchType.GRAPH_COMPLETION
        else:
            query_type = SearchType.CHUNKS  # 只使用向量搜索
        
        try:
            # 执行搜索
            results = await cognee.search(
                query_text=query,
                datasets=[dataset_name],
                query_type=query_type,
                top_k=top_k,
                use_combined_context=self.use_combined_context
            )
            
            # 转换为标准格式
            search_results = []
            for result in results:
                # 提取相似度（Cognee 返回的结果格式可能不同）
                similarity = 1.0
                if hasattr(result, 'similarity'):
                    similarity = float(result.similarity)
                elif hasattr(result, 'score'):
                    similarity = float(result.score)
                elif hasattr(result, 'distance'):
                    # 距离越小越相似，转换为相似度
                    distance = float(result.distance)
                    similarity = max(0.0, 1.0 - distance)
                
                # 过滤相似度低于阈值的
                if similarity < threshold:
                    continue
                
                # 提取内容
                content = ""
                if hasattr(result, 'content'):
                    content = result.content
                elif hasattr(result, 'text'):
                    content = result.text
                elif isinstance(result, str):
                    content = result
                else:
                    # 尝试从元数据中获取
                    metadata = getattr(result, 'metadata', {})
                    content = metadata.get('content', str(result))
                
                # 提取元数据
                metadata = {}
                if hasattr(result, 'metadata'):
                    metadata = result.metadata if isinstance(result.metadata, dict) else {}
                elif hasattr(result, 'payload'):
                    metadata = result.payload if isinstance(result.payload, dict) else {}
                
                # 构建 Memory 对象
                memory = Memory(
                    id=metadata.get('memory_id', str(uuid.uuid4())),
                    user_id=user_id,
                    session_id=metadata.get('session_id', session_id or ""),
                    memory_type=MemoryType(metadata.get('memory_type', 'user')),
                    content=content,
                    embedding=None,  # 不返回 embedding
                    importance=metadata.get('importance', 0.5),
                    metadata={k: v for k, v in metadata.items() 
                             if k not in ['memory_id', 'session_id', 'memory_type', 'importance', 'created_at', 'expires_at']},
                    created_at=datetime.fromisoformat(metadata['created_at']) 
                        if metadata.get('created_at') else datetime.utcnow(),
                    expires_at=datetime.fromisoformat(metadata['expires_at']) 
                        if metadata.get('expires_at') else None
                )
                
                search_results.append(
                    MemorySearchResult(
                        memory=memory,
                        similarity=similarity,
                        distance=1.0 - similarity if similarity < 1.0 else None
                    )
                )
            
            # 按相似度排序
            search_results.sort(key=lambda x: x.similarity, reverse=True)
            
            logger.debug(
                f"Search completed: {len(search_results)} results",
                extra={"query": query[:50], "user_id": user_id, "top_k": top_k}
            )
            
            return search_results[:top_k]
            
        except Exception as e:
            logger.error(f"Cognee search failed: {e}", exc_info=True)
            return []
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """删除记忆"""
        await self.initialize()
        
        try:
            dataset_name = self.user_dataset_pattern.format(user_id=user_id)
            
            # Cognee 的删除操作
            await cognee.delete(
                dataset_name=dataset_name,
                data_ids=[memory_id]
            )
            
            logger.debug(f"Memory deleted from Cognee: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}", exc_info=True)
            return False
    
    async def delete_session_memories(
        self,
        user_id: str,
        session_id: str
    ) -> int:
        """删除会话的所有记忆"""
        await self.initialize()
        
        try:
            dataset_name = self.user_dataset_pattern.format(user_id=user_id)
            
            # 搜索该会话的所有记忆
            # 注意：Cognee 可能需要通过搜索找到所有相关记忆，然后删除
            # 这里简化处理，实际可能需要根据 Cognee API 调整
            
            # 先搜索获取所有记忆ID
            results = await cognee.search(
                query_text="",  # 空查询获取所有
                datasets=[dataset_name],
                top_k=1000  # 假设会话记忆不超过1000条
            )
            
            # 过滤出该会话的记忆
            memory_ids = []
            for result in results:
                metadata = getattr(result, 'metadata', {})
                if metadata.get('session_id') == session_id:
                    memory_id = metadata.get('memory_id')
                    if memory_id:
                        memory_ids.append(memory_id)
            
            # 批量删除
            if memory_ids:
                await cognee.delete(
                    dataset_name=dataset_name,
                    data_ids=memory_ids
                )
            
            deleted_count = len(memory_ids)
            logger.info(
                f"Deleted {deleted_count} memories for session {session_id}",
                extra={"user_id": user_id, "session_id": session_id, "count": deleted_count}
            )
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete session memories: {e}", exc_info=True)
            return 0
    
    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """获取记忆统计信息"""
        await self.initialize()
        
        try:
            dataset_name = self.user_dataset_pattern.format(user_id=user_id)
            
            # 搜索获取所有记忆（用于统计）
            results = await cognee.search(
                query_text="",  # 空查询获取所有
                datasets=[dataset_name],
                top_k=10000  # 假设用户记忆不超过10000条
            )
            
            # 统计
            user_memories = 0
            assistant_memories = 0
            
            for result in results:
                metadata = getattr(result, 'metadata', {})
                memory_type = metadata.get('memory_type', 'user')
                if memory_type == 'user':
                    user_memories += 1
                elif memory_type == 'assistant':
                    assistant_memories += 1
            
            stats = {
                "user_memories": user_memories,
                "assistant_memories": assistant_memories,
                "total_memories": user_memories + assistant_memories
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}", exc_info=True)
            return {
                "user_memories": 0,
                "assistant_memories": 0,
                "total_memories": 0
            }
    
    async def batch_add_memories(self, memories: List[Memory]) -> List[str]:
        """批量添加记忆
        
        Args:
            memories: 记忆对象列表
            
        Returns:
            List[str]: 成功写入的记忆ID列表
        """
        if not memories:
            return []
        
        try:
            success_ids = []
            
            # 批量写入（Cognee 可能不支持真正的批量，逐个写入）
            for memory in memories:
                try:
                    memory_id = await self._add_to_cognee(memory)
                    success_ids.append(memory_id)
                except Exception as e:
                    logger.error(f"Failed to add memory {memory.id} in batch: {e}", exc_info=True)
                    # 继续处理其他记忆
            
            logger.info(
                f"Batch added {len(success_ids)}/{len(memories)} memories to Cognee",
                extra={"total": len(memories), "success": len(success_ids)}
            )
            
            return success_ids
            
        except Exception as e:
            logger.error(f"Failed to batch add memories: {e}", exc_info=True)
            return []
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self.initialize()
            
            # 尝试获取统计信息（轻量级操作）
            stats = await self.get_memory_stats("health_check_user")
            return True
            
        except Exception as e:
            logger.error(f"Cognee health check failed: {e}", exc_info=True)
            return False

