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
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from app.engines.memory.manager import MemoryManager
from app.engines.ai.engine_pool import LLMEnginePool
from app.core.personality.models import Personality, IntelligentScoring
from app.schemas.context import ContextBundle, Message as MessageSchema
from app.models.message import Message as DBMessage
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
        db: AsyncSession
    ):
        """初始化ContextBuilder
        
        Args:
            memory_manager: 记忆管理器
            engine_pool: LLM引擎池
            db: 数据库会话（异步）
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
                self._retrieve_memories(user_id, session_id, current_message, personality_config) if include_memories else asyncio.coroutine(lambda: [])(),
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
    ) -> List[MessageSchema]:
        """获取最近的消息原文
        
        Args:
            session_id: 会话ID
            count: 消息数量
            
        Returns:
            List[MessageSchema]: 消息列表
        """
        try:
            # 查询数据库获取最近的消息
            stmt = (
                select(DBMessage)
                .where(DBMessage.session_id == UUID(session_id))
                .order_by(desc(DBMessage.created_at))
                .limit(count)
            )
            
            result = await self.db.execute(stmt)
            messages = result.scalars().all()
            
            # 转换为响应模型并反转顺序（从旧到新）
            message_responses = [
                MessageSchema(
                    id=msg.id,
                    session_id=msg.session_id,
                    role=msg.role,
                    content=msg.content,
                    tokens=getattr(msg, 'tokens', None),  # tokens 可能不存在
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
            
            result = await self.db.execute(stmt)
            summaries = result.scalars().all()
            
            return [s.content for s in summaries]
            
        except Exception as e:
            logger.error(f"Failed to load history summaries: {e}", exc_info=True)
            return []
    
    async def _retrieve_memories(
        self,
        user_id: str,
        session_id: str,
        query: str,
        personality_config: Optional[Personality] = None
    ) -> List[Any]:
        """检索相关记忆
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            query: 查询文本
            personality_config: 人格配置（用于获取相似度阈值）
            
        Returns:
            List[Memory]: 记忆列表
        """
        try:
            # 从人格配置中获取相似度阈值，如果没有则使用默认值0.3（更宽松，提高召回率）
            if personality_config and hasattr(personality_config, 'memory') and hasattr(personality_config.memory, 'retrieval'):
                similarity_threshold = personality_config.memory.retrieval.similarity_threshold
                max_results = personality_config.memory.retrieval.max_results
                timeout = personality_config.memory.retrieval.timeout_seconds
            else:
                similarity_threshold = 0.3  # 默认使用更宽松的阈值
                max_results = 5
                timeout = 0.5
            
            # 为了确保重要记忆不被过滤，检索更多结果（2倍），然后统一排序筛选
            # 这样可以避免按类型分别限制导致的遗漏
            search_max_results = max_results * 2
            
            logger.debug(
                f"Retrieving memories with personality config",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "similarity_threshold": similarity_threshold,
                    "max_results": max_results,
                    "timeout": timeout,
                    "has_personality_config": personality_config is not None
                }
            )
            
            # 调用MemoryManager检索记忆
            # 使用 search_max_results 获取更多候选结果，然后统一排序筛选
            memory_results = await self.memory_manager.retrieve_memories(
                user_id=user_id,
                session_id=session_id,
                query=query,
                max_results=search_max_results,  # 检索更多结果
                include_user_memory=True,
                include_ai_memory=True,
                timeout=timeout,
                similarity_threshold=similarity_threshold
            )
            
            # 合并用户记忆和AI记忆
            user_memories = memory_results.get("user_memories", [])
            ai_memories = memory_results.get("ai_memories", [])
            
            logger.debug(
                f"Memory retrieval results",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "query": query[:50],
                    "user_memories_count": len(user_memories),
                    "ai_memories_count": len(ai_memories),
                    "total_count": len(user_memories) + len(ai_memories)
                }
            )
            
            all_memories = []
            all_memories.extend(user_memories)
            all_memories.extend(ai_memories)
            
            # 按相似度排序（MemorySearchResult 使用 similarity 而不是 score）
            all_memories.sort(key=lambda m: getattr(m, 'similarity', getattr(m, 'score', 0)), reverse=True)
            
            # 详细记录所有检索到的记忆（用于调试）
            logger.info(
                f"All retrieved memories (sorted by similarity)",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "query": query[:50],
                    "total_count": len(all_memories),
                    "all_memories": [
                        {
                            "id": m.memory.id,
                            "content": m.memory.content[:100],
                            "similarity": round(m.similarity, 4),
                            "memory_type": m.memory.memory_type.value,
                            "session_id": m.memory.session_id
                        }
                        for m in all_memories[:20]  # 记录前20个
                    ]
                }
            )
            
            # 智能筛选：优先包含关键信息的记忆（如果启用）
            intelligent_scoring = None
            if personality_config and hasattr(personality_config, 'memory') and hasattr(personality_config.memory, 'retrieval'):
                intelligent_scoring = personality_config.memory.retrieval.intelligent_scoring
            
            if intelligent_scoring and intelligent_scoring.enabled:
                all_memories = self._apply_intelligent_scoring(
                    all_memories,
                    query,
                    intelligent_scoring
                )
            
            # 使用配置的 max_results（不是硬编码的5）
            result = all_memories[:max_results]
            
            logger.info(
                f"Final selected memories (top {max_results})",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "query": query[:50],
                    "returned_count": len(result),
                    "selected_memories": [
                        {
                            "id": m.memory.id,
                            "content": m.memory.content[:100],
                            "similarity": round(m.similarity, 4),
                            "memory_type": m.memory.memory_type.value
                        }
                        for m in result
                    ]
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}", exc_info=True)
            return []
    
    def _apply_intelligent_scoring(
        self,
        memories: List[Any],
        query: str,
        config: IntelligentScoring
    ) -> List[Any]:
        """应用智能评分重新排序记忆
        
        Args:
            memories: 记忆列表
            query: 查询文本
            config: 智能评分配置
            
        Returns:
            List[MemorySearchResult]: 重新排序后的记忆列表
        """
        import re
        
        # 检测查询类型：是否询问具体数值
        is_numeric_query = any(
            keyword in query 
            for keyword in config.numeric_query_keywords
        )
        
        # 对记忆进行智能评分
        def score_memory(mem_result):
            """计算记忆的智能评分"""
            content = mem_result.memory.content
            similarity = mem_result.similarity
            
            # 基础分数：相似度
            score = similarity
            
            # 如果是数值查询，优先包含数字的记忆
            if is_numeric_query:
                # 检查记忆是否包含数字（具体数值）
                has_number = bool(re.search(r'\d+', content))
                if has_number:
                    # 使用配置的加分权重
                    score += config.numeric_boost
                    
                    # 如果记忆同时包含查询关键词和数字，额外加分
                    if any(kw in content for kw in config.numeric_memory_keywords):
                        score += config.keyword_match_boost
            
            # 加分项：内容长度适中（使用配置的范围）
            content_len = len(content)
            if config.optimal_length_min <= content_len <= config.optimal_length_max:
                score += config.length_boost
            
            return score
        
        # 按智能评分重新排序
        # 先保存原始相似度用于日志
        original_similarities = {id(m): getattr(m, 'similarity', 0) for m in memories}
        
        scored_memories = [(score_memory(m), m) for m in memories]
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        sorted_memories = [m for _, m in scored_memories]
        
        # 记录智能评分后的排序结果
        logger.debug(
            f"Memories after intelligent scoring",
            extra={
                "query": query[:50],
                "is_numeric_query": is_numeric_query,
                "config_enabled": config.enabled,
                "scored_memories": [
                    {
                        "content": m.memory.content[:100],
                        "original_similarity": round(original_similarities.get(id(m), 0), 4),
                        "final_score": round(score, 4),
                        "boost": round(score - original_similarities.get(id(m), 0), 4)
                    }
                    for score, m in scored_memories[:10]
                ]
            }
        )
        
        return sorted_memories
    
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
            result = await self.db.execute(stmt)
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
        recent_messages: List[MessageSchema],
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
        # memories 是 MemorySearchResult 列表，需要提取 memory.content
        for m in memories:
            if hasattr(m, 'memory'):
                # MemorySearchResult 对象
                estimated_tokens += len(m.memory.content) * 1.5
            elif hasattr(m, 'content'):
                # 已经是 Memory 对象
                estimated_tokens += len(m.content) * 1.5
        estimated_tokens += sum(len(msg.content) * 1.5 for msg in recent_messages)
        
        # 将 MemorySearchResult 列表转换为 Memory 列表（ContextBundle 需要 Memory 类型）
        memory_list = []
        for mem_result in memories:
            if hasattr(mem_result, 'memory'):
                # MemorySearchResult 对象，提取 memory 属性
                memory_list.append(mem_result.memory)
            elif hasattr(mem_result, 'content'):
                # 已经是 Memory 对象
                memory_list.append(mem_result)
        
        logger.debug(
            f"Assembling context bundle",
            extra={
                "system_prompts_count": len(system_prompts),
                "recent_messages_count": len(recent_messages),
                "summaries_count": len(summaries),
                "memories_count": len(memory_list),
                "user_profile": user_profile is not None
            }
        )
        
        return ContextBundle(
            system_prompts=system_prompts,
            recent_messages=recent_messages,
            summarized_history=summaries,
            retrieved_memories=memory_list,  # 使用转换后的 Memory 列表
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

