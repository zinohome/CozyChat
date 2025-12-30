"""
多级缓存系统（简化版）

L1: 内存缓存（5分钟TTL）
L2: Redis缓存（30分钟TTL）
"""

# 标准库
import time
from typing import Any, Optional, Dict
import json

# 本地库
from app.utils.logger import logger


class MultiLevelCache:
    """多级缓存（简化版）"""
    
    def __init__(self):
        """初始化缓存"""
        # L1: 内存缓存
        self._l1_cache: Dict[str, tuple[Any, float]] = {}
        self._l1_ttl = 300  # 5分钟
        
        logger.info("MultiLevelCache initialized (L1 only for now)")
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存
        
        Args:
            key: 缓存键
        
        Returns:
            缓存值或None
        """
        # 检查L1缓存
        if key in self._l1_cache:
            value, expire_time = self._l1_cache[key]
            if time.time() < expire_time:
                logger.debug(f"Cache hit (L1): {key}")
                return value
            else:
                # 过期，删除
                del self._l1_cache[key]
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None使用默认值
        
        Returns:
            是否成功
        """
        if ttl is None:
            ttl = self._l1_ttl
        
        expire_time = time.time() + ttl
        self._l1_cache[key] = (value, expire_time)
        
        logger.debug(f"Cache set (L1): {key}, ttl={ttl}s")
        return True
    
    async def delete(self, key: str) -> bool:
        """删除缓存
        
        Args:
            key: 缓存键
        
        Returns:
            是否成功
        """
        if key in self._l1_cache:
            del self._l1_cache[key]
            logger.debug(f"Cache deleted: {key}")
            return True
        return False
    
    def clear(self) -> None:
        """清空缓存"""
        self._l1_cache.clear()
        logger.info("Cache cleared")


# 全局缓存实例
cache = MultiLevelCache()

