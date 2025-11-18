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
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

# 第三方库
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from app.engines.memory.manager import MemoryManager
from app.engines.ai.engine_pool import LLMEnginePool
from app.core.personality.models import Personality, IntelligentScoring, ScoringWeights
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
            # 注意：SQLAlchemy的AsyncSession不支持并发操作，必须顺序执行
            # 或者为每个查询创建独立的会话（但会增加开销）
            # 这里采用顺序执行，因为查询通常很快
            
            # 1. 获取最近消息
            recent_messages = await self._get_recent_messages(session_id, recent_message_count)
            
            # 2. 加载历史摘要（如果启用）
            summaries = []
            if include_summaries:
                summaries = await self._load_history_summaries(session_id)
            
            # 3. 检索记忆（如果启用）
            memories = []
            if include_memories:
                memories = await self._retrieve_memories(user_id, session_id, current_message, personality_config)
            
            # 4. 加载用户画像
            user_profile = await self._load_user_profile(user_id)
            
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
            # 注意：SQLAlchemy模型实例的属性在运行时会被正确解析为实际值
            # 类型检查器可能报错，但运行时不会有问题
            message_responses = [
                MessageSchema(
                    id=msg.id,  # type: ignore[arg-type]
                    session_id=msg.session_id,  # type: ignore[arg-type]
                    role=msg.role,  # type: ignore[arg-type]
                    content=msg.content,  # type: ignore[arg-type]
                    tokens=getattr(msg, 'tokens', None),  # tokens 可能不存在
                    model=msg.model,  # type: ignore[arg-type]
                    created_at=msg.created_at  # type: ignore[arg-type]
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
            
            # 注意：SQLAlchemy模型实例的属性在运行时会被正确解析为实际值
            # 类型检查器可能报错，但运行时不会有问题
            return [str(s.content) for s in summaries]  # type: ignore[misc]
            
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
            
            # 为了确保重要记忆不被过滤，检索更多结果（3倍），然后统一排序筛选
            # 这样可以避免按类型分别限制导致的遗漏，特别是对于相似度较低但包含关键信息的记忆
            search_max_results = max_results * 3
            
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
            # 特别记录包含关键信息的记忆（包含数字+关键词）
            import re
            key_memories = []
            # 获取智能评分配置（如果可用）
            intelligent_scoring_config = None
            if personality_config and hasattr(personality_config, 'memory') and hasattr(personality_config.memory, 'retrieval'):
                intelligent_scoring_config = personality_config.memory.retrieval.intelligent_scoring
            
            if intelligent_scoring_config and intelligent_scoring_config.enabled:
                numeric_keywords = intelligent_scoring_config.numeric_memory_keywords
                for m in all_memories:
                    content = m.memory.content
                    has_number = bool(re.search(r'\d+', content))
                    has_keyword = any(kw in content for kw in numeric_keywords)
                    if has_number and has_keyword:
                        key_memories.append({
                            "id": m.memory.id,
                            "content": content[:100],
                            "similarity": round(m.similarity, 4),
                            "memory_type": m.memory.memory_type.value
                        })
            
            logger.info(
                f"All retrieved memories (sorted by similarity)",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "query": query[:50],
                    "total_count": len(all_memories),
                    "key_memories_count": len(key_memories),  # 包含关键信息的记忆数量
                    "key_memories": key_memories[:5],  # 记录前5个关键记忆
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
            
            # 应用多因子排序和智能评分
            # 1. 智能评分（关键词匹配、数值匹配等）
            intelligent_scoring = None
            scoring_weights = None
            memory_levels_config = None
            if personality_config and hasattr(personality_config, 'memory') and hasattr(personality_config.memory, 'retrieval'):
                intelligent_scoring = personality_config.memory.retrieval.intelligent_scoring
                scoring_weights = personality_config.memory.retrieval.scoring_weights
                memory_levels_config = personality_config.memory.retrieval.memory_levels
            
            # 2. 应用智能评分
            if intelligent_scoring and intelligent_scoring.enabled:
                all_memories = self._apply_intelligent_scoring(
                    all_memories,
                    query,
                    intelligent_scoring
                )
            
            # 3. 应用多因子排序（相似度 + 重要性 + 时效性 + 相关性）
            if scoring_weights:
                all_memories = self._apply_comprehensive_scoring(
                    all_memories,
                    query,
                    session_id,
                    scoring_weights,
                    memory_levels_config
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
    
    def _match_keyword_with_number(
        self,
        content: str,
        keyword: str,
        max_distance: int = 5
    ) -> Optional[Tuple[str, float]]:
        """匹配关键词和数值，支持多种格式
        
        支持的格式：
        - "体重90kg"
        - "体重 90kg"
        - "体重是90kg"
        - "体重：90kg"
        - "体重为90公斤"
        - "体重90"
        
        Args:
            content: 记忆内容
            keyword: 关键词
            max_distance: 关键词和数字之间的最大距离（字符数）
            
        Returns:
            Optional[Tuple[str, float]]: (匹配的数值文本, 数值) 或 None
        """
        import re
        
        # 模式1：关键词 + 可选分隔符 + 数字 + 可选单位
        patterns = [
            rf'{re.escape(keyword)}[：:是]?\s*(\d+(?:\.\d+)?)\s*(?:kg|公斤|千克|cm|厘米|岁|岁数)?',
            rf'{re.escape(keyword)}\s+(\d+(?:\.\d+)?)',
            rf'{re.escape(keyword)}(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value_text = match.group(1)
                try:
                    value = float(value_text)
                    return (value_text, value)
                except ValueError:
                    continue
        
        # 模式2：在关键词附近查找数字（距离限制）
        keyword_pos = content.find(keyword)
        if keyword_pos != -1:
            # 在关键词前后max_distance个字符内查找数字
            search_start = max(0, keyword_pos - max_distance)
            search_end = min(len(content), keyword_pos + len(keyword) + max_distance)
            search_text = content[search_start:search_end]
            
            # 查找数字
            number_match = re.search(r'(\d+(?:\.\d+)?)', search_text)
            if number_match:
                value_text = number_match.group(1)
                try:
                    value = float(value_text)
                    return (value_text, value)
                except ValueError:
                    pass
        
        return None
    
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
                    # 对于包含查询关键词+具体数值的记忆，给予更大的boost
                    matched_keywords = [kw for kw in config.numeric_memory_keywords if kw in content]
                    if matched_keywords:
                        score += config.keyword_match_boost
                        # 特殊处理：如果记忆包含查询关键词+具体数值，且查询也包含该关键词
                        # 给予额外的大幅boost，确保包含关键信息的记忆能够进入top 5
                        # 检查查询中是否包含关键词，且记忆中也包含该关键词
                        # 例如："我体重多少？" 查询包含"体重"，记忆"体重90kg"也包含"体重"
                        query_keywords = [kw for kw in config.numeric_query_keywords if kw in query]
                        if query_keywords:
                            # 检查记忆是否包含查询中的关键词
                            for qk in query_keywords:
                                if qk in content:
                                    # 对于"我体重多少？"和"体重90kg"这样的精确匹配，给予额外的大幅boost
                                    # 这个boost足够大，确保即使原始相似度较低（如0.37），也能进入top 5
                                    score += 0.8  # 大幅boost，确保关键记忆进入top 5
                                    
                                    # 使用灵活的关键词-数值匹配函数
                                    if config.keyword_number_matching.enabled:
                                        match_result = self._match_keyword_with_number(
                                            content,
                                            qk,
                                            max_distance=config.keyword_number_matching.max_distance
                                        )
                                        if match_result:
                                            # 如果关键词和数值匹配成功，给予超级boost
                                            score += config.keyword_number_matching.super_boost
                                    break  # 找到一个匹配就足够了
            
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
    
    def _calculate_recency_score(self, created_at) -> float:
        """计算时效性分数
        
        Args:
            created_at: 记忆创建时间
            
        Returns:
            float: 时效性分数（0-1），越新越高
        """
        from datetime import datetime, timezone
        
        if not created_at:
            return 0.5  # 默认分数
        
        # 计算距离现在的时间（天）
        if isinstance(created_at, datetime):
            now = datetime.now(timezone.utc) if created_at.tzinfo else datetime.now()
            delta = (now - created_at).total_seconds() / 86400  # 转换为天
        else:
            return 0.5
        
        # 使用指数衰减：7天内=1.0, 30天=0.5, 90天=0.1
        if delta <= 7:
            return 1.0
        elif delta <= 30:
            return 0.5 + 0.5 * (1 - (delta - 7) / 23)
        elif delta <= 90:
            return 0.1 + 0.4 * (1 - (delta - 30) / 60)
        else:
            return 0.1
    
    def _calculate_relevance_score(
        self,
        content: str,
        query: str,
        query_intent: Optional[Dict[str, Any]] = None
    ) -> float:
        """计算相关性分数
        
        Args:
            content: 记忆内容
            query: 查询文本
            query_intent: 查询意图（可选）
            
        Returns:
            float: 相关性分数（0-1）
        """
        import re
        
        # 基础相关性：关键词匹配
        query_words = set(re.findall(r'\w+', query.lower()))
        content_words = set(re.findall(r'\w+', content.lower()))
        
        # 计算Jaccard相似度
        if query_words:
            jaccard = len(query_words & content_words) / len(query_words | content_words)
        else:
            jaccard = 0.0
        
        # 如果查询意图已知，根据意图类型调整
        if query_intent:
            if query_intent.get("type") == "numeric_query":
                # 数值查询：检查是否包含数值
                if re.search(r'\d+', content):
                    jaccard += 0.3  # 额外加分
        
        return min(1.0, jaccard)
    
    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """分析查询意图
        
        Args:
            query: 查询文本
            
        Returns:
            Dict[str, Any]: 查询意图信息
        """
        import re
        
        # 检测数值查询关键词
        numeric_keywords = ['身高', '体重', '年龄', '多少', '几', '多高', '多重', '多大', '血压', '血糖']
        is_numeric_query = any(kw in query for kw in numeric_keywords)
        
        # 提取关键词
        keywords = [kw for kw in numeric_keywords if kw in query]
        
        # 判断是否为问题
        is_question = any(qw in query for qw in ['什么', '多少', '几', '如何', '怎么', '？', '?'])
        
        # 判断查询类型
        if is_numeric_query and is_question:
            query_type = "numeric_query"
            # 根据关键词推断期望格式
            if '体重' in keywords:
                expected_format = "体重XXkg"
            elif '身高' in keywords:
                expected_format = "身高XXcm"
            elif '年龄' in keywords:
                expected_format = "年龄XX岁"
            else:
                expected_format = None
        elif is_question:
            query_type = "factual_query"
            expected_format = None
        else:
            query_type = "conversational"
            expected_format = None
        
        return {
            "type": query_type,
            "keywords": keywords,
            "expected_format": expected_format,
            "is_question": is_question
        }
    
    def _apply_comprehensive_scoring(
        self,
        memories: List[Any],
        query: str,
        session_id: str,
        weights: ScoringWeights,
        memory_levels_config: Optional[Any] = None
    ) -> List[Any]:
        """应用多因子综合评分
        
        Args:
            memories: 记忆列表
            query: 查询文本
            session_id: 当前会话ID
            weights: 权重配置
            memory_levels_config: 记忆层级配置
            
        Returns:
            List[MemorySearchResult]: 重新排序后的记忆列表
        """
        # 分析查询意图
        query_intent = self._analyze_query_intent(query)
        
        # 对每个记忆计算综合分数
        def calculate_comprehensive_score(mem_result):
            """计算综合评分"""
            memory = mem_result.memory
            
            # 1. 相似度分数（归一化到0-1）
            similarity_score = mem_result.similarity
            
            # 2. 重要性分数（归一化到0-1）
            importance_score = memory.importance
            
            # 3. 时效性分数（归一化到0-1）
            recency_score = self._calculate_recency_score(memory.created_at)
            
            # 4. 相关性分数（基于查询意图）
            relevance_score = self._calculate_relevance_score(
                memory.content,
                query,
                query_intent
            )
            
            # 5. 加权求和
            comprehensive_score = (
                similarity_score * weights.similarity +
                importance_score * weights.importance +
                recency_score * weights.recency +
                relevance_score * weights.relevance
            )
            
            # 6. 记忆层级boost（如果启用）
            if memory_levels_config and memory_levels_config.enabled:
                if memory.session_id == session_id:
                    # 当前会话记忆：更高权重
                    comprehensive_score *= memory_levels_config.session_memory_boost
                else:
                    # 跨会话记忆：标准权重
                    comprehensive_score *= memory_levels_config.cross_session_memory_boost
            
            return comprehensive_score
        
        # 按综合评分重新排序
        scored_memories = [(calculate_comprehensive_score(m), m) for m in memories]
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        sorted_memories = [m for _, m in scored_memories]
        
        logger.debug(
            f"Memories after comprehensive scoring",
            extra={
                "query": query[:50],
                "query_intent": query_intent,
                "weights": {
                    "similarity": weights.similarity,
                    "importance": weights.importance,
                    "recency": weights.recency,
                    "relevance": weights.relevance
                },
                "top_5_scores": [
                    {
                        "content": m.memory.content[:50],
                        "score": round(score, 4)
                    }
                    for score, m in scored_memories[:5]
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
        if personality_config and hasattr(personality_config, 'ai'):
            # 从AI配置中获取system_prompt
            ai_config = personality_config.ai
            if hasattr(ai_config, 'system_prompt') and ai_config.system_prompt:
                system_prompts.append(ai_config.system_prompt)
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
        
        if personality_config and hasattr(personality_config, 'ai'):
            # 从AI配置中获取system_prompt
            ai_config = personality_config.ai
            if hasattr(ai_config, 'system_prompt') and ai_config.system_prompt:
                system_prompts.append(ai_config.system_prompt)
            elif hasattr(personality_config, 'description') and personality_config.description:
                system_prompts.append(personality_config.description)
        
        return ContextBundle(
            system_prompts=system_prompts,
            recent_messages=[],
            summarized_history=[],
            retrieved_memories=[],
            user_profile=None,
            total_tokens=int(len(system_prompts[0]) * 1.5) if system_prompts else 0,
            metadata={"fallback": True}
        )

