"""
知识引擎数据模型
"""

# 标准库
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class KnowledgeSearchResult:
    """知识搜索结果
    
    Attributes:
        content: 知识内容
        score: 相关度分数
        source: 来源数据集
        metadata: 元数据
    """
    content: str
    score: float
    source: str
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict: 字典格式的结果
        """
        return {
            "content": self.content,
            "score": self.score,
            "source": self.source,
            "metadata": self.metadata or {}
        }


@dataclass
class KnowledgeAddRequest:
    """知识添加请求
    
    Attributes:
        content: 知识内容
        dataset_name: 数据集名称
        metadata: 元数据
    """
    content: str
    dataset_name: str
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict: 字典格式的请求
        """
        return {
            "content": self.content,
            "dataset_name": self.dataset_name,
            "metadata": self.metadata or {}
        }

