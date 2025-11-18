"""
Qdrant记忆引擎实现

使用Qdrant作为向量数据库存储和检索记忆
"""

# 标准库
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# 第三方库
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from sentence_transformers import SentenceTransformer

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from .base import MemoryEngineBase
from .models import Memory, MemorySearchResult, MemoryType


class QdrantMemoryEngine(MemoryEngineBase):
    """Qdrant记忆引擎实现
    
    将用户记忆和AI记忆分别存储在不同的集合中
    
    Attributes:
        client: Qdrant客户端
        user_collection_name: 用户记忆集合名称
        assistant_collection_name: AI记忆集合名称
        embedding_dimension: 向量维度
    """
    
    # 类级别的模型缓存（所有实例共享）
    _model_cache: Dict[str, SentenceTransformer] = {}
    _model_cache_lock = threading.Lock()
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化Qdrant引擎
        
        Args:
            config: 配置信息（可选）
        """
        super().__init__(
            engine_name="qdrant",
            config=config or {}
        )
        
        # 获取配置
        url = self.config.get("url") or settings.qdrant_url
        api_key = self.config.get("api_key") or settings.qdrant_api_key
        
        if not url:
            raise ValueError("Qdrant URL is required")
        
        # 使用全局QdrantClient单例，避免重复创建连接
        try:
            from app.engines.memory.qdrant_client_manager import get_qdrant_client
            self.client = get_qdrant_client()
            logger.debug(
                "Using global QdrantClient singleton",
                extra={"url": url}
            )
        except Exception as e:
            # 如果全局客户端未初始化，则创建新的（向后兼容）
            logger.warning(
                f"Global QdrantClient not available, creating new client: {e}",
                exc_info=False
            )
            if api_key:
                self.client = QdrantClient(url=url, api_key=api_key)
            else:
                self.client = QdrantClient(url=url)
        
        # 集合配置
        collection_prefix = self.config.get("collection_prefix", "cozychat_")
        self.user_collection_name = f"{collection_prefix}user_memories"
        self.assistant_collection_name = f"{collection_prefix}assistant_memories"
        self.mixed_collection_name = f"{collection_prefix}mixed_memories"
        
        # 存储模式配置 (hybrid/dual/unified)
        self.storage_mode = settings.memory_storage_mode
        
        # 向量配置
        embedding_config = self.config.get("embedding", {})
        self.embedding_dimension = embedding_config.get("dimension", 384)
        
        # 创建集合
        self._ensure_collections()
        
        logger.info(
            "Qdrant memory engine initialized",
            extra={
                "url": url,
                "user_collection": self.user_collection_name,
                "assistant_collection": self.assistant_collection_name,
                "mixed_collection": self.mixed_collection_name,
                "storage_mode": self.storage_mode,
                "embedding_dimension": self.embedding_dimension
            }
        )
    
    def _convert_to_qdrant_id(self, memory_id: str) -> str:
        """将记忆ID转换为Qdrant兼容的UUID格式
        
        Qdrant只接受标准UUID格式（xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx）
        或无符号整数。我们的ID格式是 mem-{hex}，需要转换。
        
        Args:
            memory_id: 原始记忆ID（格式：mem-{hex}）
            
        Returns:
            str: 标准UUID格式的字符串
        """
        # 如果已经是标准UUID格式，直接返回
        try:
            uuid.UUID(memory_id)
            return memory_id
        except ValueError:
            pass
        
        # 如果是 mem-{hex} 格式，提取hex部分并转换为标准UUID
        if memory_id.startswith("mem-"):
            hex_str = memory_id[4:]  # 去掉 "mem-" 前缀
            # 将32位hex字符串转换为标准UUID格式
            # 格式：xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
            uuid_str = f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:]}"
            return uuid_str
        
        # 其他格式，尝试作为UUID解析
        try:
            return str(uuid.UUID(memory_id))
        except ValueError:
            # 如果无法转换，生成一个新的UUID
            logger.warning(f"Invalid memory ID format: {memory_id}, generating new UUID")
            return str(uuid.uuid4())
    
    def _convert_from_qdrant_id(self, qdrant_id: str) -> str:
        """将Qdrant的UUID格式ID转换回mem-{hex}格式
        
        为了保持与系统其他部分的兼容性，将UUID格式转换回mem-{hex}格式
        
        Args:
            qdrant_id: Qdrant返回的UUID格式ID
            
        Returns:
            str: mem-{hex}格式的ID
        """
        # 如果是mem-格式，直接返回
        if qdrant_id.startswith("mem-"):
            return qdrant_id
        
        # 如果是UUID格式，转换为mem-{hex}
        try:
            uuid_obj = uuid.UUID(qdrant_id)
            # 将UUID转换为32位hex字符串，然后加上mem-前缀
            hex_str = uuid_obj.hex
            return f"mem-{hex_str}"
        except ValueError:
            # 如果无法解析，直接返回原值
            return qdrant_id
    
    def _ensure_collections(self):
        """确保集合存在，且维度匹配配置"""
        try:
            collections = self.client.get_collections().collections
            collection_info = {c.name: c for c in collections}
            
            # 检查用户记忆集合
            if self.user_collection_name in collection_info:
                # 检查维度是否匹配
                collection = self.client.get_collection(self.user_collection_name)
                vectors_config = collection.config.params.vectors
                # 处理不同的向量配置类型
                if hasattr(vectors_config, 'size'):
                    current_dim = vectors_config.size  # type: ignore
                elif isinstance(vectors_config, dict):
                    # 如果是字典类型，取第一个向量的size
                    first_vector = next(iter(vectors_config.values())) if vectors_config else None
                    current_dim = first_vector.size if first_vector and hasattr(first_vector, 'size') else None  # type: ignore
                else:
                    current_dim = None
                
                if current_dim is None or current_dim != self.embedding_dimension:
                    if current_dim is not None:
                        logger.warning(
                            f"Collection {self.user_collection_name} dimension mismatch: "
                            f"expected {self.embedding_dimension}, got {current_dim}. "
                            "Deleting and recreating..."
                        )
                    self.client.delete_collection(self.user_collection_name)
                    collection_info.pop(self.user_collection_name, None)
            
            if self.user_collection_name not in collection_info:
                self.client.create_collection(
                    collection_name=self.user_collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(
                    f"Created collection: {self.user_collection_name} "
                    f"(dimension: {self.embedding_dimension})"
                )
            
            # 检查AI记忆集合
            if self.assistant_collection_name in collection_info:
                # 检查维度是否匹配
                collection = self.client.get_collection(self.assistant_collection_name)
                vectors_config = collection.config.params.vectors
                # 处理不同的向量配置类型
                if hasattr(vectors_config, 'size'):
                    current_dim = vectors_config.size  # type: ignore
                elif isinstance(vectors_config, dict):
                    # 如果是字典类型，取第一个向量的size
                    first_vector = next(iter(vectors_config.values())) if vectors_config else None
                    current_dim = first_vector.size if first_vector and hasattr(first_vector, 'size') else None  # type: ignore
                else:
                    current_dim = None
                
                if current_dim is None or current_dim != self.embedding_dimension:
                    if current_dim is not None:
                        logger.warning(
                            f"Collection {self.assistant_collection_name} dimension mismatch: "
                            f"expected {self.embedding_dimension}, got {current_dim}. "
                            "Deleting and recreating..."
                        )
                    self.client.delete_collection(self.assistant_collection_name)
                    collection_info.pop(self.assistant_collection_name, None)
            
            if self.assistant_collection_name not in collection_info:
                self.client.create_collection(
                    collection_name=self.assistant_collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(
                    f"Created collection: {self.assistant_collection_name} "
                    f"(dimension: {self.embedding_dimension})"
                )
            
            # 检查混合记忆集合（仅在hybrid模式下创建）
            if self.storage_mode == "hybrid":
                if self.mixed_collection_name in collection_info:
                    # 检查维度是否匹配
                    collection = self.client.get_collection(self.mixed_collection_name)
                    vectors_config = collection.config.params.vectors
                    # 处理不同的向量配置类型
                    if hasattr(vectors_config, 'size'):
                        current_dim = vectors_config.size  # type: ignore
                    elif isinstance(vectors_config, dict):
                        # 如果是字典类型，取第一个向量的size
                        first_vector = next(iter(vectors_config.values())) if vectors_config else None
                        current_dim = first_vector.size if first_vector and hasattr(first_vector, 'size') else None  # type: ignore
                    else:
                        current_dim = None
                    
                    if current_dim is None or current_dim != self.embedding_dimension:
                        if current_dim is not None:
                            logger.warning(
                                f"Collection {self.mixed_collection_name} dimension mismatch: "
                                f"expected {self.embedding_dimension}, got {current_dim}. "
                                "Deleting and recreating..."
                            )
                        self.client.delete_collection(self.mixed_collection_name)
                        collection_info.pop(self.mixed_collection_name, None)
                
                if self.mixed_collection_name not in collection_info:
                    self.client.create_collection(
                        collection_name=self.mixed_collection_name,
                        vectors_config=VectorParams(
                            size=self.embedding_dimension,
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(
                        f"Created mixed collection: {self.mixed_collection_name} "
                        f"(dimension: {self.embedding_dimension})"
                    )
                
        except Exception as e:
            logger.error(f"Failed to ensure collections: {e}", exc_info=True)
            raise
    
    def _get_collection_name(self, memory_type: MemoryType) -> str:
        """根据记忆类型获取对应的集合名称
        
        Args:
            memory_type: 记忆类型
            
        Returns:
            str: 集合名称
            
        Raises:
            ValueError: 如果记忆类型不支持
        """
        if memory_type == MemoryType.USER:
            return self.user_collection_name
        elif memory_type == MemoryType.ASSISTANT:
            return self.assistant_collection_name
        else:
            raise ValueError(f"Unsupported memory type: {memory_type}")
    
    def _get_embedding_model(self, model_name: str) -> SentenceTransformer:
        """获取或创建embedding模型（带缓存）
        
        使用类级别的缓存来避免重复加载模型，提升性能。
        
        Args:
            model_name: 模型名称
            
        Returns:
            SentenceTransformer: 模型实例
        """
        # 先检查缓存（不加锁，快速路径）
        if model_name in QdrantMemoryEngine._model_cache:
            return QdrantMemoryEngine._model_cache[model_name]
        
        # 加锁，确保线程安全
        with QdrantMemoryEngine._model_cache_lock:
            # 双重检查，避免重复加载
            if model_name in QdrantMemoryEngine._model_cache:
                return QdrantMemoryEngine._model_cache[model_name]
            
            # 创建新模型实例
            logger.info(f"Loading embedding model: {model_name} (first time)")
            model = SentenceTransformer(model_name, device='cpu')
            
            # 缓存模型
            QdrantMemoryEngine._model_cache[model_name] = model
            logger.debug(f"Cached embedding model: {model_name}")
            
            return model
    
    async def add_memory(self, memory: Memory) -> str:
        """添加记忆到向量数据库
        
        Args:
            memory: 记忆对象
            
        Returns:
            str: 记忆ID
        """
        try:
            collection_name = self._get_collection_name(memory.memory_type)
            
            # 准备payload（元数据）
            payload = {
                "user_id": memory.user_id,
                "session_id": memory.session_id,
                "content": memory.content,
                "importance": memory.importance,
                "created_at": memory.created_at.timestamp(),
                "memory_type": memory.memory_type.value,
                **memory.metadata
            }
            
            if memory.expires_at:
                payload["expires_at"] = memory.expires_at.timestamp()
            
            # 如果没有提供embedding，使用sentence-transformers生成
            if not memory.embedding:
                embedding_model = self.config.get("embedding", {}).get("model", "all-MiniLM-L6-v2")
                # 使用缓存的模型实例（避免重复加载）
                model = self._get_embedding_model(embedding_model)
                # 使用convert_to_numpy=False返回tensor，然后手动转换
                embedding = model.encode(memory.content, convert_to_numpy=False, convert_to_tensor=True)
                # 将tensor移到CPU并直接转换为list（跳过numpy）
                # 类型检查：embedding 可能是 tensor 或 numpy array
                if hasattr(embedding, 'cpu') and callable(getattr(embedding, 'cpu', None)):
                    embedding_raw = embedding.cpu().tolist()  # type: ignore
                elif hasattr(embedding, 'tolist') and callable(getattr(embedding, 'tolist', None)):
                    embedding_raw = embedding.tolist()  # type: ignore
                elif isinstance(embedding, list):
                    embedding_raw = embedding
                else:
                    embedding_raw = list(embedding)
                
                # 确保类型是 List[float]
                memory.embedding = [float(x) for x in embedding_raw]
            
            # 确保 embedding 是 List[float] 类型
            if memory.embedding:
                embedding_vector: List[float] = [float(x) for x in memory.embedding]
            else:
                raise ValueError("Memory embedding is required")
            
            # 创建point（将ID转换为Qdrant兼容的UUID格式）
            qdrant_id = self._convert_to_qdrant_id(memory.id)
            point = PointStruct(
                id=qdrant_id,
                vector=embedding_vector,
                payload=payload
            )
            
            # 写入原始collection (user/assistant)
            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            # 在hybrid模式下，同时写入mixed collection
            if self.storage_mode == "hybrid":
                self.client.upsert(
                    collection_name=self.mixed_collection_name,
                    points=[point]
                )
                logger.debug(
                    f"Added {memory.memory_type.value} memory to both {collection_name} and {self.mixed_collection_name}",
                    extra={"memory_id": memory.id, "user_id": memory.user_id}
                )
            else:
                logger.debug(
                    f"Added {memory.memory_type.value} memory to {collection_name}",
                    extra={"memory_id": memory.id, "user_id": memory.user_id}
                )
            
            return memory.id
            
        except Exception as e:
            logger.error(f"Failed to add memory: {e}", exc_info=True)
            raise
    
    async def batch_add_memories(self, memories: List[Memory]) -> List[str]:
        """批量添加记忆到向量数据库
        
        使用Qdrant的批量接口，提升写入性能。
        
        Args:
            memories: 记忆对象列表
            
        Returns:
            List[str]: 成功写入的记忆ID列表
        """
        if not memories:
            return []
        
        try:
            # 按collection分组
            collections_map: Dict[str, List[Memory]] = {}
            
            for memory in memories:
                collection_name = self._get_collection_name(memory.memory_type)
                if collection_name not in collections_map:
                    collections_map[collection_name] = []
                collections_map[collection_name].append(memory)
            
            success_ids = []
            
            # 批量写入每个collection
            for collection_name, collection_memories in collections_map.items():
                points = []
                
                for memory in collection_memories:
                    # 准备payload
                    payload = {
                        "user_id": memory.user_id,
                        "session_id": memory.session_id,
                        "content": memory.content,
                        "importance": memory.importance,
                        "created_at": memory.created_at.timestamp(),
                        "memory_type": memory.memory_type.value,
                        **memory.metadata
                    }
                    
                    if memory.expires_at:
                        payload["expires_at"] = memory.expires_at.timestamp()
                    
                    # 生成embedding（如果没有）
                    if not memory.embedding:
                        embedding_model = self.config.get("embedding", {}).get("model", "all-MiniLM-L6-v2")
                        model = self._get_embedding_model(embedding_model)
                        embedding = model.encode(memory.content, convert_to_numpy=False, convert_to_tensor=True)
                        
                        if hasattr(embedding, 'cpu') and callable(getattr(embedding, 'cpu', None)):
                            embedding_raw = embedding.cpu().tolist()  # type: ignore
                        elif hasattr(embedding, 'tolist') and callable(getattr(embedding, 'tolist', None)):
                            embedding_raw = embedding.tolist()  # type: ignore
                        elif isinstance(embedding, list):
                            embedding_raw = embedding
                        else:
                            embedding_raw = list(embedding)
                        
                        memory.embedding = [float(x) for x in embedding_raw]
                    
                    embedding_vector: List[float] = [float(x) for x in memory.embedding]
                    
                    # 创建point
                    qdrant_id = self._convert_to_qdrant_id(memory.id)
                    point = PointStruct(
                        id=qdrant_id,
                        vector=embedding_vector,
                        payload=payload
                    )
                    points.append(point)
                
                # 批量upsert到原collection
                self.client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                
                # 在hybrid模式下，同时写入mixed collection
                if self.storage_mode == "hybrid":
                    self.client.upsert(
                        collection_name=self.mixed_collection_name,
                        points=points
                    )
                
                success_ids.extend([mem.id for mem in collection_memories])
                
                logger.debug(
                    f"Batch added {len(points)} memories to {collection_name}",
                    extra={
                        "collection": collection_name,
                        "count": len(points),
                        "hybrid_mode": self.storage_mode == "hybrid"
                    }
                )
            
            logger.info(
                f"Batch added {len(success_ids)} memories",
                extra={"total_count": len(success_ids)}
            )
            
            return success_ids
            
        except Exception as e:
            logger.error(f"Failed to batch add memories: {e}", exc_info=True)
            raise
    
    async def search_memories(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        use_hybrid_search: bool = False,
        keyword_extraction: Optional[callable] = None
    ) -> List[MemorySearchResult]:
        """搜索相关记忆（支持混合检索：向量搜索 + 关键词搜索）
        
        Args:
            query: 查询文本
            user_id: 用户ID
            session_id: 会话ID（可选）
            memory_type: 记忆类型（可选）
            limit: 返回结果数量限制
            similarity_threshold: 相似度阈值
            use_hybrid_search: 是否使用混合检索（关键词搜索 + 向量搜索）
            keyword_extraction: 关键词提取函数（可选），接收query返回关键词列表
            
        Returns:
            List[MemorySearchResult]: 搜索结果列表
        """
        try:
            results = []
            
            # 生成查询向量
            embedding_model = self.config.get("embedding", {}).get("model", "all-MiniLM-L6-v2")
            # 使用缓存的模型实例（避免重复加载）
            model = self._get_embedding_model(embedding_model)
            # 使用convert_to_numpy=False返回tensor，然后手动转换
            query_embedding = model.encode(query, convert_to_numpy=False, convert_to_tensor=True)
            # 将tensor移到CPU并直接转换为list（跳过numpy）
            # 类型检查：query_embedding 可能是 tensor 或 numpy array
            if hasattr(query_embedding, 'cpu') and callable(getattr(query_embedding, 'cpu', None)):
                query_vector_raw = query_embedding.cpu().tolist()  # type: ignore
            elif hasattr(query_embedding, 'tolist') and callable(getattr(query_embedding, 'tolist', None)):
                query_vector_raw = query_embedding.tolist()  # type: ignore
            elif isinstance(query_embedding, list):
                query_vector_raw = query_embedding
            else:
                query_vector_raw = list(query_embedding)
            
            # 确保类型是 List[float]
            query_vector: List[float] = [float(x) for x in query_vector_raw]
            
            # 确定要搜索的集合
            collections_to_search = []
            
            # 在hybrid模式下，优先使用mixed collection进行搜索
            if self.storage_mode == "hybrid" and not memory_type:
                # 如果没有指定memory_type，直接搜索mixed collection
                collections_to_search.append((
                    self.mixed_collection_name,
                    None  # mixed collection包含所有类型
                ))
            elif memory_type:
                # 指定了memory_type，搜索对应的collection
                collections_to_search.append((
                    self._get_collection_name(memory_type),
                    memory_type
                ))
            else:
                # dual/unified模式，或需要分别搜索
                collections_to_search.append((
                    self.user_collection_name,
                    MemoryType.USER
                ))
                collections_to_search.append((
                    self.assistant_collection_name,
                    MemoryType.ASSISTANT
                ))
            
            # 构建过滤条件
            filter_conditions = [
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                )
            ]
            
            if session_id:
                filter_conditions.append(
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id)
                    )
                )
            
            # 混合检索：提取关键词（在应用层进行过滤）
            # 注意：Qdrant 的 MatchAny 用于精确值匹配，不适合文本内容的模糊匹配
            # 因此采用两步策略：1) 向量搜索获取更多候选 2) 应用层关键词过滤
            keywords = []
            if use_hybrid_search:
                keywords = self._extract_keywords(query, keyword_extraction)
                if keywords:
                    logger.debug(
                        f"Hybrid search: extracted keywords (will filter in application layer)",
                        extra={
                            "query": query[:50],
                            "keywords": keywords,
                            "keyword_count": len(keywords)
                        }
                    )
            
            # 合并所有过滤条件（不包含关键词过滤，在应用层处理）
            all_filter_conditions = filter_conditions.copy()
            
            # 类型转换：将 list[FieldCondition] 转换为 List[Condition]
            from qdrant_client.models import Condition
            query_filter: Optional[Filter] = (
                Filter(must=list(all_filter_conditions)) if all_filter_conditions else None  # type: ignore
            )
            
            # 搜索每个集合
            # 注意：不在这里应用score_threshold，而是获取更多结果后在代码中过滤
            # 这样可以记录所有结果，便于调试
            search_limit = limit * 3  # 获取更多结果，以便在应用阈值后仍有足够的结果
            all_raw_results = []  # 用于记录所有原始结果（用于调试）
            
            for collection_name, mem_type in collections_to_search:
                try:
                    search_results = self.client.search(
                        collection_name=collection_name,
                        query_vector=query_vector,
                        limit=search_limit,  # 获取更多结果
                        query_filter=query_filter
                        # 不在这里应用score_threshold，在代码中应用
                    )
                    
                    # 处理结果
                    for scored_point in search_results:
                        payload = scored_point.payload
                        similarity = scored_point.score
                        
                        # 检查 payload 是否存在
                        if not payload:
                            logger.warning(f"Scored point {scored_point.id} has no payload, skipping")
                            continue
                        
                        # 确定memory_type：从payload获取（mixed collection）或使用指定的类型
                        if mem_type is None:
                            # 从payload中获取memory_type（mixed collection情况）
                            memory_type_str = payload.get("memory_type", "user")
                            actual_mem_type = MemoryType(memory_type_str) if memory_type_str else MemoryType.USER
                        else:
                            actual_mem_type = mem_type
                        
                        # 记录所有原始结果（用于调试）
                        all_raw_results.append({
                            "collection": collection_name,
                            "memory_type": actual_mem_type.value,
                            "similarity": similarity,
                            "content": str(payload.get("content", ""))[:50] if payload else "N/A",
                            "session_id": str(payload.get("session_id", "")) if payload else "N/A"
                        })
                        
                        # 应用相似度阈值
                        if similarity < similarity_threshold:
                            continue
                        
                        # 混合检索：在应用层进行关键词过滤
                        content = str(payload.get("content", ""))
                        if use_hybrid_search and keywords:
                            # 检查内容是否包含任一关键词
                            content_lower = content.lower()
                            has_keyword = any(
                                keyword.lower() in content_lower 
                                for keyword in keywords
                            )
                            if not has_keyword:
                                # 不包含关键词，但相似度足够高时仍保留（降低阈值）
                                # 这样可以平衡关键词匹配和语义相似度
                                if similarity < similarity_threshold * 0.8:  # 降低20%阈值
                                    continue
                        
                        # 将Qdrant返回的UUID格式ID转换回mem-{hex}格式
                        original_id = self._convert_from_qdrant_id(str(scored_point.id))
                        
                        # 构建Memory对象
                        memory = Memory(
                            id=original_id,
                            user_id=str(payload.get("user_id", "")),
                            session_id=str(payload.get("session_id", "")),
                            memory_type=actual_mem_type,
                            content=content,
                            importance=float(payload.get("importance", 0.5)),
                            metadata={k: v for k, v in payload.items() 
                                     if k not in ["user_id", "session_id", "content", 
                                                  "importance", "created_at", "expires_at", "memory_type"]},
                            created_at=datetime.fromtimestamp(float(payload.get("created_at", 0)))
                        )
                        
                        results.append(MemorySearchResult(
                            memory=memory,
                            similarity=similarity,
                            distance=1 - similarity  # 转换为距离
                        ))
                        
                except Exception as e:
                    mem_type_str = mem_type.value if mem_type else "mixed"
                    logger.warning(f"Search failed for {mem_type_str} memories in {collection_name}: {e}")
                    continue
            
            # 记录所有原始结果（用于调试）
            logger.debug(
                f"Qdrant search raw results (before threshold filter)",
                extra={
                    "user_id": user_id,
                    "query": query[:50],
                    "similarity_threshold": similarity_threshold,
                    "total_raw_results": len(all_raw_results),
                    "raw_results": all_raw_results[:20]  # 只记录前20条
                }
            )
            
            # 按相似度排序
            results.sort(key=lambda x: x.similarity, reverse=True)
            
            # 去重：相同内容的记忆只保留相似度最高的一条
            # 这样可以避免返回多条相同内容的记忆，让结果更加多样化
            seen_contents = {}
            deduplicated_results = []
            for result in results:
                content = result.memory.content
                # 如果内容已存在，只保留相似度更高的
                if content in seen_contents:
                    existing_similarity = seen_contents[content].similarity
                    if result.similarity > existing_similarity:
                        # 替换为相似度更高的
                        deduplicated_results.remove(seen_contents[content])
                        deduplicated_results.append(result)
                        seen_contents[content] = result
                else:
                    deduplicated_results.append(result)
                    seen_contents[content] = result
            
            # 重新按相似度排序（因为去重可能改变了顺序）
            deduplicated_results.sort(key=lambda x: x.similarity, reverse=True)
            
            # 限制数量
            results = deduplicated_results[:limit]
            
            logger.debug(
                "Memory search completed",
                extra={
                    "user_id": user_id,
                    "query_length": len(query),
                    "results_count": len(results)
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}", exc_info=True)
            return []
    
    def _extract_keywords(
        self,
        query: str,
        keyword_extraction: Optional[callable] = None
    ) -> List[str]:
        """从查询中提取关键词
        
        Args:
            query: 查询文本
            keyword_extraction: 自定义关键词提取函数（可选）
            
        Returns:
            List[str]: 关键词列表
        """
        if keyword_extraction:
            # 使用自定义提取函数
            try:
                keywords = keyword_extraction(query)
                if isinstance(keywords, list):
                    return keywords
            except Exception as e:
                logger.warning(f"Keyword extraction function failed: {e}")
        
        # 默认：简单提取关键词（中文和英文）
        import re
        
        # 提取中文关键词（2-4个字）
        chinese_keywords = re.findall(r'[\u4e00-\u9fa5]{2,4}', query)
        
        # 提取英文关键词（3个字符以上，排除常见停用词）
        stop_words = {'the', 'is', 'are', 'was', 'were', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        english_keywords = [w for w in words if w not in stop_words]
        
        # 合并并去重
        all_keywords = list(set(chinese_keywords + english_keywords))
        
        # 限制关键词数量（避免过滤条件过于复杂）
        return all_keywords[:5]  # 最多5个关键词
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """删除记忆
        
        Args:
            memory_id: 记忆ID
            user_id: 用户ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 将ID转换为Qdrant兼容的UUID格式
            qdrant_id = self._convert_to_qdrant_id(memory_id)
            
            # 尝试从两个集合中删除
            for collection_name in [self.user_collection_name, self.assistant_collection_name]:
                try:
                    self.client.delete(
                        collection_name=collection_name,
                        points_selector=[qdrant_id]
                    )
                    logger.info(f"Deleted memory {memory_id} (Qdrant ID: {qdrant_id})")
                    return True
                except Exception:
                    continue
            
            logger.warning(f"Memory {memory_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}", exc_info=True)
            return False
    
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
        """
        try:
            deleted_count = 0
            
            # 构建过滤条件
            filter_conditions = Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    ),
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id)
                    )
                ]
            )
            
            # 从两个集合中删除
            for collection_name in [self.user_collection_name, self.assistant_collection_name]:
                try:
                    result = self.client.delete(
                        collection_name=collection_name,
                        points_selector=filter_conditions
                    )
                    # Qdrant返回操作状态
                    if result:
                        deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete from collection {collection_name}: {e}")
                    continue
            
            logger.info(
                f"Deleted session memories",
                extra={"user_id": user_id, "session_id": session_id, "deleted_count": deleted_count}
            )
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete session memories: {e}", exc_info=True)
            return 0
    
    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """获取记忆统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 统计信息
        """
        try:
            stats = {
                "user_id": user_id,
                "user_memories_count": 0,
                "assistant_memories_count": 0,
                "total_memories_count": 0
            }
            
            # 构建过滤条件
            user_filter = Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            )
            
            # 获取用户记忆数量
            try:
                user_results = self.client.scroll(
                    collection_name=self.user_collection_name,
                    scroll_filter=user_filter,
                    limit=1,
                    with_payload=False,
                    with_vectors=False
                )
                # 注意：scroll返回的是(points, next_page_offset)
                # 要获取准确数量，需要使用count API
                collection_info = self.client.get_collection(self.user_collection_name)
                # 这里简化处理，实际应该使用scroll遍历或count API
                stats["user_memories_count"] = len(user_results[0]) if user_results[0] else 0
            except Exception as e:
                logger.warning(f"Failed to get user memories count: {e}")
            
            # 获取AI记忆数量
            try:
                assistant_results = self.client.scroll(
                    collection_name=self.assistant_collection_name,
                    scroll_filter=user_filter,
                    limit=1,
                    with_payload=False,
                    with_vectors=False
                )
                stats["assistant_memories_count"] = len(assistant_results[0]) if assistant_results[0] else 0
            except Exception as e:
                logger.warning(f"Failed to get assistant memories count: {e}")
            
            stats["total_memories_count"] = (
                stats["user_memories_count"] + stats["assistant_memories_count"]
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}", exc_info=True)
            return {"user_id": user_id, "error": str(e)}

