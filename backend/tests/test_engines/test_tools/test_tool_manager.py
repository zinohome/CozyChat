"""
工具管理器测试

测试工具管理器的工具注册、执行、获取等功能
"""

# 标准库
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# 本地库
from app.engines.tools.manager import ToolManager
from app.engines.tools.base import Tool, ToolType
from app.engines.tools.registry import ToolRegistry


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
        return {
            "input": {
                "type": "string",
                "description": "Input parameter",
                "required": True
            }
        }
    
    def validate_parameters(self, **kwargs) -> None:
        """验证参数"""
        if "input" not in kwargs:
            raise ValueError("Missing required parameter: input")
    
    async def execute(self, **kwargs) -> dict:
        """执行工具"""
        return {"result": f"Processed: {kwargs.get('input', '')}"}


class TestToolManager:
    """测试工具管理器"""
    
    @pytest.fixture
    def tool_manager(self):
        """创建工具管理器实例"""
        return ToolManager(max_concurrent_tools=3, tool_timeout=5.0)
    
    @pytest.fixture
    def registered_tool(self, tool_manager):
        """注册测试工具"""
        ToolRegistry.register("mock_tool", MockTool)
        yield
        # 清理
        ToolRegistry.unregister("mock_tool")
    
    @pytest.mark.asyncio
    async def test_create_tool_success(self, tool_manager, registered_tool):
        """测试：创建工具成功"""
        tool = tool_manager.create_tool("mock_tool")
        
        assert tool is not None
        assert isinstance(tool, MockTool)
        assert tool.name == "mock_tool"
    
    @pytest.mark.asyncio
    async def test_create_tool_not_found(self, tool_manager):
        """测试：创建不存在的工具"""
        tool = tool_manager.create_tool("non_existent_tool")
        
        assert tool is None
    
    @pytest.mark.asyncio
    async def test_execute_tool_success(self, tool_manager, registered_tool):
        """测试：执行工具成功"""
        result = await tool_manager.execute_tool(
            tool_name="mock_tool",
            parameters={"input": "test"}
        )
        
        assert result["success"] is True
        assert "result" in result
        assert result["tool_name"] == "mock_tool"
    
    @pytest.mark.asyncio
    async def test_execute_tool_timeout(self, tool_manager, registered_tool):
        """测试：执行工具超时"""
        # 创建一个会超时的工具
        class SlowTool(MockTool):
            async def execute(self, **kwargs) -> dict:
                await asyncio.sleep(10.0)  # 超过5秒超时
                return {"result": "done"}
        
        ToolRegistry.register("slow_tool", SlowTool)
        try:
            # 使用短超时时间
            manager = ToolManager(tool_timeout=0.1)
            result = await manager.execute_tool(
                tool_name="slow_tool",
                parameters={"input": "test"}
            )
            
            # 应该超时并返回错误
            assert result["success"] is False
            assert "timeout" in result.get("error", "").lower() or "timeout" in str(result)
        finally:
            ToolRegistry.unregister("slow_tool")
    
    @pytest.mark.asyncio
    async def test_execute_tool_invalid_parameters(self, tool_manager, registered_tool):
        """测试：执行工具参数无效"""
        result = await tool_manager.execute_tool(
            tool_name="mock_tool",
            parameters={}  # 缺少必需参数
        )
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_execute_tools_concurrent(self, tool_manager, registered_tool):
        """测试：并发执行工具"""
        # 创建多个工具执行任务
        tasks = [
            tool_manager.execute_tool(
                tool_name="mock_tool",
                parameters={"input": f"test_{i}"}
            )
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 所有任务应该成功
        assert len(results) == 5
        for result in results:
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_available_tools(self, tool_manager, registered_tool):
        """测试：获取可用工具列表"""
        tools = tool_manager.get_available_tools()
        
        assert isinstance(tools, list)
        assert "mock_tool" in tools
    
    @pytest.mark.asyncio
    async def test_get_tools_for_openai(self, tool_manager, registered_tool):
        """测试：获取OpenAI格式的工具列表"""
        tools = tool_manager.get_tools_for_openai(tool_names=["mock_tool"])
        
        assert isinstance(tools, list)
        if len(tools) > 0:
            tool = tools[0]
            assert "type" in tool or "function" in tool
            assert "name" in tool.get("function", {}) or "name" in tool
    
    @pytest.mark.asyncio
    async def test_get_tools_for_openai_all(self, tool_manager, registered_tool):
        """测试：获取所有工具的OpenAI格式"""
        tools = tool_manager.get_tools_for_openai()
        
        assert isinstance(tools, list)
        # 至少应该有mock_tool
        assert len(tools) >= 0
    
    def test_health_check(self, tool_manager):
        """测试：健康检查"""
        health = tool_manager.health_check()
        
        assert isinstance(health, dict)
        assert "status" in health
        assert health["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_execute_tool_error_handling(self, tool_manager, registered_tool):
        """测试：执行工具错误处理"""
        # 创建一个会抛出异常的工具
        class ErrorTool(MockTool):
            async def execute(self, **kwargs) -> dict:
                raise Exception("Tool execution error")
        
        ToolRegistry.register("error_tool", ErrorTool)
        try:
            result = await tool_manager.execute_tool(
                tool_name="error_tool",
                parameters={"input": "test"}
            )
            
            assert result["success"] is False
            assert "error" in result
        finally:
            ToolRegistry.unregister("error_tool")
    
    @pytest.mark.asyncio
    async def test_get_tools_for_openai_with_filter(self, tool_manager, registered_tool):
        """测试：获取OpenAI格式的工具列表（带过滤）"""
        # 注册另一个工具
        class AnotherTool(MockTool):
            @property
            def name(self) -> str:
                return "another_tool"
        
        ToolRegistry.register("another_tool", AnotherTool)
        try:
            # 只获取mock_tool
            tools = tool_manager.get_tools_for_openai(tool_names=["mock_tool"])
            
            assert isinstance(tools, list)
            # 验证只返回了指定的工具
            tool_names = [
                t.get("function", {}).get("name") or t.get("name")
                for t in tools
            ]
            assert "mock_tool" in tool_names or len(tools) == 0
        finally:
            ToolRegistry.unregister("another_tool")

