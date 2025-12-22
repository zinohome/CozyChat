"""缓存工具模块 - 向后兼容

注意：新的MultiLevelCache已移至cache_new目录
这里只导出旧的CacheManager和cached装饰器以保持向后兼容
"""

# 旧的缓存管理器（向后兼容）
# 从同级cache.py文件导入（使用importlib避免命名冲突）
import importlib.util
import os

# 获取cache.py的路径
_cache_py_path = os.path.join(os.path.dirname(__file__), "..", "cache.py")
if os.path.exists(_cache_py_path):
    _spec = importlib.util.spec_from_file_location("cache_module", _cache_py_path)
    _cache_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_cache_module)
    
    cache_manager = getattr(_cache_module, "cache_manager", None)
    CacheManager = getattr(_cache_module, "CacheManager", None)
    cached = getattr(_cache_module, "cached", None)
else:
    import warnings
    warnings.warn("Legacy cache.py not found", ImportWarning)
    cache_manager = None
    CacheManager = None
    cached = None

__all__ = ["cache_manager", "CacheManager", "cached"]

