"""
智能上下文构建器

负责为LLM对话构建分层、优化的上下文，包含：
- 最近对话原文
- 历史摘要
- 检索到的长期记忆
- 用户画像
"""

# 标准库
import asyncio
from typing import Dict, List, Optional, Any
from uuid import UUID

# 第三方库
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from app.engines.memory.manager import MemoryManager
from app.engines.ai.engine_pool import LLMEnginePool
from app.core.personality.models import Personality
from app.schemas.context import ContextBundle
from app.schemas.message import MessageResponse
from app.models.message import Message
from app.models.session_context import SessionContext
from app.models.user import User


class ContextBuilder:
    """智能上下文构建器
    
    根据分层策略构建最优的LLM输入上下文。
    """
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        engine_pool: LLMEnginePool,
        db: Session
    ):
        """初始化ContextBuilder
        
        Args:
            memory_manager: 记忆管理器
            engine_pool: LLM引擎池
            db: 数据库会话
        """
        self.memory_manager = memory_manager
        self.engine_pool = engine_pool
        self.db = db
        
        logger.info("ContextBuilder initialized")
    
    async def build_context(
        self,
        user_id: str,
        session_id: str,
        current_message: str,
        personality_config: Personality,
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
        if recent_message_count is None:
            recent_message_count = settings.context_recent_message_count
        if max_tokens is None:
            max_tokens = settings.context_max_tokens
        
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
            # 并发执行各个组件
            tasks = [
                self._get_recent_messages(session_id, recent_message_count),
                self._load_history_summaries(session_id) if include_summaries else asyncio.coroutine(lambda: [])(),
                self._retrieve_memories(user_id, session_id, current_message) if include_memories else asyncio.coroutine(lambda: [])(),
                self._load_user_profile(user_id),
            ]
            
            recent_messages, summaries, memories, user_profile = await asyncio.gather(*tasks)
            
            # 组装上下文
            context_bundle = self._assemble_context(
                personality_config=personality_config,
                recent_messages=recent_messages,
                summaries=summaries,
                memories=memories,
                user_profile=user_profile,
                max_tokens=max_tokens
            )
            
            elapsed = asyncio.get_event_loop().time() - start_time
            
            logger.info(
                f"Context built successfully in {elapsed:.3f}s",
                extra={
                    "session_id": session_id,
                    "recent_msg_count": len(recent_messages),
                    "summary_count": len(summaries),
                    "memory_count": len(memories),
                    "estimated_tokens": context_bundle.total_tokens,
                    "elapsed_time": elapsed
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
            return self._build_fallback_context(personality_config)
    
    async def _get_recent_messages(
        self,
        session_id: str,
        count: int
    ) -> List[MessageResponse]:
        """获取最近的消息原文
        
        Args:
            session_id: 会话ID
            count: 消息数量
            
        Returns:
            List[MessageResponse]: 消息列表
        """
        try:
            # 查询数据库获取最近的消息
            stmt = (
                select(Message)
                .where(Message.session_id == UUID(session_id))
                .order_by(desc(Message.created_at))
                .limit(count)
            )
            
            result = self.db.execute(stmt)
            messages = result.scalars().all()
            
            # 转换为响应模型并反转顺序（从旧到新）
            message_responses = [
                MessageResponse(
                    id=msg.id,
                    session_id=msg.session_id,
                    role=msg.role,
                    content=msg.content,
                    tokens=msg.tokens,
                    model=msg.model,
                    created_at=msg.created_at
                )
                for msg in reversed(messages)
            ]
            
            return message_responses
            
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}", exc_info=True)
            return []
    
    async def _load_history_summaries(
        self,
        session_id: str
    ) -> List[str]:
        """加载历史摘要
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[str]: 摘要文本列表
        """
        try:
            # 查询历史摘要
            stmt = (
                select(SessionContext)
                .where(
                    and_(
                        SessionContext.session_id == UUID(session_id),
                        SessionContext.context_type == 'history_summary'
                    )
                )
                .order_by(SessionContext.created_at)
            )
            
            result = self.db.execute(stmt)
            summaries = result.scalars().all()
            
            return [s.content for s in summaries]
            
        except Exception as e:
            logger.error(f"Failed to load history summaries: {e}", exc_info=True)
            return []
    
    async def _retrieve_memories(
        self,
        user_id: str,
        session_id: str,
        query: str
    ) -> List[Any]:
        """检索相关记忆
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            query: 查询文本
            
        Returns:
            List[Memory]: 记忆列表
        """
        try:
            # 调用MemoryManager检索记忆
            memory_results = await self.memory_manager.retrieve_memories(
                user_id=user_id,
                session_id=session_id,
                query=query,
                max_results=5,  # 限制数量
                include_user_memory=True,
                include_ai_memory=True,
                timeout=0.5,
                similarity_threshold=0.7
            )
            
            # 合并用户记忆和AI记忆
            all_memories = []
            all_memories.extend(memory_results.get("user_memories", []))
            all_memories.extend(memory_results.get("ai_memories", []))
            
            # 按重要性排序
            all_memories.sort(key=lambda m: m.score, reverse=True)
            
            return all_memories[:5]  # 只取前5个
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}", exc_info=True)
            return []
    
    async def _load_user_profile(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """加载用户画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict[str, Any]]: 用户画像信息
        """
        try:
            # 查询用户信息
            stmt = select(User).where(User.id == UUID(user_id))
            result = self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # 构建用户画像
            profile = {
                "username": user.username,
                "preferences": user.preferences or {},
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to load user profile: {e}", exc_info=True)
            return None
    
    def _assemble_context(
        self,
        personality_config: Personality,
        recent_messages: List[MessageResponse],
        summaries: List[str],
        memories: List[Any],
        user_profile: Optional[Dict[str, Any]],
        max_tokens: int
    ) -> ContextBundle:
        """组装上下文包
        
        Args:
            personality_config: 人格配置
            recent_messages: 最近消息
            summaries: 历史摘要
            memories: 检索到的记忆
            user_profile: 用户画像
            max_tokens: 最大token数
            
        Returns:
            ContextBundle: 上下文包
        """
        # 构建系统提示词
        system_prompts = []
        
        # 1. 人格定义
        if hasattr(personality_config, 'system_prompt') and personality_config.system_prompt:
            system_prompts.append(personality_config.system_prompt)
        elif hasattr(personality_config, 'description') and personality_config.description:
            system_prompts.append(personality_config.description)
        
        # 2. 用户画像
        if user_profile:
            profile_text = f"用户信息: {user_profile.get('username', '未知')}"
            if user_profile.get('preferences'):
                profile_text += f"，偏好: {user_profile['preferences']}"
            system_prompts.append(profile_text)
        
        # 粗略估算token数
        # 简单按字符数估算：中文约1.5token/字，英文约0.25token/词
        estimated_tokens = sum(len(p) * 1.5 for p in system_prompts)
        estimated_tokens += sum(len(s) * 1.5 for s in summaries)
        estimated_tokens += sum(len(m.content) * 1.5 for m in memories)
        estimated_tokens += sum(len(msg.content) * 1.5 for msg in recent_messages)
        
        return ContextBundle(
            system_prompts=system_prompts,
            recent_messages=recent_messages,
            summarized_history=summaries,
            retrieved_memories=memories,
            user_profile=user_profile,
            total_tokens=int(estimated_tokens),
            metadata={
                "max_tokens": max_tokens,
                "personality_id": personality_config.id if hasattr(personality_config, 'id') else None
            }
        )
    
    def _build_fallback_context(
        self,
        personality_config: Personality
    ) -> ContextBundle:
        """构建降级上下文（当主流程失败时使用）
        
        Args:
            personality_config: 人格配置
            
        Returns:
            ContextBundle: 基本上下文包
        """
        system_prompts = []
        
        if hasattr(personality_config, 'system_prompt') and personality_config.system_prompt:
            system_prompts.append(personality_config.system_prompt)
        elif hasattr(personality_config, 'description') and personality_config.description:
            system_prompts.append(personality_config.description)
        
        return ContextBundle(
            system_prompts=system_prompts,
            recent_messages=[],
            summarized_history=[],
            retrieved_memories=[],
            user_profile=None,
            total_tokens=len(system_prompts[0]) * 1.5 if system_prompts else 0,
            metadata={"fallback": True}
        )

