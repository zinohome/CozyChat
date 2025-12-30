"""
工具注册中心测试

测试ToolRegistry的功能
"""

# 标准库
import pytest
from unittest.mock import MagicMock, patch

# 本地库
from app.engines.tools.registry import ToolRegistry
from app.engines.tools.base import Tool, ToolType


class MockTool(Tool):
    """Mock工具用于测试"""
    
    @property
    def name(self) -> str:
        return "mock_tool"
    
    @property
    def description(self) -> str:
        return "Mock tool for testing"
    
    @property
    def parameters(self) -> dict:
        return {}
    
    async def execute(self, **kwargs):
        return {"result": "success"}


class TestToolRegistry:
    """测试工具注册中心"""
    
    def setup_method(self):
        """每个测试前清理注册表"""
        ToolRegistry._tools.clear()
    
    def test_register_tool_success(self):
        """测试：注册工具成功（覆盖34-51行）"""
        ToolRegistry.register("test_tool", MockTool)
        
        assert "test_tool" in ToolRegistry._tools
        assert ToolRegistry._tools["test_tool"] == MockTool
    
    def test_register_tool_duplicate(self):
        """测试：注册工具（重复注册，覆盖44-45行）"""
        ToolRegistry.register("test_tool", MockTool)
        
        # 重复注册应该只记录警告，不抛出异常
        with patch('app.engines.tools.registry.logger') as mock_logger:
            ToolRegistry.register("test_tool", MockTool)
            mock_logger.warning.assert_called()
    
    def test_register_tool_invalid_class(self):
        """测试：注册工具（无效类，覆盖47-48行）"""
        class InvalidClass:
            pass
        
        with pytest.raises(ValueError, match="must be subclass of Tool"):
            ToolRegistry.register("invalid_tool", InvalidClass)
    
    def test_get_tool_class_success(self):
        """测试：获取工具类（成功）"""
        ToolRegistry.register("test_tool", MockTool)
        
        tool_class = ToolRegistry.get_tool_class("test_tool")
        assert tool_class == MockTool
    
    def test_get_tool_class_not_found(self):
        """测试：获取工具类（不存在）"""
        tool_class = ToolRegistry.get_tool_class("nonexistent_tool")
        assert tool_class is None
    
    def test_list_tools(self):
        """测试：列出所有工具"""
        ToolRegistry.register("tool1", MockTool)
        ToolRegistry.register("tool2", MockTool)
        
        tools = ToolRegistry.list_tools()
        assert "tool1" in tools
        assert "tool2" in tools
    
    def test_is_registered_true(self):
        """测试：检查工具是否已注册（已注册，覆盖84行）"""
        ToolRegistry.register("test_tool", MockTool)
        
        assert ToolRegistry.is_registered("test_tool") is True
    
    def test_is_registered_false(self):
        """测试：检查工具是否已注册（未注册）"""
        assert ToolRegistry.is_registered("nonexistent_tool") is False
    
    def test_unregister_tool_success(self):
        """测试：注销工具（成功，覆盖87-95行）"""
        ToolRegistry.register("test_tool", MockTool)
        
        ToolRegistry.unregister("test_tool")
        
        assert "test_tool" not in ToolRegistry._tools
    
    def test_unregister_tool_not_found(self):
        """测试：注销工具（不存在，覆盖96-97行）"""
        with patch('app.engines.tools.registry.logger') as mock_logger:
            ToolRegistry.unregister("nonexistent_tool")
            mock_logger.warning.assert_called()
    
    def test_get_all_tools_info_success(self):
        """测试：获取所有工具信息（成功，覆盖100-125行）"""
        ToolRegistry.register("test_tool", MockTool)
        
        tools_info = ToolRegistry.get_all_tools_info()
        
        assert "test_tool" in tools_info
        assert tools_info["test_tool"]["name"] == "mock_tool"
        assert tools_info["test_tool"]["description"] == "Mock tool for testing"
        assert tools_info["test_tool"]["type"] == ToolType.BUILTIN.value
    
    def test_get_all_tools_info_with_error(self):
        """测试：获取所有工具信息（工具实例化错误，覆盖117-124行）"""
        # 创建一个会抛出异常的Mock工具类
        class ErrorTool(Tool):
            def __init__(self):
                raise Exception("Initialization error")
            
            @property
            def name(self) -> str:
                return "error_tool"
            
            @property
            def description(self) -> str:
                return "Error tool"
            
            @property
            def parameters(self) -> dict:
                return {}
            
            async def execute(self, **kwargs):
                return {}
        
        ToolRegistry.register("error_tool", ErrorTool)
        
        with patch('app.engines.tools.registry.logger') as mock_logger:
            tools_info = ToolRegistry.get_all_tools_info()
            
            assert "error_tool" in tools_info
            assert tools_info["error_tool"]["name"] == "error_tool"
            assert tools_info["error_tool"]["description"] == "Unknown"
            mock_logger.warning.assert_called()

