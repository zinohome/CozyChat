"""
记忆去重器

检测并合并相似记忆，避免重复存储
"""

# 标准库
from typing import List, Optional
from datetime import datetime, timedelta

# 本地库
from app.utils.logger import logger
from .models import Memory, MemoryType, MemorySearchResult
from .base import MemoryEngineBase


class MemoryDeduplicator:
    """记忆去重器
    
    检测相似记忆并合并，保留重要性更高的记忆
    """
    
    def __init__(
        self,
        engine: MemoryEngineBase,
        similarity_threshold: float = 0.95
    ):
        """初始化去重器
        
        Args:
            engine: 记忆引擎（用于搜索相似记忆）
            similarity_threshold: 相似度阈值（超过此值认为是重复）
        """
        self.engine = engine
        self.similarity_threshold = similarity_threshold
        
        logger.debug(
            "Memory deduplicator initialized",
            extra={"similarity_threshold": similarity_threshold}
        )
    
    async def find_duplicates(
        self,
        memory: Memory,
        limit: int = 10
    ) -> List[Memory]:
        """查找相似记忆
        
        使用向量相似度搜索查找可能重复的记忆
        
        Args:
            memory: 要检查的记忆
            limit: 最多返回的相似记忆数量
            
        Returns:
            List[Memory]: 相似记忆列表（按相似度降序）
        """
        try:
            # 使用记忆内容作为查询文本
            results = await self.engine.search_memories(
                query=memory.content,
                user_id=memory.user_id,
                session_id=None,  # 跨Session搜索
                memory_type=memory.memory_type,
                limit=limit,
                similarity_threshold=self.similarity_threshold
            )
            
            # 过滤掉自己
            duplicates = [
                result.memory
                for result in results
                if result.memory.id != memory.id
                and result.similarity >= self.similarity_threshold
            ]
            
            logger.info(
                f"Found {len(duplicates)} duplicate memories",
                extra={
                    "memory_id": memory.id,
                    "user_id": memory.user_id,
                    "duplicate_count": len(duplicates),
                    "similarity_threshold": self.similarity_threshold
                }
            )
            
            return duplicates
            
        except Exception as e:
            logger.error(
                f"Failed to find duplicates: {e}",
                exc_info=True,
                extra={"memory_id": memory.id}
            )
            return []
    
    async def merge_memories(
        self,
        memories: List[Memory]
    ) -> Memory:
        """合并相似记忆
        
        合并策略：
        1. 保留重要性最高的记忆
        2. 合并内容（去重后拼接）
        3. 合并元数据
        4. 更新创建时间为最早的
        
        Args:
            memories: 要合并的记忆列表
            
        Returns:
            Memory: 合并后的记忆
        """
        if not memories:
            raise ValueError("Cannot merge empty memory list")
        
        if len(memories) == 1:
            return memories[0]
        
        # 按重要性排序，保留最重要的
        sorted_memories = sorted(
            memories,
            key=lambda m: m.importance,
            reverse=True
        )
        
        primary_memory = sorted_memories[0]
        other_memories = sorted_memories[1:]
        
        # 合并内容（去重）
        contents = [primary_memory.content]
        for mem in other_memories:
            if mem.content not in contents:
                contents.append(mem.content)
        
        merged_content = "\n".join(contents)
        
        # 合并元数据
        merged_metadata = primary_memory.metadata.copy()
        for mem in other_memories:
            # 合并访问频率
            if "access_count" in mem.metadata:
                merged_metadata["access_count"] = (
                    merged_metadata.get("access_count", 0) +
                    mem.metadata.get("access_count", 0)
                )
            # 合并其他元数据
            for key, value in mem.metadata.items():
                if key not in merged_metadata:
                    merged_metadata[key] = value
        
        # 更新重要性（取最高值）
        merged_importance = max(m.importance for m in memories)
        
        # 更新创建时间（取最早的）
        merged_created_at = min(m.created_at for m in memories)
        
        # 创建合并后的记忆
        merged_memory = Memory(
            id=primary_memory.id,
            user_id=primary_memory.user_id,
            session_id=primary_memory.session_id,
            memory_type=primary_memory.memory_type,
            content=merged_content,
            importance=merged_importance,
            metadata=merged_metadata,
            created_at=merged_created_at,
            expires_at=primary_memory.expires_at
        )
        
        logger.info(
            f"Merged {len(memories)} memories",
            extra={
                "merged_memory_id": merged_memory.id,
                "original_count": len(memories),
                "merged_importance": merged_importance
            }
        )
        
        return merged_memory
    
    async def deduplicate_and_save(
        self,
        memory: Memory,
        engine: MemoryEngineBase
    ) -> Memory:
        """去重并保存
        
        检查是否有重复记忆，如果有则合并，否则直接保存
        
        Args:
            memory: 要保存的记忆
            engine: 记忆引擎
            
        Returns:
            Memory: 保存后的记忆（可能是合并后的）
        """
        # 查找重复
        duplicates = await self.find_duplicates(memory)
        
        if duplicates:
            # 有重复，合并
            all_memories = [memory] + duplicates
            merged_memory = await self.merge_memories(all_memories)
            
            # 删除重复的记忆
            for dup in duplicates:
                try:
                    await engine.delete_memory(dup.id, dup.user_id)
                    logger.debug(f"Deleted duplicate memory: {dup.id}")
                except Exception as e:
                    logger.warning(f"Failed to delete duplicate memory {dup.id}: {e}")
            
            # 更新合并后的记忆
            await engine.add_memory(merged_memory)
            
            return merged_memory
        else:
            # 无重复，直接保存
            await engine.add_memory(memory)
            return memory

