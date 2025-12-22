"""缓存工具模块 - 向后兼容

注意：新的MultiLevelCache已移至cache_new目录
这里只导出旧的CacheManager以保持向后兼容
"""

# 旧的缓存管理器（向后兼容）
# 从上级cache.py导入
try:
    from ..cache import cache_manager, CacheManager
except ImportError:
    import warnings
    warnings.warn("Legacy cache_manager not available", ImportWarning)
    cache_manager = None
    CacheManager = None

__all__ = ["cache_manager", "CacheManager"]

