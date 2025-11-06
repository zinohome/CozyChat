"""
健康检查接口测试

测试应用健康检查功能
"""

# 第三方库
import pytest
from httpx import AsyncClient

# 本地库
from app import __version__


@pytest.mark.asyncio
class TestHealthEndpoint:
    """测试健康检查接口"""
    
    async def test_health_check(self, async_client: AsyncClient):
        """测试健康检查接口返回正确状态"""
        response = await async_client.get("/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "version" in data
        assert "environment" in data
        assert "timestamp" in data
        assert "database" in data
        
        assert data["version"] == __version__
        assert data["status"] in ["healthy", "unhealthy"]
    
    async def test_root_endpoint(self, async_client: AsyncClient):
        """测试根路径返回欢迎信息"""
        response = await async_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "CozyChat" in data["message"]
