"""
ToolService单元测试

测试工具服务的所有功能，包括：
- 准备工具
- 执行工具调用
- 验证工具调用
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Any

from app.services.tool_service import ToolService


class TestToolService:
    """ToolService单元测试类"""
    
    @pytest.fixture
    def mock_tool_call_handler(self):
        """创建模拟工具调用处理器"""
        handler = MagicMock()
        handler.prepare_tools = AsyncMock(return_value=[])
        handler.execute_tool_call = AsyncMock(return_value=None)
        return handler
    
    @pytest.fixture
    def mock_tool_manager_factory(self):
        """创建模拟工具管理器工厂"""
        factory = MagicMock()
        factory.create_manager = MagicMock(return_value=MagicMock())
        return factory
    
    @pytest.fixture
    def tool_service(self, mock_tool_manager_factory):
        """创建ToolService实例"""
        return ToolService(tool_factory=mock_tool_manager_factory)
    
    def test_prepare_tools_success(
        self,
        tool_service
    ):
        """测试：获取可用工具列表（替代prepare_tools）"""
        # Arrange
        allowed_tools = ["calculator", "time"]
        
        mock_manager = MagicMock()
        mock_manager.get_tools_for_openai.return_value = [
            {"function": {"name": "calculator"}},
            {"function": {"name": "time"}}
        ]
        tool_service.tool_factory.get_tool_manager = MagicMock(return_value=mock_manager)
        
        # Act
        result = tool_service.get_available_tools(allowed_tools=allowed_tools)
        
        # Assert
        assert result is not None
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_execute_tool_call_success(
        self,
        tool_service
    ):
        """测试：成功执行工具调用"""
        # Arrange
        tool_call_chunks = [{
            "id": "call-1",
            "function": {
                "name": "calculator",
                "arguments": '{"expression": "2+2"}'
            }
        }]
        
        # Mock tool_handler.execute_tool_calls
        tool_service.tool_handler.execute_tool_calls = AsyncMock(return_value=[{"result": "4"}])
        
        # Act
        result = await tool_service.execute_tool_calls(tool_call_chunks)
        
        # Assert
        assert result is not None
        tool_service.tool_handler.execute_tool_calls.assert_called_once()
    
    def test_get_available_tools(
        self,
        tool_service,
        mock_tool_manager_factory
    ):
        """测试：获取可用工具列表"""
        # Arrange
        allowed_tools = ["calculator", "time"]
        
        mock_manager = MagicMock()
        mock_manager.get_tools_for_openai.return_value = [
            {"function": {"name": "calculator"}},
            {"function": {"name": "time"}}
        ]
        mock_tool_manager_factory.get_tool_manager = MagicMock(return_value=mock_manager)
        
        # Act
        result = tool_service.get_available_tools(allowed_tools=allowed_tools)
        
        # Assert
        assert result is not None
        assert len(result) == 2
