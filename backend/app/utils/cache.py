"""
缓存工具

提供Redis缓存封装，支持多种缓存策略
"""

# 标准库
import json
from typing import Any, Optional, Union, Dict, Callable
from functools import wraps, lru_cache
from datetime import timedelta
from threading import Lock
import time

# 第三方库
import redis
from redis.connection import ConnectionPool
from cachetools import TTLCache

# 本地库
from app.config.config import settings
from app.utils.logger import logger


class CacheManager:
    """缓存管理器
    
    提供Redis缓存的统一接口，支持多种缓存策略
    """
    
    def __init__(self):
        """初始化缓存管理器"""
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self) -> None:
        """连接Redis"""
        try:
            redis_url = settings.redis_url
            redis_password = settings.redis_password
            
            # 检查URL中是否已包含密码
            has_password_in_url = "@" in redis_url.split("://")[1] if "://" in redis_url else False
            
            # 如果URL中没有密码，但配置了密码，则在URL中添加密码
            if not has_password_in_url and redis_password:
                # 解析URL并添加密码
                if redis_url.startswith("redis://"):
                    # redis://host:port/db -> redis://:password@host:port/db
                    url_parts = redis_url.split("://")
                    if len(url_parts) == 2:
                        host_part = url_parts[1]
                        redis_url = f"redis://:{redis_password}@{host_part}"
            
            # 创建连接池
            self.pool = ConnectionPool.from_url(
                redis_url,
                max_connections=settings.redis_max_connections,
                decode_responses=True
            )
            
            # 创建Redis客户端
            self.client = redis.Redis(connection_pool=self.pool)
            
            # 测试连接
            try:
                self.client.ping()
                logger.info(
                    "Redis cache connected",
                    extra={
                        "redis_url": settings.redis_url,
                        "max_connections": settings.redis_max_connections
                    }
                )
            except Exception as ping_error:
                # Redis连接失败不影响应用启动，只记录警告
                logger.warning(
                    f"Redis cache connection failed (cache will be disabled): {ping_error}",
                    exc_info=False
                )
                self.client = None
            
        except Exception as e:
            # Redis连接失败不影响应用启动，只记录警告
            logger.warning(
                f"Failed to initialize Redis cache (cache will be disabled): {e}",
                exc_info=False
            )
            self.client = None
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值，如果不存在返回None
        """
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            # 尝试JSON解析
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Failed to get cache key '{key}': {e}", exc_info=True)
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒或timedelta对象）
            
        Returns:
            bool: 是否设置成功
        """
        if not self.client:
            return False
        
        try:
            # 序列化值
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            else:
                serialized_value = str(value)
            
            # 转换TTL
            if isinstance(ttl, timedelta):
                ttl_seconds = int(ttl.total_seconds())
            else:
                ttl_seconds = ttl
            
            # 设置缓存
            if ttl_seconds:
                self.client.setex(key, ttl_seconds, serialized_value)
            else:
                self.client.set(key, serialized_value)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set cache key '{key}': {e}", exc_info=True)
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存键
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        if not self.client:
            return False
        
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Failed to delete cache key '{key}': {e}", exc_info=True)
            return False
    
    def exists(self, key: str) -> bool:
        """检查缓存键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否存在
        """
        if not self.client:
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check cache key '{key}': {e}", exc_info=True)
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存键
        
        Args:
            pattern: 键模式（支持通配符）
            
        Returns:
            int: 清除的键数量
        """
        if not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to clear cache pattern '{pattern}': {e}", exc_info=True)
            return 0
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """递增缓存值
        
        Args:
            key: 缓存键
            amount: 递增数量
            
        Returns:
            Optional[int]: 递增后的值，如果失败返回None
        """
        if not self.client:
            return None
        
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Failed to increment cache key '{key}': {e}", exc_info=True)
            return None
    
    def get_or_set(
        self,
        key: str,
        callable_func: callable,
        ttl: Optional[Union[int, timedelta]] = None,
        *args,
        **kwargs
    ) -> Any:
        """获取缓存值，如果不存在则调用函数并缓存结果
        
        Args:
            key: 缓存键
            callable_func: 可调用函数
            ttl: 过期时间
            *args: 函数位置参数
            **kwargs: 函数关键字参数
            
        Returns:
            Any: 缓存值或函数返回值
        """
        # 尝试获取缓存
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        
        # 调用函数获取值
        value = callable_func(*args, **kwargs)
        
        # 缓存结果
        if value is not None:
            self.set(key, value, ttl)
        
        return value
    
    def close(self) -> None:
        """关闭连接"""
        if self.pool:
            self.pool.disconnect()
            logger.info("Redis cache connection closed")


# 全局缓存管理器实例
cache_manager = CacheManager()


class MultiLevelCache:
    """多级缓存管理器
    
    实现 L1（内存）+ L2（Redis）两级缓存架构
    
    L1缓存（内存）：
    - 使用TTLCache，快速访问
    - 适合热点数据
    - 容量有限（默认1000条）
    
    L2缓存（Redis）：
    - 持久化缓存
    - 容量大
    - 跨进程共享
    """
    
    def __init__(
        self,
        l1_maxsize: int = 1000,
        l1_ttl: int = 60,
        l2_manager: Optional[CacheManager] = None
    ):
        """初始化多级缓存
        
        Args:
            l1_maxsize: L1缓存最大容量
            l1_ttl: L1缓存TTL（秒）
            l2_manager: L2缓存管理器（Redis）
        """
        # L1缓存（内存）
        self.l1_cache: TTLCache = TTLCache(maxsize=l1_maxsize, ttl=l1_ttl)
        self.l1_lock = Lock()
        
        # L2缓存（Redis）
        self.l2_cache = l2_manager or cache_manager
        
        logger.info(
            "Multi-level cache initialized",
            extra={
                "l1_maxsize": l1_maxsize,
                "l1_ttl": l1_ttl,
                "l2_enabled": self.l2_cache.client is not None
            }
        )
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值（先查L1，再查L2）
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值，如果不存在返回None
        """
        # 1. 先查L1缓存
        with self.l1_lock:
            if key in self.l1_cache:
                logger.debug(f"L1 cache hit: {key}")
                return self.l1_cache[key]
        
        # 2. 再查L2缓存
        value = self.l2_cache.get(key)
        if value is not None:
            # 回填L1缓存
            with self.l1_lock:
                self.l1_cache[key] = value
            logger.debug(f"L2 cache hit: {key}")
            return value
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
        l1_only: bool = False
    ) -> bool:
        """设置缓存值（同时写入L1和L2）
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒或timedelta）
            l1_only: 是否只写入L1缓存（默认False）
            
        Returns:
            bool: 是否设置成功
        """
        # 1. 写入L1缓存
        with self.l1_lock:
            self.l1_cache[key] = value
        
        # 2. 写入L2缓存（除非l1_only=True）
        if not l1_only:
            return self.l2_cache.set(key, value, ttl)
        
        return True
    
    def delete(self, key: str) -> bool:
        """删除缓存键（同时删除L1和L2）
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        # 删除L1缓存
        with self.l1_lock:
            if key in self.l1_cache:
                del self.l1_cache[key]
        
        # 删除L2缓存
        return self.l2_cache.delete(key)
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self.l1_lock:
            self.l1_cache.clear()
        self.l2_cache.clear_pattern("*")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self.l1_lock:
            l1_size = len(self.l1_cache)
            l1_maxsize = self.l1_cache.maxsize
        
        return {
            "l1": {
                "size": l1_size,
                "maxsize": l1_maxsize,
                "hit_rate": getattr(self.l1_cache, "hit_rate", 0.0)
            },
            "l2": {
                "enabled": self.l2_cache.client is not None
            }
        }


class CacheWarmer:
    """缓存预热器
    
    在应用启动或特定时机预热常用数据到缓存
    """
    
    def __init__(self, cache: Union[CacheManager, MultiLevelCache]):
        """初始化缓存预热器
        
        Args:
            cache: 缓存管理器
        """
        self.cache = cache
        self.warmup_tasks: list = []
    
    def register_warmup(
        self,
        key: str,
        loader: Callable,
        ttl: Optional[int] = None
    ) -> None:
        """注册预热任务
        
        Args:
            key: 缓存键
            loader: 数据加载函数
            ttl: 过期时间（秒）
        """
        self.warmup_tasks.append({
            "key": key,
            "loader": loader,
            "ttl": ttl
        })
    
    async def warmup(self) -> Dict[str, Any]:
        """执行预热
        
        Returns:
            Dict[str, Any]: 预热结果统计
        """
        results = {
            "total": len(self.warmup_tasks),
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        for task in self.warmup_tasks:
            try:
                # 加载数据
                if hasattr(task["loader"], "__call__"):
                    # 如果是异步函数
                    if hasattr(task["loader"], "__code__") and "async" in str(task["loader"]):
                        value = await task["loader"]()
                    else:
                        value = task["loader"]()
                else:
                    value = task["loader"]
                
                # 写入缓存
                if value is not None:
                    self.cache.set(
                        task["key"],
                        value,
                        ttl=task["ttl"]
                    )
                    results["success"] += 1
                    logger.debug(f"Cache warmed: {task['key']}")
                else:
                    results["failed"] += 1
                    logger.warning(f"Cache warmup failed (no data): {task['key']}")
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "key": task["key"],
                    "error": str(e)
                })
                logger.error(f"Cache warmup error for '{task['key']}': {e}", exc_info=True)
        
        logger.info(
            "Cache warmup completed",
            extra=results
        )
        
        return results


# 全局多级缓存实例（可选使用）
multi_level_cache = MultiLevelCache(
    l1_maxsize=1000,
    l1_ttl=60,
    l2_manager=cache_manager
)


def cached(
    key_prefix: str,
    ttl: Optional[Union[int, timedelta]] = None,
    key_func: Optional[callable] = None
):
    """缓存装饰器
    
    Args:
        key_prefix: 缓存键前缀
        ttl: 过期时间
        key_func: 生成缓存键的函数（可选）
        
    Example:
        @cached("user_profile", ttl=300)
        def get_user_profile(user_id: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认使用参数生成键
                key_parts = [key_prefix]
                if args:
                    key_parts.extend(str(arg) for arg in args)
                if kwargs:
                    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # 尝试获取缓存
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 调用函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            if result is not None:
                cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

