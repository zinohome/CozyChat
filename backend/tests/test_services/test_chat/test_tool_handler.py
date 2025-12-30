"""
ToolCallHandler服务单元测试

测试工具调用处理服务的各种场景
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch

from app.services.chat.tool_handler import ToolCallHandler
from app.engines.tools.factory import ToolManagerFactory


class TestToolCallHandler:
    """ToolCallHandler单元测试类"""
    
    @pytest.fixture
    def mock_tool_manager(self):
        """创建模拟工具管理器"""
        manager = Mock()
        manager.execute_tool = AsyncMock()
        return manager
    
    @pytest.fixture
    def mock_tool_factory(self, mock_tool_manager):
        """创建模拟工具工厂"""
        factory = Mock(spec=ToolManagerFactory)
        factory.get_tool_manager.return_value = mock_tool_manager
        return factory
    
    @pytest.fixture
    def tool_handler(self, mock_tool_factory):
        """创建ToolCallHandler实例"""
        return ToolCallHandler(tool_factory=mock_tool_factory)
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_success(
        self,
        tool_handler,
        mock_tool_manager
    ):
        """测试：成功执行工具调用"""
        # Arrange
        tool_call_chunks = [
            {
                "id": "call_001",
                "type": "function",
                "function": {
                    "name": "calculator",
                    "arguments": json.dumps({"expression": "1 + 1"})
                }
            }
        ]
        
        mock_tool_manager.execute_tool.return_value = {
            "success": True,
            "result": "2"
        }
        
        # Act
        results = await tool_handler.execute_tool_calls(tool_call_chunks)
        
        # Assert
        assert len(results) == 1
        assert results[0]["role"] == "tool"
        assert results[0]["tool_call_id"] == "call_001"
        assert results[0]["content"] == "2"
        mock_tool_manager.execute_tool.assert_called_once_with(
            tool_name="calculator",
            parameters={"expression": "1 + 1"}
        )
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_with_dict_result(
        self,
        tool_handler,
        mock_tool_manager
    ):
        """测试：工具返回字典结果"""
        # Arrange
        tool_call_chunks = [
            {
                "id": "call_002",
                "type": "function",
                "function": {
                    "name": "weather",
                    "arguments": json.dumps({"city": "Beijing"})
                }
            }
        ]
        
        mock_tool_manager.execute_tool.return_value = {
            "success": True,
            "result": {
                "city": "Beijing",
                "temperature": 25,
                "weather": "Sunny"
            }
        }
        
        # Act
        results = await tool_handler.execute_tool_calls(tool_call_chunks)
        
        # Assert
        assert len(results) == 1
        assert results[0]["role"] == "tool"
        assert results[0]["tool_call_id"] == "call_002"
        # 验证结果被转换为JSON字符串
        result_data = json.loads(results[0]["content"])
        assert result_data["city"] == "Beijing"
        assert result_data["temperature"] == 25
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_with_list_result(
        self,
        tool_handler,
        mock_tool_manager
    ):
        """测试：工具返回列表结果"""
        # Arrange
        tool_call_chunks = [
            {
                "id": "call_003",
                "type": "function",
                "function": {
                    "name": "search",
                    "arguments": json.dumps({"query": "Python"})
                }
            }
        ]
        
        mock_tool_manager.execute_tool.return_value = {
            "success": True,
            "result": ["Result 1", "Result 2", "Result 3"]
        }
        
        # Act
        results = await tool_handler.execute_tool_calls(tool_call_chunks)
        
        # Assert
        assert len(results) == 1
        result_list = json.loads(results[0]["content"])
        assert isinstance(result_list, list)
        assert len(result_list) == 3
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_failure(
        self,
        tool_handler,
        mock_tool_manager
    ):
        """测试：工具执行失败"""
        # Arrange
        tool_call_chunks = [
            {
                "id": "call_004",
                "type": "function",
                "function": {
                    "name": "calculator",
                    "arguments": json.dumps({"expression": "invalid"})
                }
            }
        ]
        
        mock_tool_manager.execute_tool.return_value = {
            "success": False,
            "error": "Invalid expression"
        }
        
        # Act
        results = await tool_handler.execute_tool_calls(tool_call_chunks)
        
        # Assert
        assert len(results) == 1
        assert results[0]["role"] == "tool"
        assert results[0]["tool_call_id"] == "call_004"
        assert "工具执行失败" in results[0]["content"]
        assert "Invalid expression" in results[0]["content"]
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_exception(
        self,
        tool_handler,
        mock_tool_manager
    ):
        """测试：工具执行抛出异常"""
        # Arrange
        tool_call_chunks = [
            {
                "id": "call_005",
                "type": "function",
                "function": {
                    "name": "calculator",
                    "arguments": json.dumps({"expression": "1 + 1"})
                }
            }
        ]
        
        mock_tool_manager.execute_tool.side_effect = Exception("Network error")
        
        # Act
        results = await tool_handler.execute_tool_calls(tool_call_chunks)
        
        # Assert
        assert len(results) == 1
        assert results[0]["role"] == "tool"
        assert results[0]["tool_call_id"] == "call_005"
        assert "工具执行出错" in results[0]["content"]
        assert "Network error" in results[0]["content"]
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_multiple_tools(
        self,
        tool_handler,
        mock_tool_manager
    ):
        """测试：执行多个工具调用"""
        # Arrange
        tool_call_chunks = [
            {
                "id": "call_006",
                "type": "function",
                "function": {
                    "name": "calculator",
                    "arguments": json.dumps({"expression": "1 + 1"})
                }
            },
            {
                "id": "call_007",
                "type": "function",
                "function": {
                    "name": "time",
                    "arguments": json.dumps({})
                }
            }
        ]
        
        mock_tool_manager.execute_tool.side_effect = [
            {"success": True, "result": "2"},
            {"success": True, "result": "2024-01-01 12:00:00"}
        ]
        
        # Act
        results = await tool_handler.execute_tool_calls(tool_call_chunks)
        
        # Assert
        assert len(results) == 2
        assert results[0]["content"] == "2"
        assert results[1]["content"] == "2024-01-01 12:00:00"
        assert mock_tool_manager.execute_tool.call_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_invalid_json(
        self,
        tool_handler,
        mock_tool_manager
    ):
        """测试：无效的JSON参数"""
        # Arrange
        tool_call_chunks = [
            {
                "id": "call_008",
                "type": "function",
                "function": {
                    "name": "calculator",
                    "arguments": "invalid json"
                }
            }
        ]
        
        # Act
        results = await tool_handler.execute_tool_calls(tool_call_chunks)
        
        # Assert
        assert len(results) == 1
        assert results[0]["role"] == "tool"
        assert "工具执行出错" in results[0]["content"]
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_empty_chunks(
        self,
        tool_handler,
        mock_tool_manager
    ):
        """测试：空的工具调用列表"""
        # Arrange
        tool_call_chunks = []
        
        # Act
        results = await tool_handler.execute_tool_calls(tool_call_chunks)
        
        # Assert
        assert len(results) == 0
        mock_tool_manager.execute_tool.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_with_none_chunks(
        self,
        tool_handler,
        mock_tool_manager
    ):
        """测试：包含None的工具调用列表"""
        # Arrange
        tool_call_chunks = [
            None,
            {
                "id": "call_009",
                "type": "function",
                "function": {
                    "name": "calculator",
                    "arguments": json.dumps({"expression": "1 + 1"})
                }
            },
            None
        ]
        
        mock_tool_manager.execute_tool.return_value = {
            "success": True,
            "result": "2"
        }
        
        # Act
        results = await tool_handler.execute_tool_calls(tool_call_chunks)
        
        # Assert
        assert len(results) == 1
        mock_tool_manager.execute_tool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_with_truncation(
        self,
        tool_handler,
        mock_tool_manager
    ):
        """测试：截断过长的结果"""
        # Arrange
        long_content = "A" * 2000  # 创建一个很长的字符串
        tool_call_chunks = [
            {
                "id": "call_010",
                "type": "function",
                "function": {
                    "name": "search",
                    "arguments": json.dumps({"query": "test"})
                }
            }
        ]
        
        mock_tool_manager.execute_tool.return_value = {
            "success": True,
            "result": long_content
        }
        
        # Act
        results = await tool_handler.execute_tool_calls(
            tool_call_chunks,
            available_tokens=100  # 限制可用token
        )
        
        # Assert
        assert len(results) == 1
        assert len(results[0]["content"]) < len(long_content)
        assert "结果已截断" in results[0]["content"]
    
    def test_truncate_result_short_content(self, tool_handler):
        """测试：不需要截断的短内容"""
        # Arrange
        content = "Short content"
        available_tokens = 1000
        
        # Act
        result = tool_handler._truncate_result(content, available_tokens)
        
        # Assert
        assert result == content
    
    @patch('app.services.chat.tool_handler.estimate_tokens')
    def test_truncate_result_long_content(self, mock_estimate_tokens, tool_handler):
        """测试：截断长内容"""
        # Arrange
        long_content = "A" * 2000
        available_tokens = 100
        
        # Mock estimate_tokens返回大于available_tokens的值
        mock_estimate_tokens.side_effect = [500, 100]  # 第一次返回500(原始)，第二次返回100(截断后)
        
        # Act
        result = tool_handler._truncate_result(long_content, available_tokens)
        
        # Assert
        assert len(result) < len(long_content)
        assert "结果已截断" in result
        assert str(len(long_content)) in result  # 包含原始长度信息
    
    def test_format_tool_calls_for_message_success(self):
        """测试：格式化工具调用为消息格式"""
        # Arrange
        tool_call_chunks = [
            {
                "id": "call_011",
                "type": "function",
                "function": {
                    "name": "calculator",
                    "arguments": json.dumps({"expression": "1 + 1"})
                }
            },
            {
                "id": "call_012",
                "type": "function",
                "function": {
                    "name": "time",
                    "arguments": json.dumps({})
                }
            }
        ]
        
        # Act
        formatted = ToolCallHandler.format_tool_calls_for_message(tool_call_chunks)
        
        # Assert
        assert len(formatted) == 2
        assert formatted[0]["id"] == "call_011"
        assert formatted[0]["type"] == "function"
        assert formatted[0]["function"]["name"] == "calculator"
        assert formatted[1]["id"] == "call_012"
    
    def test_format_tool_calls_for_message_with_none(self):
        """测试：格式化包含None的工具调用"""
        # Arrange
        tool_call_chunks = [
            None,
            {
                "id": "call_013",
                "type": "function",
                "function": {
                    "name": "calculator",
                    "arguments": json.dumps({"expression": "1 + 1"})
                }
            },
            {},  # 空字典
            {
                "id": "call_014",
                "function": {}  # 没有name
            }
        ]
        
        # Act
        formatted = ToolCallHandler.format_tool_calls_for_message(tool_call_chunks)
        
        # Assert
        assert len(formatted) == 1  # 只有一个有效的工具调用
        assert formatted[0]["id"] == "call_013"
    
    def test_format_tool_calls_for_message_empty(self):
        """测试：格式化空列表"""
        # Arrange
        tool_call_chunks = []
        
        # Act
        formatted = ToolCallHandler.format_tool_calls_for_message(tool_call_chunks)
        
        # Assert
        assert len(formatted) == 0
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_no_function_name(
        self,
        tool_handler,
        mock_tool_manager
    ):
        """测试：没有function name的工具调用"""
        # Arrange
        tool_call_chunks = [
            {
                "id": "call_015",
                "type": "function",
                "function": {}  # 没有name
            }
        ]
        
        # Act
        results = await tool_handler.execute_tool_calls(tool_call_chunks)
        
        # Assert
        assert len(results) == 0
        mock_tool_manager.execute_tool.assert_not_called()

