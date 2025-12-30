"""
MCP工具发现测试

测试MCP工具发现器的功能
"""

# 标准库
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# 本地库
from app.engines.tools.mcp.discovery import MCPDiscovery
from app.engines.tools.mcp.client import MCPClient


class TestMCPDiscovery:
    """测试MCP工具发现器"""
    
    @pytest.fixture
    def mcp_discovery(self):
        """创建MCP发现器实例"""
        return MCPDiscovery()
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Mock MCP客户端"""
        mock_client = MagicMock(spec=MCPClient)
        mock_client.initialize = AsyncMock(return_value={
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "test_server", "version": "1.0.0"}
        })
        mock_client.list_tools = AsyncMock(return_value=[
            {"name": "tool1", "description": "Tool 1"},
            {"name": "tool2", "description": "Tool 2"}
        ])
        mock_client.close = AsyncMock()
        return mock_client
    
    @pytest.mark.asyncio
    async def test_discovery_initialization(self, mcp_discovery):
        """测试：发现器初始化"""
        assert mcp_discovery.clients == {}
        assert mcp_discovery.registry is not None
    
    @pytest.mark.asyncio
    async def test_discover_server_success(self, mcp_discovery, mock_mcp_client):
        """测试：发现服务器工具成功"""
        with patch('app.engines.tools.mcp.discovery.MCPClient', return_value=mock_mcp_client):
            with patch('app.engines.tools.mcp.discovery.ToolRegistry.register') as mock_register:
                tools = await mcp_discovery.discover_server(
                    server_name="test_server",
                    command=["python", "-m", "test_server"],
                    env={"TEST_ENV": "test_value"}
                )
                
                assert isinstance(tools, list)
                assert len(tools) == 2
                assert "test_server__tool1" in tools
                assert "test_server__tool2" in tools
                mock_mcp_client.initialize.assert_called_once()
                mock_mcp_client.list_tools.assert_called_once()
                assert mock_register.call_count == 2
    
    @pytest.mark.asyncio
    async def test_discover_server_no_tools(self, mcp_discovery, mock_mcp_client):
        """测试：发现服务器（无工具）"""
        mock_mcp_client.list_tools = AsyncMock(return_value=[])
        
        with patch('app.engines.tools.mcp.discovery.MCPClient', return_value=mock_mcp_client):
            with patch('app.engines.tools.mcp.discovery.ToolRegistry'):
                tools = await mcp_discovery.discover_server(
                    server_name="test_server",
                    command=["python", "-m", "test_server"]
                )
                
                assert isinstance(tools, list)
                assert len(tools) == 0
    
    @pytest.mark.asyncio
    async def test_discover_server_error(self, mcp_discovery):
        """测试：发现服务器错误"""
        with patch('app.engines.tools.mcp.discovery.MCPClient', side_effect=Exception("Connection failed")):
            tools = await mcp_discovery.discover_server(
                server_name="test_server",
                command=["python", "-m", "test_server"]
            )
            
            # 简化实现会捕获异常并返回空列表
            assert isinstance(tools, list)
            assert len(tools) == 0
    
    @pytest.mark.asyncio
    async def test_discover_server_tool_without_name(self, mcp_discovery, mock_mcp_client):
        """测试：发现服务器（工具无name字段）"""
        mock_mcp_client.list_tools = AsyncMock(return_value=[
            {"description": "Tool without name"},
            {"name": "tool2", "description": "Tool 2"}
        ])
        
        with patch('app.engines.tools.mcp.discovery.MCPClient', return_value=mock_mcp_client):
            with patch('app.engines.tools.mcp.discovery.ToolRegistry.register') as mock_register:
                tools = await mcp_discovery.discover_server(
                    server_name="test_server",
                    command=["python", "-m", "test_server"]
                )
                
                # 只有有name的工具会被注册
                assert len(tools) == 1
                assert "test_server__tool2" in tools
                assert mock_register.call_count == 1
    
    @pytest.mark.asyncio
    async def test_discover_from_config(self, mcp_discovery):
        """测试：从配置发现服务器"""
        results = await mcp_discovery.discover_from_config()
        
        assert isinstance(results, dict)
        # 简化实现返回空字典
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_close_all_success(self, mcp_discovery, mock_mcp_client):
        """测试：关闭所有客户端成功"""
        mcp_discovery.clients = {
            "server1": mock_mcp_client,
            "server2": mock_mcp_client
        }
        
        await mcp_discovery.close_all()
        
        assert len(mcp_discovery.clients) == 0
        assert mock_mcp_client.close.call_count == 2
    
    @pytest.mark.asyncio
    async def test_close_all_with_error(self, mcp_discovery):
        """测试：关闭所有客户端（有错误）"""
        mock_client1 = MagicMock()
        mock_client1.close = AsyncMock()
        
        mock_client2 = MagicMock()
        mock_client2.close = AsyncMock(side_effect=Exception("Close failed"))
        
        mcp_discovery.clients = {
            "server1": mock_client1,
            "server2": mock_client2
        }
        
        # 简化实现会捕获异常并继续
        await mcp_discovery.close_all()
        
        # 所有客户端都会被尝试关闭
        assert mock_client1.close.called
        assert mock_client2.close.called
        assert len(mcp_discovery.clients) == 0
