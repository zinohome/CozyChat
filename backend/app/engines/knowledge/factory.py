"""
知识引擎工厂

提供可插拔式的知识引擎创建，支持未来替换实现
"""

# 标准库
from typing import Dict, Any

# 本地库
from app.engines.knowledge.base import KnowledgeEngineBase
from app.engines.knowledge.cognee_engine import CogneeKnowledgeEngine
from app.utils.logger import logger


class KnowledgeEngineFactory:
    """知识引擎工厂
    
    支持创建不同类型的知识引擎实现：
    - cognee: Cognee知识图谱引擎
    - (未来可扩展其他实现)
    """
    
    @staticmethod
    def create_engine(provider: str, config: Dict[str, Any]) -> KnowledgeEngineBase:
        """创建知识引擎实例
        
        Args:
            provider: 引擎提供商（如 "cognee"）
            config: 引擎配置
        
        Returns:
            KnowledgeEngineBase: 知识引擎实例
        
        Raises:
            ValueError: 未知的provider
        """
        provider = provider.lower().strip()
        
        if provider == "cognee":
            logger.info(f"Creating Cognee knowledge engine with config: {config}")
            return CogneeKnowledgeEngine(config=config)
        
        # 未来可扩展其他知识引擎
        # elif provider == "neo4j":
        #     return Neo4jKnowledgeEngine(config=config)
        # elif provider == "elasticsearch":
        #     return ElasticsearchKnowledgeEngine(config=config)
        
        else:
            raise ValueError(
                f"Unknown knowledge engine provider: {provider}. "
                f"Supported providers: cognee"
            )

