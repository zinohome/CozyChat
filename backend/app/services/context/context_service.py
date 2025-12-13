"""
上下文服务

统一协调各个子服务，构建完整的上下文
"""

# 标准库
import asyncio
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.core.personality.models import Personality
    from app.engines.memory.manager import MemoryManager
    from sqlalchemy.ext.asyncio import AsyncSession

# 本地库
from app.config.config import settings
from app.schemas.context import ContextBundle
from app.utils.logger import logger

from .context_assembler import ContextAssembler
from .message_retriever import MessageRetriever
from .memory_retriever import MemoryRetriever
from .summary_loader import SummaryLoader
from .user_profile_loader import UserProfileLoader


class ContextService:
    """上下文服务
    
    统一协调各个子服务，构建完整的上下文
    """
    
    def __init__(
        self,
        db: "AsyncSession",
        memory_manager: "MemoryManager"
    ):
        """初始化ContextService
        
        Args:
            db: 数据库会话（异步）
            memory_manager: 记忆管理器
        """
        self.db = db
        self.memory_manager = memory_manager
        
        # 初始化子服务
        self.message_retriever = MessageRetriever(db)
        self.summary_loader = SummaryLoader(db)
        self.memory_retriever = MemoryRetriever(memory_manager)
        self.user_profile_loader = UserProfileLoader(db)
        self.context_assembler = ContextAssembler()
        
        logger.info("ContextService initialized")
    
    async def build_context(
        self,
        user_id: str,
        session_id: str,
        current_message: str,
        personality_config: "Personality",
        recent_message_count: Optional[int] = None,
        include_memories: bool = True,
        include_summaries: bool = True,
        max_tokens: Optional[int] = None
    ) -> ContextBundle:
        """构建智能上下文
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            current_message: 当前用户消息
            personality_config: 人格配置
            recent_message_count: 保留的最近消息数量
            include_memories: 是否包含长期记忆
            include_summaries: 是否包含历史摘要
            max_tokens: 最大token数
            
        Returns:
            ContextBundle: 构建好的上下文包
        """
        start_time = asyncio.get_event_loop().time()
        
        # 使用配置中的默认值
        # 使用配置适配器获取上下文配置（优先YAML，回退到Settings）
        from app.utils.config_adapter import get_config_adapter
        config_adapter = get_config_adapter()
        context_config = config_adapter.get_context_config()
        
        if recent_message_count is None:
            recent_message_count = context_config.get("recent", {}).get("message_count", settings.context_recent_message_count)
        if max_tokens is None:
            max_tokens = context_config.get("max_tokens", settings.context_max_tokens)
        
        logger.info(
            f"Building context for session {session_id}",
            extra={
                "user_id": user_id,
                "recent_message_count": recent_message_count,
                "include_memories": include_memories,
                "include_summaries": include_summaries
            }
        )
        
        try:
            # 并行获取各个组件（性能优化：使用asyncio.gather并行执行独立任务）
            # 注意：只并行执行真正独立的任务，避免None任务影响性能
            tasks = []
            task_indices = {}  # 记录每个任务的索引，便于后续处理
            
            # 1. 获取最近消息（总是需要）
            tasks.append(
                self.message_retriever.get_recent_messages(session_id, recent_message_count)
            )
            task_indices['recent_messages'] = 0
            
            # 2. 加载历史摘要（如果需要）
            if include_summaries:
                tasks.append(self.summary_loader.load_history_summaries(session_id))
                task_indices['summaries'] = len(tasks) - 1
            else:
                task_indices['summaries'] = None
            
            # 3. 检索记忆（如果需要）
            if include_memories:
                tasks.append(
                    self.memory_retriever.retrieve_memories(
                        user_id=user_id,
                        session_id=session_id,
                        query=current_message,
                        personality_config=personality_config
                    )
                )
                task_indices['memories'] = len(tasks) - 1
            else:
                task_indices['memories'] = None
            
            # 4. 加载用户画像（总是需要）
            tasks.append(self.user_profile_loader.load_user_profile(user_id))
            task_indices['user_profile'] = len(tasks) - 1
            
            # 等待所有任务完成（并行执行，提升性能）
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果（使用task_indices映射，更清晰）
            recent_messages = (
                results[task_indices['recent_messages']]
                if not isinstance(results[task_indices['recent_messages']], Exception)
                else []
            )
            summaries = (
                results[task_indices['summaries']]
                if task_indices['summaries'] is not None
                and not isinstance(results[task_indices['summaries']], Exception)
                and results[task_indices['summaries']] is not None
                else []
            )
            memories = (
                results[task_indices['memories']]
                if task_indices['memories'] is not None
                and not isinstance(results[task_indices['memories']], Exception)
                and results[task_indices['memories']] is not None
                else []
            )
            user_profile = (
                results[task_indices['user_profile']]
                if not isinstance(results[task_indices['user_profile']], Exception)
                else None
            )
            
            # 记录异常（如果有）
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(
                        f"Failed to load context component {i}: {result}",
                        exc_info=True
                    )
            
            # 组装上下文
            context_bundle = self.context_assembler.assemble_context(
                personality_config=personality_config,
                recent_messages=recent_messages,
                summaries=summaries,
                memories=memories,
                user_profile=user_profile,
                max_tokens=max_tokens
            )
            
            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.info(
                f"Context built successfully",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "elapsed_time": round(elapsed_time, 3),
                    "total_tokens": context_bundle.total_tokens,
                    "recent_messages_count": len(recent_messages),
                    "summaries_count": len(summaries),
                    "memories_count": len(context_bundle.retrieved_memories)
                }
            )
            
            return context_bundle
            
        except Exception as e:
            logger.error(
                f"Failed to build context: {e}",
                exc_info=True,
                extra={"session_id": session_id, "user_id": user_id}
            )
            # 降级：返回基本上下文
            return self.context_assembler.build_fallback_context(personality_config)
