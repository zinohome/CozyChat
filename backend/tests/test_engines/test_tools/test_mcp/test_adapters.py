"""
MCP工具适配器测试

测试MCP工具适配器的功能
"""

# 标准库
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# 本地库
from app.engines.tools.mcp.adapters import MCPToolAdapter
from app.engines.tools.mcp.client import MCPClient


class TestMCPToolAdapter:
    """测试MCP工具适配器"""
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Mock MCP客户端"""
        mock_client = MagicMock(spec=MCPClient)
        mock_client.call_tool = AsyncMock(return_value="Tool result")
        return mock_client
    
    @pytest.fixture
    def tool_info(self):
        """工具信息"""
        return {
            "name": "test_tool",
            "description": "Test tool description",
            "inputSchema": {
                "properties": {
                    "arg1": {"type": "string", "description": "Argument 1"},
                    "arg2": {"type": "number", "description": "Argument 2"}
                }
            }
        }
    
    @pytest.fixture
    def mcp_adapter(self, mock_mcp_client, tool_info):
        """创建MCP工具适配器实例"""
        return MCPToolAdapter(
            mcp_client=mock_mcp_client,
            server_name="test_server",
            tool_info=tool_info
        )
    
    def test_adapter_initialization(self, mcp_adapter, mock_mcp_client, tool_info):
        """测试：适配器初始化"""
        assert mcp_adapter.mcp_client == mock_mcp_client
        assert mcp_adapter.server_name == "test_server"
        assert mcp_adapter.tool_info == tool_info
        assert mcp_adapter.name == "test_server__test_tool"
        assert mcp_adapter.description == "Test tool description"
        assert isinstance(mcp_adapter.parameters, dict)
        assert "arg1" in mcp_adapter.parameters
        assert "arg2" in mcp_adapter.parameters
    
    def test_adapter_name_property(self, mcp_adapter):
        """测试：适配器名称属性"""
        assert mcp_adapter.name == "test_server__test_tool"
    
    def test_adapter_description_property(self, mcp_adapter):
        """测试：适配器描述属性"""
        assert mcp_adapter.description == "Test tool description"
    
    def test_adapter_parameters_property(self, mcp_adapter):
        """测试：适配器参数属性"""
        params = mcp_adapter.parameters
        assert isinstance(params, dict)
        assert "arg1" in params
        assert "arg2" in params
    
    def test_adapter_without_input_schema(self, mock_mcp_client):
        """测试：适配器（无inputSchema）"""
        tool_info = {
            "name": "test_tool",
            "description": "Test tool"
        }
        
        adapter = MCPToolAdapter(
            mcp_client=mock_mcp_client,
            server_name="test_server",
            tool_info=tool_info
        )
        
        assert adapter.parameters == {}
    
    @pytest.mark.asyncio
    async def test_execute_success(self, mcp_adapter, mock_mcp_client):
        """测试：执行工具成功"""
        result = await mcp_adapter.execute(arg1="value1", arg2=42)
        
        assert result == "Tool result"
        mock_mcp_client.call_tool.assert_called_once_with(
            server_name="test_server",
            tool_name="test_tool",
            arguments={"arg1": "value1", "arg2": 42}
        )
    
    @pytest.mark.asyncio
    async def test_execute_error(self, mcp_adapter, mock_mcp_client):
        """测试：执行工具错误"""
        mock_mcp_client.call_tool = AsyncMock(side_effect=Exception("Tool execution failed"))
        
        result = await mcp_adapter.execute(arg1="value1")
        
        assert isinstance(result, str)
        # 适配器会捕获异常并返回错误信息
        assert "执行失败" in result or "MCP工具执行失败" in result
    
    @pytest.mark.asyncio
    async def test_execute_with_empty_args(self, mcp_adapter, mock_mcp_client):
        """测试：执行工具（无参数）"""
        result = await mcp_adapter.execute()
        
        assert result == "Tool result"
        mock_mcp_client.call_tool.assert_called_once_with(
            server_name="test_server",
            tool_name="test_tool",
            arguments={}
        )
