"""
记忆重要性评分器

根据内容特征自动计算记忆的重要性分数
"""

# 标准库
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# 本地库
from app.utils.logger import logger
from app.utils.config_loader import get_config_loader


class ImportanceScorer:
    """重要性评分器
    
    根据内容长度、关键词、频率、时间等计算记忆的重要性分数
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化评分器
        
        Args:
            config: 配置字典（如果不提供则从YAML加载）
        """
        if config is None:
            config_loader = get_config_loader()
            memory_config = config_loader.load_memory_config()
            importance_config = memory_config.get("importance", {}) if memory_config else {}
            scoring_config = importance_config.get("scoring", {}) if importance_config else {}
            config = scoring_config.get("default", {}) if scoring_config else {}
        
        # 权重配置
        if config:
            self.content_length_weight = config.get("content_length_weight", 0.3)
            self.keyword_weight = config.get("keyword_weight", 0.4)
            self.frequency_weight = config.get("frequency_weight", 0.2)
            self.recency_weight = config.get("recency_weight", 0.1)
        else:
            self.content_length_weight = 0.3
            self.keyword_weight = 0.4
            self.frequency_weight = 0.2
            self.recency_weight = 0.1
        
        # 重要关键词列表（可根据实际需求扩展）
        self.important_keywords = [
            # 个人信息相关
            "姓名", "名字", "年龄", "生日", "出生", "地址", "电话", "邮箱",
            "工作", "职业", "公司", "学校", "学历",
            # 偏好相关
            "喜欢", "不喜欢", "讨厌", "偏好", "习惯", "爱好",
            # 重要事件
            "重要", "关键", "必须", "记得", "记住", "不要忘记",
            # 健康相关
            "健康", "疾病", "过敏", "药物", "治疗",
            # 关系相关
            "家人", "朋友", "同事", "恋人", "配偶",
        ]
        
        logger.debug(
            "Importance scorer initialized",
            extra={
                "content_length_weight": self.content_length_weight,
                "keyword_weight": self.keyword_weight,
                "frequency_weight": self.frequency_weight,
                "recency_weight": self.recency_weight,
            }
        )
    
    def calculate_importance(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        created_at: Optional[datetime] = None
    ) -> float:
        """计算记忆重要性
        
        算法：
        1. 内容长度评分 (0-1) - 内容越长，重要性越高（但有限制）
        2. 关键词评分 (0-1) - 包含重要关键词越多，重要性越高
        3. 频率评分 (0-1) - 基于历史访问频率（需要metadata支持）
        4. 时间评分 (0-1) - 基于创建时间（新记忆权重更高）
        
        最终分数 = 加权平均，范围 [0, 1]
        
        Args:
            content: 记忆内容
            metadata: 元数据（可包含访问频率等信息）
            user_id: 用户ID（可选，用于频率统计）
            session_id: 会话ID（可选）
            created_at: 创建时间（可选，默认当前时间）
            
        Returns:
            float: 重要性分数 [0, 1]
        """
        if not content or not content.strip():
            return 0.0
        
        metadata = metadata or {}
        created_at = created_at or datetime.utcnow()
        
        # 1. 内容长度评分
        content_length_score = self._calculate_length_score(content)
        
        # 2. 关键词评分
        keyword_score = self._calculate_keyword_score(content)
        
        # 3. 频率评分（如果有访问频率信息）
        frequency_score = self._calculate_frequency_score(metadata)
        
        # 4. 时间评分
        recency_score = self._calculate_recency_score(created_at)
        
        # 加权平均
        importance = (
            content_length_score * self.content_length_weight +
            keyword_score * self.keyword_weight +
            frequency_score * self.frequency_weight +
            recency_score * self.recency_weight
        )
        
        # 确保在 [0, 1] 范围内
        importance = max(0.0, min(1.0, importance))
        
        logger.debug(
            "Calculated memory importance",
            extra={
                "content_length": len(content),
                "content_length_score": round(content_length_score, 3),
                "keyword_score": round(keyword_score, 3),
                "frequency_score": round(frequency_score, 3),
                "recency_score": round(recency_score, 3),
                "final_importance": round(importance, 3),
            }
        )
        
        return importance
    
    def _calculate_length_score(self, content: str) -> float:
        """计算内容长度评分
        
        评分规则：
        - 0-10字符: 0.1
        - 10-50字符: 0.3-0.6（线性增长）
        - 50-200字符: 0.6-0.9（线性增长）
        - 200+字符: 0.9（饱和）
        
        Args:
            content: 内容文本
            
        Returns:
            float: 长度评分 [0, 1]
        """
        length = len(content.strip())
        
        if length == 0:
            return 0.0
        elif length < 10:
            return 0.1
        elif length < 50:
            # 10-50字符: 0.3-0.6
            return 0.3 + (length - 10) / 40 * 0.3
        elif length < 200:
            # 50-200字符: 0.6-0.9
            return 0.6 + (length - 50) / 150 * 0.3
        else:
            # 200+字符: 0.9（饱和）
            return 0.9
    
    def _calculate_keyword_score(self, content: str) -> float:
        """计算关键词评分
        
        评分规则：
        - 检测重要关键词出现次数
        - 关键词数量越多，评分越高
        - 最高1.0（包含5个以上关键词）
        
        Args:
            content: 内容文本
            
        Returns:
            float: 关键词评分 [0, 1]
        """
        content_lower = content.lower()
        matched_keywords = []
        
        for keyword in self.important_keywords:
            if keyword.lower() in content_lower:
                matched_keywords.append(keyword)
        
        keyword_count = len(matched_keywords)
        
        if keyword_count == 0:
            return 0.2  # 即使没有关键词，也有基础分数
        elif keyword_count == 1:
            return 0.4
        elif keyword_count == 2:
            return 0.6
        elif keyword_count == 3:
            return 0.75
        elif keyword_count == 4:
            return 0.85
        else:
            return 1.0
    
    def _calculate_frequency_score(self, metadata: Dict[str, Any]) -> float:
        """计算频率评分
        
        评分规则：
        - 基于历史访问频率（需要metadata中的access_count）
        - 访问次数越多，评分越高
        - 如果没有频率信息，返回0.5（中性分数）
        
        Args:
            metadata: 元数据
            
        Returns:
            float: 频率评分 [0, 1]
        """
        access_count = metadata.get("access_count", 0)
        
        if access_count == 0:
            return 0.5  # 中性分数
        elif access_count == 1:
            return 0.6
        elif access_count == 2:
            return 0.7
        elif access_count <= 5:
            return 0.8
        elif access_count <= 10:
            return 0.9
        else:
            return 1.0
    
    def _calculate_recency_score(self, created_at: datetime) -> float:
        """计算时间评分
        
        评分规则：
        - 新记忆（7天内）: 1.0
        - 较新记忆（7-30天）: 0.8
        - 中等记忆（30-90天）: 0.6
        - 较旧记忆（90-180天）: 0.4
        - 旧记忆（180天+）: 0.2
        
        Args:
            created_at: 创建时间
            
        Returns:
            float: 时间评分 [0, 1]
        """
        now = datetime.utcnow()
        age_days = (now - created_at).days
        
        if age_days < 7:
            return 1.0
        elif age_days < 30:
            return 0.8
        elif age_days < 90:
            return 0.6
        elif age_days < 180:
            return 0.4
        else:
            return 0.2
    
    def update_access_frequency(
        self,
        metadata: Dict[str, Any],
        increment: int = 1
    ) -> Dict[str, Any]:
        """更新访问频率
        
        Args:
            metadata: 元数据
            increment: 增量
            
        Returns:
            Dict: 更新后的元数据
        """
        current_count = metadata.get("access_count", 0)
        metadata["access_count"] = current_count + increment
        metadata["last_accessed_at"] = datetime.utcnow().isoformat()
        return metadata

