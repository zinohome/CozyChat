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
from app.utils.logger import logger
from app.utils.cache import cache_manager


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
        # 记录慢请求（>200ms）
        if process_time > 0.2:
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

