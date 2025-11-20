"""记忆评分服务

负责记忆的智能评分、多因子评分和相关性计算
"""

# 标准库
import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

# 本地库
from app.core.personality.models import IntelligentScoring, ScoringWeights
from app.utils.logger import logger


class MemoryScoringService:
    """记忆评分服务
    
    提供记忆的智能评分和多因子综合评分功能
    """
    
    def apply_intelligent_scoring(
        self,
        memories: List[Any],
        query: str,
        config: IntelligentScoring
    ) -> List[Any]:
        """应用智能评分重新排序记忆"""
        # 检测查询类型
        is_numeric_query = any(keyword in query for keyword in config.numeric_query_keywords)
        
        def score_memory(mem_result):
            content = mem_result.memory.content
            similarity = mem_result.similarity
            score = similarity
            
            if is_numeric_query:
                has_number = bool(re.search(r'\d+', content))
                if has_number:
                    score += config.numeric_boost
                    matched_keywords = [kw for kw in config.numeric_memory_keywords if kw in content]
                    if matched_keywords:
                        score += config.keyword_match_boost
                        query_keywords = [kw for kw in config.numeric_query_keywords if kw in query]
                        if query_keywords:
                            for qk in query_keywords:
                                if qk in content:
                                    score += 0.8  # 大幅boost
                                    break
            
            # 内容长度适中加分
            content_len = len(content)
            if config.optimal_length_min <= content_len <= config.optimal_length_max:
                score += config.length_boost
            
            return score
        
        # 按智能评分重新排序
        scored_memories = [(score_memory(m), m) for m in memories]
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        sorted_memories = [m for _, m in scored_memories]
        
        logger.debug(
            f"Applied intelligent scoring",
            extra={
                "query": query[:50],
                "is_numeric_query": is_numeric_query,
                "top_5_scores": [round(score, 4) for score, _ in scored_memories[:5]]
            }
        )
        
        return sorted_memories
    
    def apply_comprehensive_scoring(
        self,
        memories: List[Any],
        query: str,
        session_id: str,
        weights: ScoringWeights,
        memory_levels_config: Optional[Any] = None
    ) -> List[Any]:
        """应用多因子综合评分"""
        query_intent = self._analyze_query_intent(query)
        
        def calculate_comprehensive_score(mem_result):
            memory = mem_result.memory
            similarity_score = mem_result.similarity
            importance_score = memory.importance
            recency_score = self._calculate_recency_score(memory.created_at)
            relevance_score = self._calculate_relevance_score(memory.content, query, query_intent)
            
            comprehensive_score = (
                similarity_score * weights.similarity +
                importance_score * weights.importance +
                recency_score * weights.recency +
                relevance_score * weights.relevance
            )
            
            # 记忆层级boost
            if memory_levels_config and memory_levels_config.enabled:
                if memory.session_id == session_id:
                    comprehensive_score *= memory_levels_config.session_memory_boost
                else:
                    comprehensive_score *= memory_levels_config.cross_session_memory_boost
            
            return comprehensive_score
        
        scored_memories = [(calculate_comprehensive_score(m), m) for m in memories]
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        sorted_memories = [m for _, m in scored_memories]
        
        logger.debug(
            f"Applied comprehensive scoring",
            extra={
                "query": query[:50],
                "top_5_scores": [round(score, 4) for score, _ in scored_memories[:5]]
            }
        )
        
        return sorted_memories
    
    def _calculate_recency_score(self, created_at) -> float:
        """计算时效性分数"""
        if not created_at:
            return 0.5
        
        if isinstance(created_at, datetime):
            now = datetime.now(timezone.utc) if created_at.tzinfo else datetime.now()
            delta = (now - created_at).total_seconds() / 86400  # 天
        else:
            return 0.5
        
        # 指数衰减
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
        """计算相关性分数"""
        query_words = set(re.findall(r'\w+', query.lower()))
        content_words = set(re.findall(r'\w+', content.lower()))
        
        if query_words:
            jaccard = len(query_words & content_words) / len(query_words | content_words)
        else:
            jaccard = 0.0
        
        if query_intent and query_intent.get("type") == "numeric_query":
            if re.search(r'\d+', content):
                jaccard += 0.3
        
        return min(1.0, jaccard)
    
    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """分析查询意图"""
        numeric_keywords = ['身高', '体重', '年龄', '多少', '几', '多高', '多重', '多大', '血压', '血糖']
        is_numeric_query = any(kw in query for kw in numeric_keywords)
        keywords = [kw for kw in numeric_keywords if kw in query]
        is_question = any(qw in query for qw in ['什么', '多少', '几', '如何', '怎么', '？', '?'])
        
        if is_numeric_query and is_question:
            query_type = "numeric_query"
        elif is_question:
            query_type = "factual_query"
        else:
            query_type = "conversational"
        
        return {
            "type": query_type,
            "keywords": keywords,
            "is_question": is_question
        }

