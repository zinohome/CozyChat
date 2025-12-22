"""
性能监控中间件

记录API响应时间、请求统计等性能指标
"""

# 标准库
import time
from typing import Callable

# 第三方库
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# 本地库
from app.config.config import settings
from app.utils.logger import logger

# 导入旧的cache_manager（直接从cache.py）
try:
    # 由于cache/目录和cache.py文件冲突，需要特殊导入
    import sys
    from pathlib import Path
    cache_py_path = Path(__file__).parent.parent / "utils" / "cache.py"
    
    import importlib.util
    spec = importlib.util.spec_from_file_location("app.utils.cache_legacy", cache_py_path)
    if spec and spec.loader:
        cache_legacy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cache_legacy)
        cache_manager = cache_legacy.cache_manager
    else:
        cache_manager = None
except Exception as e:
    import warnings
    warnings.warn(f"Failed to import cache_manager: {e}")
    cache_manager = None


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件
    
    记录API响应时间、请求统计等性能指标
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录性能指标
        
        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理函数
            
        Returns:
            Response: HTTP响应
        """
        # 记录开始时间
        start_time = time.time()
        
        # 处理请求
        try:
            response = await call_next(request)
        except Exception as e:
            # 记录异常
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": process_time,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录性能指标
        self._log_performance(request, response, process_time)
        
        # 添加响应头
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        
        return response
    
    def _log_performance(
        self,
        request: Request,
        response: Response,
        process_time: float
    ) -> None:
        """记录性能指标
        
        Args:
            request: 请求对象
            response: 响应对象
            process_time: 处理时间（秒）
        """
        # 根据请求类型设置不同的慢请求阈值（从配置读取）
        # 使用配置适配器获取性能配置（优先YAML，回退到Settings）
        from app.utils.config_adapter import get_config_adapter
        config_adapter = get_config_adapter()
        performance_config = config_adapter.get_performance_config()
        slow_request_config = performance_config.get("slow_request", {})
        
        if request.method == "DELETE":
            slow_threshold = slow_request_config.get("delete_threshold", settings.performance_slow_delete_threshold)
        else:
            slow_threshold = slow_request_config.get("threshold", settings.performance_slow_request_threshold)
        
        # 记录慢请求
        if process_time > slow_threshold:
            logger.warning(
                f"Slow request: {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": process_time
                }
            )
        else:
            logger.debug(
                f"Request processed: {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": process_time
                }
            )
        
        # 更新统计信息（使用Redis）
        try:
            # 统计总请求数
            cache_manager.increment("stats:total_requests")
            
            # 统计各状态码的请求数
            cache_manager.increment(f"stats:status:{response.status_code}")
            
            # 记录平均响应时间（简化实现）
            # 实际应该使用更复杂的统计方法（如滑动窗口）
            cache_key = f"stats:avg_response_time:{request.url.path}"
            current_avg = cache_manager.get(cache_key) or 0.0
            # 简单的移动平均
            new_avg = (current_avg * 0.9) + (process_time * 0.1)
            cache_manager.set(cache_key, new_avg, ttl=3600)
            
        except Exception as e:
            # 统计失败不影响主流程
            logger.debug(f"Failed to update stats: {e}")

