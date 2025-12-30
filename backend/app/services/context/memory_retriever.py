"""
记忆检索服务

负责从向量数据库检索相关记忆，并应用智能评分和多因子排序

============================================================================
⚠️ DEPRECATED: MemoryRetriever（已废弃）
============================================================================
状态：已废弃，将在 v2.0 移除
废弃时间：2024-12-22
移除时间：2025-Q1

替代方案：使用三大人格化引擎
  - ChatMemory Engine: backend/app/engines/chatmemory/ （会话记忆）
  - Knowledge Engine: backend/app/engines/knowledge/ （知识检索）
  - ContextServiceNew: 集成智能检索和意图分析

迁移指南：docs/reports/三大人格化引擎系统架构重构方案.md
============================================================================
"""

# 标准库
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from app.core.personality.models import Personality
    from app.engines.memory.manager import MemoryManager

# 本地库
from app.utils.logger import logger


class MemoryRetriever:
    """记忆检索器
    
    负责从向量数据库检索相关记忆，并应用智能评分和多因子排序
    """
    
    def __init__(
        self,
        memory_manager: "MemoryManager"
    ):
        """初始化MemoryRetriever
        
        Args:
            memory_manager: 记忆管理器
        """
        self.memory_manager = memory_manager
    
    async def retrieve_memories(
        self,
        user_id: str,
        session_id: str,
        query: str,
        personality_config: Optional["Personality"] = None
    ) -> List[Any]:
        """检索相关记忆
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            query: 查询文本
            personality_config: 人格配置（用于获取相似度阈值）
            
        Returns:
            List[MemorySearchResult]: 记忆列表（已排序）
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
        config: Any  # IntelligentScoring
    ) -> List[Any]:
        """应用智能评分重新排序记忆
        
        Args:
            memories: 记忆列表
            query: 查询文本
            config: 智能评分配置
            
        Returns:
            List[MemorySearchResult]: 重新排序后的记忆列表
        """
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
    
    def _calculate_recency_score(self, created_at: Any) -> float:
        """计算时效性分数
        
        Args:
            created_at: 记忆创建时间
            
        Returns:
            float: 时效性分数（0-1），越新越高
        """
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
        memory_content: str,
        query: str
    ) -> float:
        """计算相关性分数
        
        Args:
            memory_content: 记忆内容
            query: 查询文本
            
        Returns:
            float: 相关性分数（0-1）
        """
        # 简单的关键词匹配
        query_words = set(query.lower().split())
        content_words = set(memory_content.lower().split())
        
        if not query_words:
            return 0.0
        
        # 计算重叠度
        overlap = len(query_words & content_words)
        return min(1.0, overlap / len(query_words))
    
    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """分析查询意图
        
        Args:
            query: 查询文本
            
        Returns:
            Dict[str, Any]: 查询意图分析结果
        """
        # 简单的意图识别
        intent = {
            "is_question": "?" in query or any(qw in query for qw in ["什么", "多少", "如何", "为什么"]),
            "is_numeric": bool(re.search(r'\d+', query)),
            "keywords": []
        }
        
        return intent
    
    def _apply_comprehensive_scoring(
        self,
        memories: List[Any],
        query: str,
        session_id: str,
        scoring_weights: Any,  # ScoringWeights
        memory_levels_config: Optional[Any] = None  # MemoryLevels
    ) -> List[Any]:
        """应用多因子综合评分
        
        Args:
            memories: 记忆列表
            query: 查询文本
            session_id: 会话ID
            scoring_weights: 评分权重配置
            memory_levels_config: 记忆级别配置
            
        Returns:
            List[MemorySearchResult]: 重新排序后的记忆列表
        """
        def calculate_comprehensive_score(mem_result):
            """计算综合评分"""
            # 1. 相似度分数（已归一化到0-1）
            similarity_score = getattr(mem_result, 'similarity', 0)
            
            # 2. 时效性分数
            recency_score = self._calculate_recency_score(mem_result.memory.created_at)
            
            # 3. 相关性分数
            relevance_score = self._calculate_relevance_score(
                mem_result.memory.content,
                query
            )
            
            # 4. 重要性分数（基于记忆级别）
            importance_score = 0.5  # 默认值
            if memory_levels_config:
                memory_type = mem_result.memory.memory_type.value
                if memory_type == "fact":
                    importance_score = memory_levels_config.fact_importance
                elif memory_type == "preference":
                    importance_score = memory_levels_config.preference_importance
                elif memory_type == "event":
                    importance_score = memory_levels_config.event_importance
            
            # 加权综合评分
            comprehensive_score = (
                similarity_score * scoring_weights.similarity +
                recency_score * scoring_weights.recency +
                relevance_score * scoring_weights.relevance +
                importance_score * scoring_weights.importance
            )
            
            return comprehensive_score
        
        # 按综合评分重新排序
        scored_memories = [(calculate_comprehensive_score(m), m) for m in memories]
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        sorted_memories = [m for _, m in scored_memories]
        
        logger.debug(
            f"Memories after comprehensive scoring",
            extra={
                "query": query[:50],
                "session_id": session_id,
                "scored_memories": [
                    {
                        "content": m.memory.content[:100],
                        "comprehensive_score": round(score, 4)
                    }
                    for score, m in scored_memories[:10]
                ]
            }
        )
        
        return sorted_memories
