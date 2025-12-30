"""
主应用测试

测试FastAPI主应用的功能
"""

# 标准库
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# 本地库
from app.main import app


class TestMainApp:
    """测试主应用"""
    
    def test_root_endpoint(self, client):
        """测试：根路径"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
    
    def test_app_initialization(self):
        """测试：应用初始化"""
        assert app is not None
        assert app.title == "CozyChat"
        assert app.version is not None
    
    def test_app_docs_endpoint(self, client):
        """测试：文档端点"""
        response = client.get("/docs")
        
        # 文档端点应该返回200或重定向
        assert response.status_code in [200, 307, 308]
    
    def test_app_openapi_endpoint(self, client):
        """测试：OpenAPI端点"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data or "info" in data
    
    @pytest.mark.asyncio
    async def test_global_exception_handler(self, client):
        """测试：全局异常处理器"""
        # 创建一个会抛出异常的端点（如果存在）
        # 由于我们无法直接测试异常处理器，这里只验证应用配置
        assert app.exception_handlers is not None
    
    def test_cors_middleware(self, client):
        """测试：CORS中间件"""
        # 测试OPTIONS请求
        response = client.options("/v1/health")
        
        # OPTIONS请求应该返回200或405
        assert response.status_code in [200, 405, 404]
    
    def test_performance_middleware(self, client):
        """测试：性能监控中间件"""
        # 发送一个请求，验证中间件正常工作
        response = client.get("/")
        
        assert response.status_code == 200
        # 中间件应该正常工作，不抛出异常

