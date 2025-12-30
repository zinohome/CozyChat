"""
工具基类覆盖率测试

补充tools/base.py的未覆盖行测试
"""

# 标准库
import pytest
from unittest.mock import MagicMock, patch

# 本地库
from app.engines.tools.base import Tool, ToolType


class MockTool(Tool):
    """Mock工具实现用于测试"""
    
    @property
    def name(self) -> str:
        return "mock_tool"
    
    @property
    def description(self) -> str:
        return "Mock tool for testing"
    
    @property
    def parameters(self) -> dict:
        return {
            "param1": {
                "type": "string",
                "description": "Parameter 1",
                "required": True
            },
            "param2": {
                "type": "integer",
                "description": "Parameter 2",
                "required": False,
                "default": 0
            }
        }
    
    async def execute(self, **kwargs):
        """执行工具"""
        return {"result": "success", "params": kwargs}


class TestToolBaseCoverage:
    """工具基类覆盖率测试"""
    
    def test_tool_init(self):
        """测试：工具初始化（覆盖34-44行）"""
        tool = MockTool()
        assert tool.tool_type == ToolType.BUILTIN
        assert tool.name == "mock_tool"
    
    def test_tool_init_with_type(self):
        """测试：工具初始化（指定类型，覆盖34行）"""
        tool = MockTool(tool_type=ToolType.MCP)
        assert tool.tool_type == ToolType.MCP
    
    def test_tool_name_property(self):
        """测试：工具名称属性（覆盖46-54行）"""
        tool = MockTool()
        assert tool.name == "mock_tool"
    
    def test_tool_description_property(self):
        """测试：工具描述属性（覆盖56-64行）"""
        tool = MockTool()
        assert tool.description == "Mock tool for testing"
    
    def test_tool_parameters_property(self):
        """测试：工具参数属性（覆盖66-84行）"""
        tool = MockTool()
        params = tool.parameters
        assert isinstance(params, dict)
        assert "param1" in params
        assert "param2" in params
    
    @pytest.mark.asyncio
    async def test_tool_execute(self):
        """测试：工具执行（覆盖86-100行）"""
        tool = MockTool()
        result = await tool.execute(param1="test", param2=123)
        assert result["result"] == "success"
        assert result["params"]["param1"] == "test"
        assert result["params"]["param2"] == 123
    
    def test_to_openai_function(self):
        """测试：转换为OpenAI function格式（覆盖102-129行）"""
        tool = MockTool()
        openai_func = tool.to_openai_function()
        
        assert openai_func["type"] == "function"
        assert "function" in openai_func
        assert openai_func["function"]["name"] == "mock_tool"
        assert openai_func["function"]["description"] == "Mock tool for testing"
        assert "parameters" in openai_func["function"]
        assert "properties" in openai_func["function"]["parameters"]
        assert "required" in openai_func["function"]["parameters"]
        assert "param1" in openai_func["function"]["parameters"]["required"]
        assert "param2" not in openai_func["function"]["parameters"]["required"]
    
    def test_get_required_params(self):
        """测试：获取必需参数（覆盖131-140行）"""
        tool = MockTool()
        required = tool._get_required_params()
        
        assert isinstance(required, list)
        assert "param1" in required
        assert "param2" not in required
    
    def test_validate_parameters_success(self):
        """测试：验证参数（成功，覆盖142-150行）"""
        tool = MockTool()
        # 应该不抛出异常
        tool.validate_parameters(param1="test", param2=123)
    
    def test_validate_parameters_missing_required(self):
        """测试：验证参数（缺少必需参数，覆盖152-157行）"""
        tool = MockTool()
        with pytest.raises(ValueError, match="Missing required parameters"):
            tool.validate_parameters(param2=123)
    
    def test_validate_parameters_unknown_param(self):
        """测试：验证参数（未知参数，覆盖160-165行）"""
        tool = MockTool()
        # 应该不抛出异常，只记录警告
        with patch('app.engines.tools.base.logger') as mock_logger:
            tool.validate_parameters(param1="test", unknown_param="value")
            # 验证警告被记录
            mock_logger.warning.assert_called()
    
    def test_validate_parameters_type_check_string(self):
        """测试：验证参数（类型检查：string，覆盖167-186行）"""
        tool = MockTool()
        # 正确的类型
        tool.validate_parameters(param1="test", param2=123)
        
        # 错误的类型
        with pytest.raises(ValueError, match="must be of type"):
            tool.validate_parameters(param1=123, param2=123)
    
    def test_validate_parameters_type_check_integer(self):
        """测试：验证参数（类型检查：integer，覆盖172-186行）"""
        tool = MockTool()
        # 正确的类型
        tool.validate_parameters(param1="test", param2=123)
        
        # 错误的类型
        with pytest.raises(ValueError, match="must be of type"):
            tool.validate_parameters(param1="test", param2="123")
    
    def test_validate_parameters_type_check_number(self):
        """测试：验证参数（类型检查：number，覆盖175-186行）"""
        # 创建一个接受number类型的工具
        class NumberTool(MockTool):
            @property
            def parameters(self):
                return {
                    "value": {
                        "type": "number",
                        "description": "Numeric value",
                        "required": True
                    }
                }
        
        tool = NumberTool()
        # 正确的类型（int或float）
        tool.validate_parameters(value=123)
        tool.validate_parameters(value=123.45)
        
        # 错误的类型
        with pytest.raises(ValueError, match="must be of type"):
            tool.validate_parameters(value="123")
    
    def test_validate_parameters_type_check_boolean(self):
        """测试：验证参数（类型检查：boolean，覆盖176-186行）"""
        # 创建一个接受boolean类型的工具
        class BooleanTool(MockTool):
            @property
            def parameters(self):
                return {
                    "flag": {
                        "type": "boolean",
                        "description": "Boolean flag",
                        "required": True
                    }
                }
        
        tool = BooleanTool()
        # 正确的类型
        tool.validate_parameters(flag=True)
        tool.validate_parameters(flag=False)
        
        # 错误的类型
        with pytest.raises(ValueError, match="must be of type"):
            tool.validate_parameters(flag="true")
    
    def test_validate_parameters_type_check_array(self):
        """测试：验证参数（类型检查：array，覆盖177-186行）"""
        # 创建一个接受array类型的工具
        class ArrayTool(MockTool):
            @property
            def parameters(self):
                return {
                    "items": {
                        "type": "array",
                        "description": "Array of items",
                        "required": True
                    }
                }
        
        tool = ArrayTool()
        # 正确的类型
        tool.validate_parameters(items=[1, 2, 3])
        
        # 错误的类型
        with pytest.raises(ValueError, match="must be of type"):
            tool.validate_parameters(items="[1, 2, 3]")
    
    def test_validate_parameters_type_check_object(self):
        """测试：验证参数（类型检查：object，覆盖178-186行）"""
        # 创建一个接受object类型的工具
        class ObjectTool(MockTool):
            @property
            def parameters(self):
                return {
                    "data": {
                        "type": "object",
                        "description": "Object data",
                        "required": True
                    }
                }
        
        tool = ObjectTool()
        # 正确的类型
        tool.validate_parameters(data={"key": "value"})
        
        # 错误的类型
        with pytest.raises(ValueError, match="must be of type"):
            tool.validate_parameters(data='{"key": "value"}')

