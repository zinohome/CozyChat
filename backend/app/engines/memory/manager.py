"""
记忆管理器

提供缓存、异步保存等高级功能
"""

# 标准库
import asyncio
import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# 第三方库
from cachetools import TTLCache

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from app.utils.config_loader import get_config_loader
from .base import MemoryEngineBase
from .chromadb_engine import ChromaDBMemoryEngine
from .qdrant_engine import QdrantMemoryEngine
from .models import Memory, MemorySearchResult, MemoryType
from .importance_scorer import ImportanceScorer
from .deduplicator import MemoryDeduplicator
from .eviction_policy import EvictionPolicy
from .queue import MemoryQueue
from .jobs import MemoryWriteJob, MemoryWriteJobStatus


# ===== 全局单例 =====
_global_memory_manager: Optional["MemoryManager"] = None


def get_memory_manager() -> "MemoryManager":
    """获取全局MemoryManager单例
    
    Returns:
        MemoryManager: 全局内存管理器实例
    """
    global _global_memory_manager
    if _global_memory_manager is None:
        _global_memory_manager = MemoryManager()
        logger.info("Global MemoryManager initialized")
    return _global_memory_manager


class MemoryManager:
    """记忆管理器
    
    提供记忆的缓存、异步保存、批量操作等高级功能
    
    Attributes:
        engine: 记忆引擎
        cache: TTL缓存
        save_timeout: 保存超时时间（秒）
        search_timeout: 搜索超时时间（秒）
        pending_saves: 待保存的记忆队列
    """
    
    def __init__(
        self,
        engine: Optional[MemoryEngineBase] = None,
        cache_ttl: Optional[int] = None,
        cache_maxsize: Optional[int] = None,
        save_timeout: float = 1.0,
        search_timeout: float = 0.5
    ):
        """初始化记忆管理器
        
        Args:
            engine: 记忆引擎（如果不提供则使用默认ChromaDB）
            cache_ttl: 缓存过期时间（秒），如果为None则从YAML配置加载
            cache_maxsize: 缓存最大条目数，如果为None则从YAML配置加载
            save_timeout: 保存操作超时时间（秒）
            search_timeout: 搜索操作超时时间（秒）
        """
        # 从YAML配置加载记忆配置
        try:
            config_loader = get_config_loader()
            memory_config = config_loader.load_memory_config()
            cache_config = memory_config.get("cache", {})
            cross_session_config = memory_config.get("cross_session_memory", {})
            
            if cache_ttl is None:
                cache_ttl = cache_config.get("ttl_seconds", 300)
            if cache_maxsize is None:
                cache_maxsize = cache_config.get("max_size", 100)
            
            # 跨Session记忆配置
            self.cross_session_enabled = cross_session_config.get("enabled", False)
            
            # 如果引擎未提供，从配置创建
            if engine is None:
                default_engine = memory_config.get("default_engine", "chromadb")
                engine_config = memory_config.get(default_engine, {})
                
                if default_engine == "chromadb":
                    # ChromaDBMemoryEngine 接受 config 字典，不是 persist_directory 关键字参数
                    engine = ChromaDBMemoryEngine(config=engine_config)
                elif default_engine == "qdrant":
                    # Qdrant引擎
                    engine = QdrantMemoryEngine(config=engine_config)
                else:
                    # 其他引擎待实现
                    logger.warning(f"Engine {default_engine} not implemented, using ChromaDB")
                    engine = ChromaDBMemoryEngine()
            
        except Exception as e:
            # 如果YAML配置加载失败，使用默认值
            logger.warning(
                f"Failed to load memory config from YAML, using defaults: {e}",
                exc_info=False
            )
            
            if cache_ttl is None:
                cache_ttl = 300
            if cache_maxsize is None:
                cache_maxsize = 100
            if engine is None:
                engine = ChromaDBMemoryEngine()
            
            # 跨Session记忆配置（默认关闭）
            self.cross_session_enabled = False
        
        self.engine = engine
        self.cache: TTLCache = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl)
        self.save_timeout = save_timeout
        self.search_timeout = search_timeout
        self.pending_saves: List[Memory] = []
        
        # 异步写入配置
        self.async_write_enabled = settings.memory_async_write
        self.queue: Optional[MemoryQueue] = None
        if self.async_write_enabled:
            try:
                self.queue = MemoryQueue()
                logger.info("Memory queue initialized for async writes")
            except Exception as e:
                logger.warning(f"Failed to initialize memory queue, falling back to sync writes: {e}")
                self.async_write_enabled = False
        
        # 初始化智能覆盖组件
        try:
            importance_config = memory_config.get("importance", {})
            scoring_config = importance_config.get("scoring", {})
            self.importance_scorer = ImportanceScorer(
                config=scoring_config.get("default", {})
            )
            self.deduplicator = MemoryDeduplicator(
                engine=engine,
                similarity_threshold=0.95
            )
            self.eviction_policy = EvictionPolicy(
                engine=engine,
                config=importance_config.get("eviction", {})
            )
            self.smart_coverage_enabled = importance_config.get("scoring", {}).get("enabled", True)
        except Exception as e:
            logger.warning(
                f"Failed to initialize smart coverage components: {e}",
                exc_info=True
            )
            # 使用默认配置
            self.importance_scorer = ImportanceScorer()
            self.deduplicator = MemoryDeduplicator(engine=engine)
            self.eviction_policy = EvictionPolicy(engine=engine)
            self.smart_coverage_enabled = False
        
        logger.info(
            "Memory manager initialized",
            extra={
                "engine": self.engine.engine_name,
                "cache_ttl": cache_ttl,
                "cache_maxsize": cache_maxsize,
                "cross_session_enabled": self.cross_session_enabled,
                "smart_coverage_enabled": self.smart_coverage_enabled,
                "async_write_enabled": self.async_write_enabled,
                "config_source": "yaml"
            }
        )
    
    def _build_cache_key(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str],
        memory_type: Optional[MemoryType]
    ) -> str:
        """构建缓存键
        
        Args:
            query: 查询文本
            user_id: 用户ID
            session_id: 会话ID
            memory_type: 记忆类型
            
        Returns:
            str: 缓存键
        """
        key_parts = [user_id, query, session_id or "none"]
        if memory_type:
            key_parts.append(memory_type.value)
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def add_memory(
        self,
        user_id: str,
        session_id: str,
        content: str,
        memory_type: MemoryType,
        importance: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        async_save: bool = True,
        auto_calculate_importance: bool = True,
        enable_deduplication: bool = True
    ) -> str:
        """添加记忆
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            content: 记忆内容
            memory_type: 记忆类型
            importance: 重要性分数（如果为None且auto_calculate_importance=True，则自动计算）
            metadata: 额外元数据
            async_save: 是否异步保存
            auto_calculate_importance: 是否自动计算重要性
            enable_deduplication: 是否启用去重
            
        Returns:
            str: 记忆ID
        """
        metadata = metadata or {}
        created_at = datetime.utcnow()
        
        # 自动计算重要性（如果启用且未提供）
        if importance is None and auto_calculate_importance and self.smart_coverage_enabled:
            try:
                importance = self.importance_scorer.calculate_importance(
                    content=content,
                    metadata=metadata,
                    user_id=user_id,
                    session_id=session_id,
                    created_at=created_at
                )
                logger.debug(
                    f"Auto-calculated importance: {importance}",
                    extra={"user_id": user_id, "content_length": len(content)}
                )
            except Exception as e:
                logger.warning(f"Failed to calculate importance: {e}", exc_info=True)
                importance = 0.5  # 默认值
        
        # 如果仍未设置，使用默认值
        if importance is None:
            importance = 0.5
        
        # 创建Memory对象
        memory = Memory(
            id=f"mem-{uuid.uuid4().hex}",
            user_id=user_id,
            session_id=session_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
            metadata=metadata,
            created_at=created_at
        )
        
        # 智能去重（如果启用）- 检查是否有重复，但不直接保存
        if enable_deduplication and self.smart_coverage_enabled:
            try:
                duplicates = await self.deduplicator.find_duplicates(memory)
                if duplicates:
                    # 有重复，合并记忆
                    all_memories = [memory] + duplicates
                    memory = await self.deduplicator.merge_memories(all_memories)
                    # 删除重复的记忆
                    for dup in duplicates:
                        try:
                            await self.engine.delete_memory(dup.id, dup.user_id)
                            logger.debug(f"Deleted duplicate memory: {dup.id}")
                        except Exception as e:
                            logger.warning(f"Failed to delete duplicate memory {dup.id}: {e}")
                    logger.debug(f"Memory deduplication completed: {memory.id}")
            except Exception as e:
                logger.warning(f"Deduplication failed, saving directly: {e}", exc_info=True)
                # 去重失败，继续正常保存流程
        
        if async_save:
            # 检查是否启用了队列异步写入
            if self.async_write_enabled and self.queue:
                # 使用队列异步写入
                job = MemoryWriteJob(
                    job_id=f"job-{uuid.uuid4().hex[:8]}",
                    memory_id=memory.id,
                    user_id=user_id,
                    session_id=session_id,
                    role=memory_type.value,
                    content=content,
                    importance=importance,
                    metadata=metadata,
                    created_at=created_at,
                    source="chat",
                    status=MemoryWriteJobStatus.PENDING
                )
                
                await self.queue.push(job)
                logger.debug(f"Memory job pushed to queue: {memory.id}")
                return memory.id
            else:
                # 异步保存：添加到待保存队列（旧方法）
                self.pending_saves.append(memory)
                logger.debug(f"Memory queued for async save: {memory.id}")
                
                # 触发后台保存
                asyncio.create_task(self._flush_pending_saves())
                
                return memory.id
        else:
            # 同步保存
            try:
                memory_id = await asyncio.wait_for(
                    self.engine.add_memory(memory),
                    timeout=self.save_timeout
                )
                logger.info(f"Memory saved synchronously: {memory_id}")
                return memory_id
            except asyncio.TimeoutError:
                logger.warning(f"Memory save timeout, falling back to async")
                
                # 如果启用了队列，推入队列
                if self.async_write_enabled and self.queue:
                    job = MemoryWriteJob(
                        job_id=f"job-{uuid.uuid4().hex[:8]}",
                        memory_id=memory.id,
                        user_id=user_id,
                        session_id=session_id,
                        role=memory_type.value,
                        content=content,
                        importance=importance,
                        metadata=metadata,
                        created_at=created_at,
                        source="chat",
                        status=MemoryWriteJobStatus.PENDING
                    )
                    await self.queue.push(job)
                else:
                    self.pending_saves.append(memory)
                    asyncio.create_task(self._flush_pending_saves())
                
                return memory.id
            except Exception as e:
                logger.error(f"Failed to save memory: {e}", exc_info=True)
                raise
    
    async def _flush_pending_saves(self):
        """刷新待保存的记忆队列"""
        if not self.pending_saves:
            return
        
        # 获取当前队列并清空
        memories_to_save = self.pending_saves.copy()
        self.pending_saves.clear()
        
        logger.debug(f"Flushing {len(memories_to_save)} pending memories")
        
        # 批量保存
        for memory in memories_to_save:
            try:
                await self.engine.add_memory(memory)
            except Exception as e:
                logger.error(f"Failed to save memory {memory.id}: {e}")
                # 失败的记忆重新加入队列
                self.pending_saves.append(memory)
    
    async def search_memories(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        use_cache: bool = True
    ) -> List[MemorySearchResult]:
        """搜索相关记忆
        
        Args:
            query: 查询文本
            user_id: 用户ID
            session_id: 会话ID
            memory_type: 记忆类型
            limit: 返回结果数量限制
            similarity_threshold: 相似度阈值
            use_cache: 是否使用缓存
            
        Returns:
            List[MemorySearchResult]: 搜索结果列表
        """
        # 检查缓存
        if use_cache:
            cache_key = self._build_cache_key(query, user_id, session_id, memory_type)
            if cache_key in self.cache:
                logger.debug(f"Memory search cache hit: {cache_key}")
                return self.cache[cache_key]
        
        # 执行搜索（带超时）
        try:
            results = await asyncio.wait_for(
                self.engine.search_memories(
                    query=query,
                    user_id=user_id,
                    session_id=session_id,
                    memory_type=memory_type,
                    limit=limit,
                    similarity_threshold=similarity_threshold
                ),
                timeout=self.search_timeout
            )
            
            # 更新缓存
            if use_cache:
                self.cache[cache_key] = results
            
            logger.info(
                "Memory search completed",
                extra={
                    "user_id": user_id,
                    "results_count": len(results),
                    "cache_hit": False
                }
            )
            
            return results
            
        except asyncio.TimeoutError:
            logger.warning(
                f"Memory search timeout after {self.search_timeout}s for user {user_id}"
            )
            return []
        except Exception as e:
            logger.error(f"Memory search failed: {e}", exc_info=True)
            return []
    
    async def add_conversation_turn(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        assistant_message: str,
        importance: float = 0.5,
        async_save: bool = True
    ) -> Dict[str, str]:
        """添加一轮对话（用户消息和AI消息）
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            user_message: 用户消息
            assistant_message: AI消息
            importance: 重要性分数
            async_save: 是否异步保存
            
        Returns:
            Dict[str, str]: 包含user_memory_id和assistant_memory_id的字典
        """
        user_memory_id = await self.add_memory(
            user_id=user_id,
            session_id=session_id,
            content=user_message,
            memory_type=MemoryType.USER,
            importance=importance,
            async_save=async_save
        )
        
        assistant_memory_id = await self.add_memory(
            user_id=user_id,
            session_id=session_id,
            content=assistant_message,
            memory_type=MemoryType.ASSISTANT,
            importance=importance,
            async_save=async_save
        )
        
        return {
            "user_memory_id": user_memory_id,
            "assistant_memory_id": assistant_memory_id
        }
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """删除记忆
        
        Args:
            memory_id: 记忆ID
            user_id: 用户ID
            
        Returns:
            bool: 是否删除成功
        """
        # 清除相关缓存
        self.cache.clear()
        
        return await self.engine.delete_memory(memory_id, user_id)
    
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
        # 清除相关缓存
        self.cache.clear()
        
        return await self.engine.delete_session_memories(user_id, session_id)
    
    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """获取记忆统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 统计信息
        """
        stats = await self.engine.get_memory_stats(user_id)
        stats["cache_size"] = len(self.cache)
        stats["pending_saves"] = len(self.pending_saves)
        return stats
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 管理器是否健康
        """
        return await self.engine.health_check()
    
    async def evict_low_importance_memories(
        self,
        user_id: str,
        memory_type: Optional[MemoryType] = None
    ) -> int:
        """淘汰低重要性记忆
        
        Args:
            user_id: 用户ID
            memory_type: 记忆类型（可选）
            
        Returns:
            int: 淘汰的记忆数量
        """
        if not self.smart_coverage_enabled:
            return 0
        
        try:
            return await self.eviction_policy.evict_memories(user_id, memory_type)
        except Exception as e:
            logger.error(f"Failed to evict memories: {e}", exc_info=True)
            return 0
    
    async def retrieve_memories(
        self,
        user_id: str,
        session_id: str,
        query: str,
        max_results: int = 5,
        include_user_memory: bool = True,
        include_ai_memory: bool = True,
        timeout: float = 0.5,
        similarity_threshold: float = 0.7
    ) -> Dict[str, List[MemorySearchResult]]:
        """检索相关记忆（用于orchestrator）
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            query: 查询文本
            max_results: 每种类型记忆的最大结果数
            include_user_memory: 是否包含用户记忆
            include_ai_memory: 是否包含AI记忆
            timeout: 搜索超时时间（秒）
            similarity_threshold: 相似度阈值
            
        Returns:
            Dict[str, List[MemorySearchResult]]: 包含user_memories和ai_memories的字典
        """
        user_memories: List[MemorySearchResult] = []
        ai_memories: List[MemorySearchResult] = []
        
        # 根据配置决定是否使用session_id过滤
        # 如果启用跨Session记忆，则不传递session_id，检索所有Session的记忆
        search_session_id: Optional[str] = None if self.cross_session_enabled else session_id
        
        # 检查是否为hybrid模式
        storage_mode = getattr(self.engine, 'storage_mode', 'dual')
        use_hybrid = (storage_mode == "hybrid" and 
                     include_user_memory and 
                     include_ai_memory)
        
        logger.info(
            f"Retrieving memories",
            extra={
                "user_id": user_id,
                "session_id": session_id,
                "query": query,
                "cross_session_enabled": self.cross_session_enabled,
                "search_session_id": search_session_id,
                "similarity_threshold": similarity_threshold,
                "max_results": max_results,
                "storage_mode": storage_mode,
                "use_hybrid": use_hybrid
            }
        )
        
        # 在hybrid模式下，使用单次检索mixed collection，然后分类
        if use_hybrid:
            try:
                mixed_results = await asyncio.wait_for(
                    self.search_memories(
                        query=query,
                        user_id=user_id,
                        session_id=search_session_id,
                        memory_type=None,  # 不指定类型，将使用mixed collection
                        limit=max_results * 2,  # 获取更多结果以便分类
                        similarity_threshold=similarity_threshold,
                        use_cache=True
                    ),
                    timeout=timeout
                )
                
                # 按memory_type分类结果
                for result in mixed_results:
                    if result.memory.memory_type == MemoryType.USER:
                        if len(user_memories) < max_results:
                            user_memories.append(result)
                    elif result.memory.memory_type == MemoryType.ASSISTANT:
                        if len(ai_memories) < max_results:
                            ai_memories.append(result)
                
                # 记录混合检索结果
                logger.info(
                    f"Retrieved memories from mixed collection",
                    extra={
                        "user_id": user_id,
                        "query": query,
                        "total_results": len(mixed_results),
                        "user_count": len(user_memories),
                        "ai_count": len(ai_memories),
                        "similarity_threshold": similarity_threshold
                    }
                )
            except asyncio.TimeoutError:
                logger.warning(f"Mixed memory search timeout after {timeout}s")
            except Exception as e:
                logger.error(f"Failed to retrieve mixed memories: {e}", exc_info=True)
        else:
            # dual/unified模式，分别检索user和assistant记忆
            # 搜索用户记忆
            if include_user_memory:
                try:
                    user_results = await asyncio.wait_for(
                        self.search_memories(
                            query=query,
                            user_id=user_id,
                            session_id=search_session_id,
                            memory_type=MemoryType.USER,
                            limit=max_results,
                            similarity_threshold=similarity_threshold,
                            use_cache=True
                        ),
                        timeout=timeout
                    )
                    user_memories = user_results
                    # 记录检索到的记忆内容（用于调试）- 显示所有记忆及其相似度
                    if user_memories:
                        logger.info(
                            f"Retrieved user memories (all results with similarity scores)",
                            extra={
                                "user_id": user_id,
                                "query": query,
                                "count": len(user_memories),
                                "similarity_threshold": similarity_threshold,
                                "memories": [
                                    {
                                        "content": mem.memory.content[:100],
                                        "similarity": round(mem.similarity, 4),
                                        "memory_id": mem.memory.id,
                                        "session_id": mem.memory.session_id
                                    }
                                    for mem in user_memories
                                ]
                            }
                        )
                    else:
                        logger.warning(
                            f"No user memories retrieved",
                            extra={
                                "user_id": user_id,
                                "query": query,
                                "similarity_threshold": similarity_threshold,
                                "search_session_id": search_session_id
                            }
                        )
                except asyncio.TimeoutError:
                    logger.warning(f"User memory search timeout after {timeout}s")
                except Exception as e:
                    logger.error(f"Failed to retrieve user memories: {e}", exc_info=True)
            
            # 搜索AI记忆
            if include_ai_memory:
                try:
                    ai_results = await asyncio.wait_for(
                        self.search_memories(
                            query=query,
                            user_id=user_id,
                            session_id=search_session_id,
                            memory_type=MemoryType.ASSISTANT,
                            limit=max_results,
                            similarity_threshold=similarity_threshold,
                            use_cache=True
                        ),
                        timeout=timeout
                    )
                    ai_memories = ai_results
                    # 记录检索到的记忆内容（用于调试）
                    if ai_memories:
                        logger.debug(
                            f"Retrieved AI memories",
                            extra={
                                "user_id": user_id,
                                "query": query,
                                "count": len(ai_memories),
                                "memories": [mem.memory.content[:50] for mem in ai_memories[:3]]  # 只记录前3条的前50个字符
                            }
                        )
                except asyncio.TimeoutError:
                    logger.warning(f"AI memory search timeout after {timeout}s")
                except Exception as e:
                    logger.error(f"Failed to retrieve AI memories: {e}", exc_info=True)
        
        return {
            "user_memories": user_memories,
            "ai_memories": ai_memories
        }

