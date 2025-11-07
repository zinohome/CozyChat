"""
内置工具测试

测试内置工具（calculator、time、weather）的功能
"""

# 标准库
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# 本地库
from app.engines.tools.builtin.calculator import CalculatorTool
from app.engines.tools.builtin.time_tool import TimeTool
from app.engines.tools.builtin.weather_tool import WeatherTool
from app.engines.tools.base import ToolType


class TestCalculatorTool:
    """测试计算器工具"""
    
    @pytest.fixture
    def calculator(self):
        """创建计算器工具实例"""
        return CalculatorTool()
    
    @pytest.mark.asyncio
    async def test_calculate_addition(self, calculator):
        """测试：加法计算"""
        result = await calculator.execute(expression="2 + 3")
        
        assert isinstance(result, str)
        assert result == "5" or "5" in result
    
    @pytest.mark.asyncio
    async def test_calculate_subtraction(self, calculator):
        """测试：减法计算"""
        result = await calculator.execute(expression="10 - 4")
        
        assert isinstance(result, str)
        assert result == "6" or "6" in result
    
    @pytest.mark.asyncio
    async def test_calculate_multiplication(self, calculator):
        """测试：乘法计算"""
        result = await calculator.execute(expression="3 * 4")
        
        assert isinstance(result, str)
        assert result == "12" or "12" in result
    
    @pytest.mark.asyncio
    async def test_calculate_division(self, calculator):
        """测试：除法计算"""
        result = await calculator.execute(expression="15 / 3")
        
        assert isinstance(result, str)
        assert result == "5" or "5" in result
    
    @pytest.mark.asyncio
    async def test_calculate_complex_expression(self, calculator):
        """测试：复杂表达式计算"""
        result = await calculator.execute(expression="(2 + 3) * 4 - 1")
        
        assert isinstance(result, str)
        assert result == "19" or "19" in result
    
    @pytest.mark.asyncio
    async def test_calculate_invalid_expression(self, calculator):
        """测试：无效表达式"""
        result = await calculator.execute(expression="2 +")
        
        assert isinstance(result, str)
        assert "错误" in result or "error" in result.lower()
    
    @pytest.mark.asyncio
    async def test_calculate_division_by_zero(self, calculator):
        """测试：除以零"""
        result = await calculator.execute(expression="10 / 0")
        
        # 应该返回错误信息
        assert isinstance(result, str)
        assert "错误" in result or "error" in result.lower() or "除以零" in result
    
    def test_to_openai_function(self, calculator):
        """测试：转换为OpenAI函数格式"""
        func = calculator.to_openai_function()
        
        assert isinstance(func, dict)
        assert "type" in func or "function" in func
        assert "name" in func.get("function", {}) or "name" in func
        assert calculator.name in str(func)


class TestTimeTool:
    """测试时间工具"""
    
    @pytest.fixture
    def time_tool(self):
        """创建时间工具实例"""
        return TimeTool()
    
    @pytest.mark.asyncio
    async def test_get_current_time(self, time_tool):
        """测试：获取当前时间"""
        result = await time_tool.execute()
        
        assert isinstance(result, str)
        assert len(result) > 0
        # 验证返回的是时间格式字符串
    
    @pytest.mark.asyncio
    async def test_get_current_time_with_timezone(self, time_tool):
        """测试：获取带时区的当前时间"""
        result = await time_tool.execute(timezone="UTC")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_get_current_time_with_format(self, time_tool):
        """测试：获取格式化时间"""
        result = await time_tool.execute(format="datetime")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_to_openai_function(self, time_tool):
        """测试：转换为OpenAI函数格式"""
        func = time_tool.to_openai_function()
        
        assert isinstance(func, dict)
        assert "type" in func or "function" in func
        assert "name" in func.get("function", {}) or "name" in func
        assert time_tool.name in str(func)


class TestWeatherTool:
    """测试天气工具"""
    
    @pytest.fixture
    def weather_tool(self):
        """创建天气工具实例"""
        return WeatherTool()
    
    @pytest.fixture
    def mock_weather_api(self, mocker):
        """Mock天气API"""
        with patch('app.engines.tools.builtin.weather_tool.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "main": {"temp": 20.5, "humidity": 60},
                "weather": [{"description": "clear sky"}],
                "name": "Beijing"
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            yield mock_client
    
    @pytest.mark.asyncio
    async def test_get_weather_success(self, weather_tool, mock_weather_api):
        """测试：获取天气成功"""
        # 设置API密钥
        weather_tool.api_key = "test_key"
        
        result = await weather_tool.execute(city="Beijing")
        
        assert isinstance(result, str)
        assert len(result) > 0
        # 验证返回的是天气信息字符串
    
    @pytest.mark.asyncio
    async def test_get_weather_invalid_city(self, weather_tool, mock_weather_api):
        """测试：无效城市"""
        # 设置API密钥
        weather_tool.api_key = "test_key"
        
        # 设置mock返回404
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404")
        mock_weather_api.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await weather_tool.execute(city="InvalidCity")
        
        assert isinstance(result, str)
        assert "错误" in result or "error" in result.lower()
    
    @pytest.mark.asyncio
    async def test_get_weather_api_error(self, weather_tool, mock_weather_api):
        """测试：API错误"""
        # 设置API密钥
        weather_tool.api_key = "test_key"
        
        # 设置mock抛出异常
        import httpx
        mock_weather_api.return_value.__aenter__.return_value.get = AsyncMock(side_effect=httpx.HTTPStatusError("API Error", request=MagicMock(), response=MagicMock()))
        
        result = await weather_tool.execute(city="Beijing")
        
        assert isinstance(result, str)
        assert "错误" in result or "error" in result.lower()
    
    def test_to_openai_function(self, weather_tool):
        """测试：转换为OpenAI函数格式"""
        func = weather_tool.to_openai_function()
        
        assert isinstance(func, dict)
        assert "type" in func or "function" in func
        assert "name" in func.get("function", {}) or "name" in func
        assert weather_tool.name in str(func)

