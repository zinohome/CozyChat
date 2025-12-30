"""
配置适配器测试

测试配置适配器的功能，确保配置迁移后功能正常
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from app.utils.config_adapter import ConfigAdapter, get_config_adapter
from app.utils.config_loader import ConfigLoader


class TestConfigAdapter:
    """配置适配器测试类"""
    
    def test_get_memory_config_with_yaml(self):
        """测试：从YAML加载记忆配置"""
        # 创建mock配置加载器
        mock_loader = Mock(spec=ConfigLoader)
        mock_loader.load_memory_config.return_value = {
            "storage_mode": "dual",
            "async_write": False,
            "batch_size": 20,
            "dedup": {
                "enabled": False,
                "mode": "off"
            }
        }
        
        # 创建mock settings
        mock_settings = Mock()
        mock_settings.memory_storage_mode = "hybrid"
        mock_settings.memory_async_write = True
        mock_settings.memory_batch_size = 10
        mock_settings.memory_dedup_enabled = True
        mock_settings.memory_dedup_mode = "async"
        mock_settings.memory_dedup_content_threshold = 5
        mock_settings.memory_dedup_storage_threshold = 0.8
        mock_settings.memory_dedup_check_interval = 300
        
        # 创建适配器
        adapter = ConfigAdapter(config_loader=mock_loader)
        adapter.settings = mock_settings
        
        # 获取配置
        config = adapter.get_memory_config()
        
        # 验证：YAML配置应覆盖Settings
        assert config["storage_mode"] == "dual", "YAML应覆盖Settings"
        assert config["async_write"] == False, "YAML应覆盖Settings"
        assert config["batch_size"] == 20, "YAML应覆盖Settings"
        assert config["dedup"]["enabled"] == False, "YAML应覆盖Settings"
        assert config["dedup"]["mode"] == "off", "YAML应覆盖Settings"
    
    def test_get_memory_config_without_yaml(self):
        """测试：YAML不存在时使用Settings作为后备"""
        # 创建mock配置加载器（抛出异常模拟YAML不存在）
        mock_loader = Mock(spec=ConfigLoader)
        mock_loader.load_memory_config.side_effect = FileNotFoundError("Config file not found")
        
        # 创建mock settings
        mock_settings = Mock()
        mock_settings.memory_storage_mode = "hybrid"
        mock_settings.memory_async_write = True
        mock_settings.memory_batch_size = 10
        mock_settings.memory_dedup_enabled = True
        mock_settings.memory_dedup_mode = "async"
        mock_settings.memory_dedup_content_threshold = 5
        mock_settings.memory_dedup_storage_threshold = 0.8
        mock_settings.memory_dedup_check_interval = 300
        
        # 创建适配器
        adapter = ConfigAdapter(config_loader=mock_loader)
        adapter.settings = mock_settings
        
        # 获取配置
        config = adapter.get_memory_config()
        
        # 验证：应使用Settings值
        assert config["storage_mode"] == "hybrid", "应使用Settings默认值"
        assert config["async_write"] == True, "应使用Settings默认值"
        assert config["batch_size"] == 10, "应使用Settings默认值"
        assert config["dedup"]["enabled"] == True, "应使用Settings默认值"
    
    def test_get_session_config(self):
        """测试：获取会话配置"""
        mock_loader = Mock(spec=ConfigLoader)
        mock_loader.load_session_config.return_value = {
            "title": {
                "trigger_length": 15,
                "max_messages": 25
            }
        }
        
        mock_settings = Mock()
        mock_settings.session_title_trigger_length = 10
        mock_settings.session_title_max_messages = 20
        mock_settings.session_title_model = "gpt-4o-mini"
        mock_settings.session_title_temperature = 0.3
        mock_settings.session_title_max_tokens = 100
        
        adapter = ConfigAdapter(config_loader=mock_loader)
        adapter.settings = mock_settings
        
        config = adapter.get_session_config()
        
        # 验证：YAML应覆盖Settings
        assert config["title"]["trigger_length"] == 15, "YAML应覆盖Settings"
        assert config["title"]["max_messages"] == 25, "YAML应覆盖Settings"
        # 验证：Settings值应保留（如果YAML中没有）
        assert config["title"]["model"] == "gpt-4o-mini", "Settings值应保留"
    
    def test_get_context_config(self):
        """测试：获取上下文配置"""
        mock_loader = Mock(spec=ConfigLoader)
        mock_loader.load_context_config.return_value = {
            "max_tokens": 10000,
            "recent": {
                "message_count": 8
            }
        }
        
        mock_settings = Mock()
        mock_settings.context_intelligent_enabled = True
        mock_settings.context_recent_message_count = 6
        mock_settings.context_max_tokens = 8000
        mock_settings.context_summary_weight = 0.3
        mock_settings.context_memory_weight = 0.2
        mock_settings.context_summary_trigger_count = 50
        mock_settings.context_summary_window_size = 20
        mock_settings.context_summary_model = "gpt-4o-mini"
        mock_settings.context_summary_temperature = 0.3
        
        adapter = ConfigAdapter(config_loader=mock_loader)
        adapter.settings = mock_settings
        
        config = adapter.get_context_config()
        
        # 验证：YAML应覆盖Settings
        assert config["max_tokens"] == 10000, "YAML应覆盖Settings"
        assert config["recent"]["message_count"] == 8, "YAML应覆盖Settings"
        # 验证：Settings值应保留
        assert config["intelligent_enabled"] == True, "Settings值应保留"
    
    def test_get_performance_config(self):
        """测试：获取性能配置"""
        mock_loader = Mock(spec=ConfigLoader)
        mock_loader.load_performance_config.return_value = {
            "slow_request": {
                "threshold": 0.3,
                "delete_threshold": 0.6
            }
        }
        
        mock_settings = Mock()
        mock_settings.performance_slow_request_threshold = 0.2
        mock_settings.performance_slow_delete_threshold = 0.5
        
        adapter = ConfigAdapter(config_loader=mock_loader)
        adapter.settings = mock_settings
        
        config = adapter.get_performance_config()
        
        # 验证：YAML应覆盖Settings
        assert config["slow_request"]["threshold"] == 0.3, "YAML应覆盖Settings"
        assert config["slow_request"]["delete_threshold"] == 0.6, "YAML应覆盖Settings"
    
    def test_config_caching(self):
        """测试：配置缓存功能"""
        mock_loader = Mock(spec=ConfigLoader)
        mock_loader.load_memory_config.return_value = {"storage_mode": "dual"}
        
        mock_settings = Mock()
        mock_settings.memory_storage_mode = "hybrid"
        mock_settings.memory_async_write = True
        mock_settings.memory_batch_size = 10
        mock_settings.memory_dedup_enabled = True
        mock_settings.memory_dedup_mode = "async"
        mock_settings.memory_dedup_content_threshold = 5
        mock_settings.memory_dedup_storage_threshold = 0.8
        mock_settings.memory_dedup_check_interval = 300
        
        adapter = ConfigAdapter(config_loader=mock_loader)
        adapter.settings = mock_settings
        
        # 第一次调用
        config1 = adapter.get_memory_config()
        # 第二次调用
        config2 = adapter.get_memory_config()
        
        # 验证：应该只调用一次load_memory_config（缓存生效）
        assert mock_loader.load_memory_config.call_count == 1, "应使用缓存"
        assert config1 == config2, "缓存结果应一致"
    
    def test_get_config_adapter_singleton(self):
        """测试：get_config_adapter单例模式"""
        # 清除全局实例
        import app.utils.config_adapter
        app.utils.config_adapter._config_adapter = None
        
        adapter1 = get_config_adapter()
        adapter2 = get_config_adapter()
        
        # 验证：应该是同一个实例
        assert adapter1 is adapter2, "应该是单例"


class TestConfigMigrationRegression:
    """配置迁移回归测试"""
    
    def test_memory_config_backward_compatibility(self):
        """测试：记忆配置向后兼容性"""
        # 模拟YAML不存在的情况
        mock_loader = Mock(spec=ConfigLoader)
        mock_loader.load_memory_config.side_effect = FileNotFoundError()
        
        mock_settings = Mock()
        mock_settings.memory_storage_mode = "hybrid"
        mock_settings.memory_async_write = True
        mock_settings.memory_batch_size = 10
        mock_settings.memory_dedup_enabled = True
        mock_settings.memory_dedup_mode = "async"
        mock_settings.memory_dedup_content_threshold = 5
        mock_settings.memory_dedup_storage_threshold = 0.8
        mock_settings.memory_dedup_check_interval = 300
        
        adapter = ConfigAdapter(config_loader=mock_loader)
        adapter.settings = mock_settings
        
        config = adapter.get_memory_config()
        
        # 验证：所有配置项都应该有值（向后兼容）
        assert "storage_mode" in config
        assert "async_write" in config
        assert "batch_size" in config
        assert "dedup" in config
        assert isinstance(config["dedup"], dict), "dedup应该是字典"
        assert "enabled" in config["dedup"], "dedup应包含enabled"
        assert config["storage_mode"] == "hybrid", "应使用Settings默认值"
    
    def test_config_priority(self):
        """测试：配置优先级（YAML > Settings）"""
        mock_loader = Mock(spec=ConfigLoader)
        # YAML中有部分配置
        mock_loader.load_memory_config.return_value = {
            "storage_mode": "dual",  # 覆盖
            "batch_size": 20  # 覆盖
            # async_write 不在YAML中，应使用Settings
        }
        
        mock_settings = Mock()
        mock_settings.memory_storage_mode = "hybrid"
        mock_settings.memory_async_write = True
        mock_settings.memory_batch_size = 10
        mock_settings.memory_dedup_enabled = True
        mock_settings.memory_dedup_mode = "async"
        mock_settings.memory_dedup_content_threshold = 5
        mock_settings.memory_dedup_storage_threshold = 0.8
        mock_settings.memory_dedup_check_interval = 300
        
        adapter = ConfigAdapter(config_loader=mock_loader)
        adapter.settings = mock_settings
        
        config = adapter.get_memory_config()
        
        # 验证：YAML中的值应覆盖Settings
        assert config["storage_mode"] == "dual", "YAML应覆盖"
        assert config["batch_size"] == 20, "YAML应覆盖"
        # 验证：YAML中没有的值应使用Settings
        assert config["async_write"] == True, "Settings应作为后备"

