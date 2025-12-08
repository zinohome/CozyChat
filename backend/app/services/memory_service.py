"""
记忆服务

统一处理记忆相关的所有操作，包括保存、检索、删除等
"""

# 标准库
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from app.core.personality.models import Personality
    from app.engines.memory.manager import MemoryManager

# 本地库
from app.utils.logger import logger


class MemoryService:
    """记忆服务
    
    统一处理记忆相关的所有操作
    """
    
    def __init__(self, memory_manager: "MemoryManager"):
        """初始化MemoryService
        
        Args:
            memory_manager: 记忆管理器
        """
        self.memory_manager = memory_manager
        logger.info("MemoryService initialized")
    
    async def save_memory(
        self,
        user_id: str,
        session_id: str,
        content: str,
        memory_type: str = "fact",
        importance: float = 0.5
    ) -> Optional[str]:
        """保存记忆
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            content: 记忆内容
            memory_type: 记忆类型（fact/preference/event）
            importance: 重要性分数（0-1）
            
        Returns:
            Optional[str]: 记忆ID，失败返回None
        """
        try:
            from app.engines.memory.models import MemoryType
            
            memory_type_enum = MemoryType(memory_type)
            
            memory_id = await self.memory_manager.add_memory(
                user_id=user_id,
                session_id=session_id,
                content=content,
                memory_type=memory_type_enum,
                importance=importance
            )
            
            logger.info(
                f"Memory saved",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "memory_type": memory_type,
                    "memory_id": memory_id
                }
            )
            
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to save memory: {e}", exc_info=True)
            return None
    
    async def retrieve_memories(
        self,
        user_id: str,
        session_id: str,
        query: str,
        max_results: int = 5,
        similarity_threshold: float = 0.3,
        timeout: float = 0.5,
        personality_config: Optional["Personality"] = None
    ) -> Dict[str, List[Any]]:
        """检索记忆
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            query: 查询文本
            max_results: 最大结果数
            similarity_threshold: 相似度阈值
            timeout: 超时时间（秒）
            personality_config: 人格配置（可选，用于获取配置参数）
            
        Returns:
            Dict[str, List[Any]]: 检索结果 {"user_memories": [], "ai_memories": []}
        """
        # 从人格配置中获取参数（如果提供）
        if personality_config and hasattr(personality_config, 'memory') and hasattr(personality_config.memory, 'retrieval'):
            similarity_threshold = personality_config.memory.retrieval.similarity_threshold
            max_results = personality_config.memory.retrieval.max_results
            timeout = personality_config.memory.retrieval.timeout_seconds
        
        try:
            results = await self.memory_manager.retrieve_memories(
                user_id=user_id,
                session_id=session_id,
                query=query,
                max_results=max_results,
                include_user_memory=True,
                include_ai_memory=True,
                timeout=timeout,
                similarity_threshold=similarity_threshold
            )
            
            logger.debug(
                f"Memories retrieved",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "query": query[:50],
                    "user_memories_count": len(results.get("user_memories", [])),
                    "ai_memories_count": len(results.get("ai_memories", []))
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}", exc_info=True)
            return {"user_memories": [], "ai_memories": []}
    
    async def delete_memory(
        self,
        memory_id: str,
        user_id: str
    ) -> bool:
        """删除记忆
        
        Args:
            memory_id: 记忆ID
            user_id: 用户ID（用于权限验证）
            
        Returns:
            bool: 是否成功删除
        """
        try:
            success = await self.memory_manager.delete_memory(
                memory_id=memory_id,
                user_id=user_id
            )
            
            if success:
                logger.info(
                    f"Memory deleted",
                    extra={"memory_id": memory_id, "user_id": user_id}
                )
            else:
                logger.warning(
                    f"Memory deletion failed or not found",
                    extra={"memory_id": memory_id, "user_id": user_id}
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}", exc_info=True)
            return False
    
    async def list_memories(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """列出记忆
        
        Args:
            user_id: 用户ID
            session_id: 会话ID（可选，用于过滤）
            memory_type: 记忆类型（可选，用于过滤）
            limit: 最大返回数量
            
        Returns:
            List[Any]: 记忆列表
        """
        try:
            memories = await self.memory_manager.list_memories(
                user_id=user_id,
                session_id=session_id,
                memory_type=memory_type,
                limit=limit
            )
            
            logger.debug(
                f"Memories listed",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "memory_type": memory_type,
                    "count": len(memories)
                }
            )
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to list memories: {e}", exc_info=True)
            return []
