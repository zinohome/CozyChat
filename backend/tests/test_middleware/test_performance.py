"""
性能监控中间件测试

测试PerformanceMiddleware的功能
"""

# 标准库
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

# 本地库
from app.middleware.performance import PerformanceMiddleware
from fastapi import Request, Response
from fastapi.testclient import TestClient
from app.main import app


class TestPerformanceMiddleware:
    """测试性能监控中间件"""
    
    @pytest.fixture
    def middleware(self):
        """创建性能监控中间件"""
        return PerformanceMiddleware(app)
    
    @pytest.fixture
    def mock_request(self):
        """创建Mock请求"""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url.path = "/v1/test"
        return request
    
    @pytest.fixture
    def mock_response(self):
        """创建Mock响应"""
        response = MagicMock(spec=Response)
        response.status_code = 200
        response.headers = {}
        return response
    
    @pytest.mark.asyncio
    async def test_dispatch_success(self, middleware, mock_request, mock_response):
        """测试：处理请求成功"""
        # Mock call_next
        async def mock_call_next(request):
            return mock_response
        
        call_next = AsyncMock(side_effect=mock_call_next)
        
        # Mock cache_manager
        with patch('app.middleware.performance.cache_manager') as mock_cache:
            mock_cache.increment.return_value = 1
            mock_cache.get.return_value = 0.1
            mock_cache.set.return_value = True
            
            result = await middleware.dispatch(mock_request, call_next)
            
            assert result == mock_response
            assert "X-Process-Time" in result.headers
            call_next.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dispatch_error(self, middleware, mock_request):
        """测试：处理请求错误"""
        # Mock call_next抛出异常
        async def mock_call_next(request):
            raise Exception("Test error")
        
        call_next = AsyncMock(side_effect=mock_call_next)
        
        with pytest.raises(Exception):
            await middleware.dispatch(mock_request, call_next)
    
    @pytest.mark.asyncio
    async def test_dispatch_slow_request(self, middleware, mock_request, mock_response):
        """测试：慢请求记录"""
        # Mock call_next延迟
        async def mock_call_next(request):
            await asyncio.sleep(0.3)  # 模拟慢请求
            return mock_response
        
        import asyncio
        call_next = AsyncMock(side_effect=mock_call_next)
        
        # Mock cache_manager
        with patch('app.middleware.performance.cache_manager') as mock_cache:
            mock_cache.increment.return_value = 1
            mock_cache.get.return_value = 0.1
            mock_cache.set.return_value = True
            
            result = await middleware.dispatch(mock_request, call_next)
            
            assert result == mock_response
            # 慢请求应该被记录（通过logger.warning）
    
    @pytest.mark.asyncio
    async def test_dispatch_fast_request(self, middleware, mock_request, mock_response):
        """测试：快速请求记录"""
        # Mock call_next快速返回
        async def mock_call_next(request):
            return mock_response
        
        call_next = AsyncMock(side_effect=mock_call_next)
        
        # Mock cache_manager
        with patch('app.middleware.performance.cache_manager') as mock_cache:
            mock_cache.increment.return_value = 1
            mock_cache.get.return_value = 0.1
            mock_cache.set.return_value = True
            
            result = await middleware.dispatch(mock_request, call_next)
            
            assert result == mock_response
            # 快速请求应该被记录（通过logger.debug）
    
    @pytest.mark.asyncio
    async def test_dispatch_stats_update(self, middleware, mock_request, mock_response):
        """测试：统计信息更新"""
        async def mock_call_next(request):
            return mock_response
        
        call_next = AsyncMock(side_effect=mock_call_next)
        
        # Mock cache_manager
        with patch('app.middleware.performance.cache_manager') as mock_cache:
            mock_cache.increment.return_value = 1
            mock_cache.get.return_value = 0.1
            mock_cache.set.return_value = True
            
            await middleware.dispatch(mock_request, call_next)
            
            # 验证统计信息被更新
            mock_cache.increment.assert_called()
            mock_cache.set.assert_called()

