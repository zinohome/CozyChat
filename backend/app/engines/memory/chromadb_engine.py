"""
ChromaDB记忆引擎实现

使用ChromaDB作为向量数据库存储和检索记忆
"""

# 标准库
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# 第三方库
import chromadb
from chromadb import PersistentClient

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from .base import MemoryEngineBase
from .models import Memory, MemorySearchResult, MemoryType


class ChromaDBMemoryEngine(MemoryEngineBase):
    """ChromaDB记忆引擎实现
    
    将用户记忆和AI记忆分别存储在不同的集合中
    
    Attributes:
        client: ChromaDB客户端
        user_collection: 用户记忆集合
        assistant_collection: AI记忆集合
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化ChromaDB引擎
        
        Args:
            config: 配置信息（可选）
        """
        super().__init__(
            engine_name="chromadb",
            config=config or {}
        )
        
        # 初始化ChromaDB客户端（使用新版本API）
        persist_directory = self.config.get(
            "persist_directory",
            settings.chroma_persist_directory
        )
        
        # ChromaDB 1.x 使用 PersistentClient 替代 Client(Settings(...))
        self.client = PersistentClient(path=persist_directory)
        
        # 创建集合（区分用户记忆和AI记忆）
        self.user_collection = self.client.get_or_create_collection(
            name=self.config.get("user_collection_name", "user_memories"),
            metadata={"type": "user"}
        )
        self.assistant_collection = self.client.get_or_create_collection(
            name=self.config.get("assistant_collection_name", "assistant_memories"),
            metadata={"type": "assistant"}
        )
        
        logger.info(
            "ChromaDB memory engine initialized",
            extra={"persist_directory": persist_directory}
        )
    
    def _get_collection(self, memory_type: MemoryType):
        """根据记忆类型获取对应的集合
        
        Args:
            memory_type: 记忆类型
            
        Returns:
            Collection: ChromaDB集合
            
        Raises:
            ValueError: 如果记忆类型不支持
        """
        if memory_type == MemoryType.USER:
            return self.user_collection
        elif memory_type == MemoryType.ASSISTANT:
            return self.assistant_collection
        else:
            raise ValueError(f"Unsupported memory type: {memory_type}")
    
    async def add_memory(self, memory: Memory) -> str:
        """添加记忆到向量数据库
        
        Args:
            memory: 记忆对象
            
        Returns:
            str: 记忆ID
        """
        try:
            collection = self._get_collection(memory.memory_type)
            
            # 准备元数据
            metadata = {
                "user_id": memory.user_id,
                "session_id": memory.session_id,
                "importance": memory.importance,
                "created_at": memory.created_at.timestamp(),
                **memory.metadata
            }
            
            if memory.expires_at:
                metadata["expires_at"] = memory.expires_at.timestamp()
            
            # 添加到集合（ChromaDB会自动生成嵌入）
            collection.add(
                ids=[memory.id],
                documents=[memory.content],
                metadatas=[metadata]
            )
            
            logger.debug(
                f"Added {memory.memory_type.value} memory",
                extra={"memory_id": memory.id, "user_id": memory.user_id}
            )
            
            return memory.id
            
        except Exception as e:
            logger.error(f"Failed to add memory: {e}", exc_info=True)
            raise
    
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
        """
        try:
            results = []
            
            # 确定要搜索的集合
            collections_to_search = []
            if memory_type:
                collections_to_search.append((
                    self._get_collection(memory_type),
                    memory_type
                ))
            else:
                # 搜索两种类型的记忆
                collections_to_search.append((self.user_collection, MemoryType.USER))
                collections_to_search.append((self.assistant_collection, MemoryType.ASSISTANT))
            
            # 构建过滤条件
            where_filter = {"user_id": user_id}
            if session_id:
                where_filter["session_id"] = session_id
            
            # 搜索每个集合
            for collection, mem_type in collections_to_search:
                try:
                    search_results = collection.query(
                        query_texts=[query],
                        n_results=limit,
                        where=where_filter
                    )
                    
                    # 处理结果
                    if search_results["ids"] and search_results["ids"][0]:
                        for i, memory_id in enumerate(search_results["ids"][0]):
                            # 计算相似度（ChromaDB返回距离，需要转换）
                            distance = search_results["distances"][0][i]
                            similarity = 1 - distance  # 简单转换
                            
                            # 过滤低相似度结果
                            if similarity < similarity_threshold:
                                continue
                            
                            # 构建Memory对象
                            metadata = search_results["metadatas"][0][i]
                            memory = Memory(
                                id=memory_id,
                                user_id=metadata["user_id"],
                                session_id=metadata["session_id"],
                                memory_type=mem_type,
                                content=search_results["documents"][0][i],
                                importance=metadata.get("importance", 0.5),
                                metadata={k: v for k, v in metadata.items() 
                                         if k not in ["user_id", "session_id", "importance", "created_at", "expires_at"]},
                                created_at=datetime.fromtimestamp(metadata["created_at"])
                            )
                            
                            results.append(MemorySearchResult(
                                memory=memory,
                                similarity=similarity,
                                distance=distance
                            ))
                            
                except Exception as e:
                    logger.warning(f"Search failed for {mem_type.value} memories: {e}")
                    continue
            
            # 按相似度排序并限制数量
            results.sort(key=lambda x: x.similarity, reverse=True)
            results = results[:limit]
            
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
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """删除记忆
        
        Args:
            memory_id: 记忆ID
            user_id: 用户ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 尝试从两个集合中删除
            for collection in [self.user_collection, self.assistant_collection]:
                try:
                    collection.delete(ids=[memory_id])
                    logger.info(f"Deleted memory {memory_id}")
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
            where_filter = {
                "user_id": user_id,
                "session_id": session_id
            }
            
            # 从两个集合中删除
            for collection in [self.user_collection, self.assistant_collection]:
                try:
                    collection.delete(where=where_filter)
                    # ChromaDB不返回删除数量，假设成功
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete from collection: {e}")
                    continue
            
            logger.info(
                f"Deleted session memories",
                extra={"user_id": user_id, "session_id": session_id}
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
            
            # 获取用户记忆数量
            try:
                user_results = self.user_collection.get(
                    where={"user_id": user_id}
                )
                stats["user_memories_count"] = len(user_results["ids"])
            except Exception:
                pass
            
            # 获取AI记忆数量
            try:
                assistant_results = self.assistant_collection.get(
                    where={"user_id": user_id}
                )
                stats["assistant_memories_count"] = len(assistant_results["ids"])
            except Exception:
                pass
            
            stats["total_memories_count"] = (
                stats["user_memories_count"] + stats["assistant_memories_count"]
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}", exc_info=True)
            return {"user_id": user_id, "error": str(e)}

