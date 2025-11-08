"""
内置工具工厂测试

测试builtin/factory.py的功能
"""

# 标准库
import pytest
import os
from unittest.mock import patch, MagicMock

# 本地库
from app.engines.tools.builtin import factory
from app.engines.tools.registry import ToolRegistry


class TestBuiltinFactory:
    """测试内置工具工厂"""
    
    def setup_method(self):
        """每个测试前清理"""
        # 清理注册表
        ToolRegistry._tools.clear()
        # 重新注册内置工具
        from app.engines.tools.builtin.calculator import CalculatorTool
        from app.engines.tools.builtin.time_tool import TimeTool
        from app.engines.tools.builtin.weather_tool import WeatherTool
        
        ToolRegistry.register("calculator", CalculatorTool)
        ToolRegistry.register("time", TimeTool)
        ToolRegistry.register("weather", WeatherTool)
    
    def test_register_builtin_tools_success(self):
        """测试：注册内置工具（成功，覆盖23-46行）"""
        # Mock配置加载器
        mock_config = {
            "builtin": [
                {"name": "calculator"},
                {"name": "time"},
                {"name": "weather"}
            ]
        }
        
        with patch('app.engines.tools.builtin.factory.get_config_loader') as mock_loader:
            mock_config_loader = MagicMock()
            mock_config_loader.load_tool_config.return_value = mock_config
            mock_loader.return_value = mock_config_loader
            
            # 重新注册
            factory.register_builtin_tools()
            
            # 验证工具已注册
            assert "calculator" in ToolRegistry.list_tools()
            assert "time" in ToolRegistry.list_tools()
            assert "weather" in ToolRegistry.list_tools()
    
    def test_register_builtin_tools_missing_tool(self):
        """测试：注册内置工具（YAML中定义但代码中未注册，覆盖37-41行）"""
        mock_config = {
            "builtin": [
                {"name": "calculator"},
                {"name": "nonexistent_tool"}  # 在YAML中定义但未在代码中注册
            ]
        }
        
        with patch('app.engines.tools.builtin.factory.get_config_loader') as mock_loader:
            with patch('app.engines.tools.builtin.factory.logger') as mock_logger:
                mock_config_loader = MagicMock()
                mock_config_loader.load_tool_config.return_value = mock_config
                mock_loader.return_value = mock_config_loader
                
                # 重新注册
                factory.register_builtin_tools()
                
                # 验证警告被记录
                mock_logger.warning.assert_called()
    
    def test_register_builtin_tools_error(self):
        """测试：注册内置工具（配置加载错误，覆盖48-52行）"""
        with patch('app.engines.tools.builtin.factory.get_config_loader') as mock_loader:
            with patch('app.engines.tools.builtin.factory.logger') as mock_logger:
                mock_loader.side_effect = Exception("Config load error")
                
                # 重新注册（应该不抛出异常）
                factory.register_builtin_tools()
                
                # 验证警告被记录
                mock_logger.warning.assert_called()
    
    def test_create_builtin_tool_success(self):
        """测试：创建内置工具（成功，覆盖59-82行）"""
        tool = factory.create_builtin_tool("calculator")
        
        assert tool is not None
        assert tool.name == "calculator"
    
    def test_create_builtin_tool_not_found(self):
        """测试：创建内置工具（不存在，覆盖69-71行）"""
        tool = factory.create_builtin_tool("nonexistent_tool")
        
        assert tool is None
    
    def test_create_builtin_tool_weather_with_api_key(self):
        """测试：创建内置工具（Weather工具，带API密钥，覆盖74-77行）"""
        # Mock设置
        with patch('app.engines.tools.builtin.factory.settings') as mock_settings:
            mock_settings.openweather_api_key = "test_api_key"
            
            tool = factory.create_builtin_tool("weather", api_key="custom_key")
            
            assert tool is not None
            assert tool.name == "weather"
    
    def test_create_builtin_tool_weather_without_api_key(self):
        """测试：创建内置工具（Weather工具，不带API密钥，覆盖76-77行）"""
        # Mock设置
        with patch('app.engines.tools.builtin.factory.settings') as mock_settings:
            mock_settings.openweather_api_key = "test_api_key"
            
            tool = factory.create_builtin_tool("weather")
            
            # 应该使用settings中的API密钥
            assert tool is not None
    
    def test_create_builtin_tool_initialization_error(self):
        """测试：创建内置工具（初始化错误，覆盖79-82行）"""
        # Mock工具类抛出异常
        with patch.object(ToolRegistry, 'get_tool_class') as mock_get:
            class ErrorTool:
                def __init__(self, **kwargs):
                    raise Exception("Initialization error")
            
            mock_get.return_value = ErrorTool
            
            tool = factory.create_builtin_tool("error_tool")
            
            assert tool is None

