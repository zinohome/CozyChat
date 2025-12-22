"""
意图分析器

分析用户查询意图，决定调用哪些引擎
"""

# 标准库
from enum import Enum
from typing import Dict, Any

# 本地库
from app.utils.logger import logger


class QueryIntent(Enum):
    """查询意图"""
    CHITCHAT = "chitchat"  # 闲聊
    KNOWLEDGE_QUERY = "knowledge"  # 知识查询
    TASK_EXECUTION = "task"  # 任务执行
    EMOTIONAL_SUPPORT = "emotional"  # 情感支持
    INFORMATION_QUERY = "info"  # 信息查询
    LEARNING = "learning"  # 学习辅导


class IntentAnalyzer:
    """意图分析器"""
    
    @staticmethod
    def analyze_intent(query: str, context: Dict[str, Any] = None) -> QueryIntent:
        """分析查询意图
        
        Args:
            query: 查询文本
            context: 上下文信息
        
        Returns:
            QueryIntent: 查询意图
        """
        if not query:
            return QueryIntent.CHITCHAT
        
        query_lower = query.lower().strip()
        
        # 知识查询关键词
        knowledge_keywords = ["什么是", "如何", "为什么", "解释", "原理", "定义", "介绍", "是什么"]
        if any(kw in query_lower for kw in knowledge_keywords):
            logger.debug(f"Intent detected: KNOWLEDGE_QUERY - {query[:50]}")
            return QueryIntent.KNOWLEDGE_QUERY
        
        # 任务执行关键词
        task_keywords = ["帮我", "请", "完成", "执行", "做", "创建", "生成"]
        if any(kw in query_lower for kw in task_keywords):
            logger.debug(f"Intent detected: TASK_EXECUTION - {query[:50]}")
            return QueryIntent.TASK_EXECUTION
        
        # 情感支持关键词
        emotional_keywords = ["难过", "开心", "焦虑", "压力", "感觉", "情绪", "心情"]
        if any(kw in query_lower for kw in emotional_keywords):
            logger.debug(f"Intent detected: EMOTIONAL_SUPPORT - {query[:50]}")
            return QueryIntent.EMOTIONAL_SUPPORT
        
        # 学习辅导关键词
        learning_keywords = ["学习", "教", "练习", "理解", "掌握", "学会"]
        if any(kw in query_lower for kw in learning_keywords):
            logger.debug(f"Intent detected: LEARNING - {query[:50]}")
            return QueryIntent.LEARNING
        
        # 默认：闲聊
        logger.debug(f"Intent detected: CHITCHAT (default) - {query[:50]}")
        return QueryIntent.CHITCHAT
    
    @staticmethod
    def get_engine_config(intent: QueryIntent) -> Dict[str, Dict[str, Any]]:
        """根据意图获取引擎配置
        
        Args:
            intent: 查询意图
        
        Returns:
            Dict: 引擎配置
        """
        configs = {
            QueryIntent.CHITCHAT: {
                "knowledge": {"enabled": False},
                "userprofile": {"enabled": True, "max_tokens": 300},
                "chatmemory": {"enabled": True, "top_k": 5},
            },
            QueryIntent.KNOWLEDGE_QUERY: {
                "knowledge": {"enabled": True, "top_k": 3},
                "userprofile": {"enabled": True, "max_tokens": 200},
                "chatmemory": {"enabled": True, "top_k": 3},
            },
            QueryIntent.TASK_EXECUTION: {
                "knowledge": {"enabled": True, "top_k": 2},
                "userprofile": {"enabled": True, "max_tokens": 200},
                "chatmemory": {"enabled": True, "top_k": 5},
            },
            QueryIntent.EMOTIONAL_SUPPORT: {
                "knowledge": {"enabled": False},
                "userprofile": {"enabled": True, "max_tokens": 400},
                "chatmemory": {"enabled": True, "top_k": 8},
            },
            QueryIntent.INFORMATION_QUERY: {
                "knowledge": {"enabled": True, "top_k": 5},
                "userprofile": {"enabled": False},
                "chatmemory": {"enabled": True, "top_k": 2},
            },
            QueryIntent.LEARNING: {
                "knowledge": {"enabled": True, "top_k": 3},
                "userprofile": {"enabled": True, "max_tokens": 300},
                "chatmemory": {"enabled": True, "top_k": 4},
            },
        }
        return configs.get(intent, configs[QueryIntent.CHITCHAT])

