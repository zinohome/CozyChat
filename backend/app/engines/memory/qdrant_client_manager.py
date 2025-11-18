"""
Qdrant客户端管理器

提供全局Qdrant客户端实例，避免重复创建连接。
"""

# 标准库
from typing import Optional
import threading

# 第三方库
from qdrant_client import QdrantClient

# 本地库
from app.config.config import settings
from app.utils.logger import logger


class QdrantClientManager:
    """Qdrant客户端管理器
    
    管理全局的Qdrant客户端连接，
    在应用启动时初始化一次。
    """
    
    _instance: Optional['QdrantClientManager'] = None
    _lock = threading.Lock()
    
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None):
        """初始化客户端管理器
        
        Args:
            url: Qdrant服务URL
            api_key: API密钥（可选）
        """
        self.url = url or settings.qdrant_url
        self.api_key = api_key or settings.qdrant_api_key
        
        if not self.url:
            raise ValueError("Qdrant URL is required")
        
        # 创建客户端
        if self.api_key:
            self.client = QdrantClient(url=self.url, api_key=self.api_key)
        else:
            self.client = QdrantClient(url=self.url)
        
        logger.info(
            "Qdrant client initialized",
            extra={"url": self.url, "has_api_key": bool(self.api_key)}
        )
    
    @classmethod
    def get_instance(
        cls,
        url: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> 'QdrantClientManager':
        """获取单例实例
        
        Args:
            url: Qdrant服务URL
            api_key: API密钥（可选）
            
        Returns:
            QdrantClientManager: 单例实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(url, api_key)
        return cls._instance
    
    def get_client(self) -> QdrantClient:
        """获取Qdrant客户端
        
        Returns:
            QdrantClient: Qdrant客户端实例
        """
        return self.client


# 创建全局实例
_manager: Optional[QdrantClientManager] = None


def get_qdrant_client() -> QdrantClient:
    """获取全局Qdrant客户端
    
    Returns:
        QdrantClient: Qdrant客户端实例
    """
    global _manager
    if _manager is None:
        _manager = QdrantClientManager.get_instance()
    return _manager.get_client()


def init_qdrant_client(
    url: Optional[str] = None,
    api_key: Optional[str] = None
) -> QdrantClient:
    """初始化全局Qdrant客户端
    
    应在应用启动时调用一次。
    
    Args:
        url: Qdrant服务URL
        api_key: API密钥（可选）
        
    Returns:
        QdrantClient: Qdrant客户端实例
    """
    global _manager
    _manager = QdrantClientManager.get_instance(url, api_key)
    return _manager.get_client()

