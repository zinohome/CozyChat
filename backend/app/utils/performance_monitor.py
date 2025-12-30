"""
性能监控工具（简化版）
"""

# 标准库
import time
from typing import Dict, Any

# 本地库
from app.utils.logger import logger


class PerformanceMonitor:
    """性能监控"""
    
    def __init__(self):
        self.metrics: Dict[str, Dict[str, Any]] = {
            "knowledge_search": {"count": 0, "total_time": 0, "cache_hits": 0},
            "profile_get": {"count": 0, "total_time": 0, "cache_hits": 0},
            "memory_search": {"count": 0, "total_time": 0, "cache_hits": 0},
        }
    
    async def track(self, operation: str, func, *args, **kwargs):
        """跟踪操作性能"""
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start
            
            if operation in self.metrics:
                self.metrics[operation]["count"] += 1
                self.metrics[operation]["total_time"] += duration
                
                if duration > 0.5:
                    logger.warning(f"{operation} took {duration:.2f}s")
            
            return result
        except Exception as e:
            logger.error(f"{operation} failed: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {}
        for operation, metrics in self.metrics.items():
            if metrics["count"] > 0:
                avg_time = metrics["total_time"] / metrics["count"]
                cache_hit_rate = metrics["cache_hits"] / metrics["count"] * 100
                stats[operation] = {
                    "count": metrics["count"],
                    "avg_time_ms": avg_time * 1000,
                    "cache_hit_rate": f"{cache_hit_rate:.1f}%",
                }
        return stats

