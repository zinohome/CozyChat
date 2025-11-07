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
from app.utils.logger import logger
from app.utils.config_loader import get_config_loader
from .base import MemoryEngineBase
from .chromadb_engine import ChromaDBMemoryEngine
from .models import Memory, MemorySearchResult, MemoryType


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
            
            if cache_ttl is None:
                cache_ttl = cache_config.get("ttl_seconds", 300)
            if cache_maxsize is None:
                cache_maxsize = cache_config.get("max_size", 100)
            
            # 如果引擎未提供，从配置创建
            if engine is None:
                default_engine = memory_config.get("default_engine", "chromadb")
                engine_config = memory_config.get(default_engine, {})
                
                if default_engine == "chromadb":
                    persist_directory = engine_config.get("persist_directory", "./data/chroma")
                    engine = ChromaDBMemoryEngine(persist_directory=persist_directory)
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
        
        self.engine = engine
        self.cache: TTLCache = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl)
        self.save_timeout = save_timeout
        self.search_timeout = search_timeout
        self.pending_saves: List[Memory] = []
        
        logger.info(
            "Memory manager initialized",
            extra={
                "engine": self.engine.engine_name,
                "cache_ttl": cache_ttl,
                "cache_maxsize": cache_maxsize,
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
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        async_save: bool = True
    ) -> str:
        """添加记忆
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            content: 记忆内容
            memory_type: 记忆类型
            importance: 重要性分数
            metadata: 额外元数据
            async_save: 是否异步保存
            
        Returns:
            str: 记忆ID
        """
        # 创建Memory对象
        memory = Memory(
            id=f"mem-{uuid.uuid4().hex}",
            user_id=user_id,
            session_id=session_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
            metadata=metadata or {}
        )
        
        if async_save:
            # 异步保存：添加到待保存队列
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

