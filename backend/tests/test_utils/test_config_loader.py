"""
配置加载器测试

测试ConfigLoader的功能
"""

# 标准库
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

# 本地库
from app.utils.config_loader import ConfigLoader


class TestConfigLoader:
    """测试配置加载器"""
    
    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """创建临时配置目录"""
        config_dir = tmp_path / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (config_dir / "models").mkdir(exist_ok=True)
        (config_dir / "tools").mkdir(exist_ok=True)
        (config_dir / "memory").mkdir(exist_ok=True)
        (config_dir / "voice").mkdir(exist_ok=True)
        
        return config_dir
    
    @pytest.fixture
    def config_loader(self, temp_config_dir):
        """创建配置加载器"""
        return ConfigLoader(config_dir=temp_config_dir)
    
    def test_load_yaml_success(self, config_loader, temp_config_dir):
        """测试：加载YAML文件成功"""
        yaml_content = """
test_key: test_value
nested:
  key1: value1
  key2: value2
"""
        yaml_file = temp_config_dir / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        config = config_loader.load_yaml(yaml_file)
        
        assert isinstance(config, dict)
        assert config["test_key"] == "test_value"
        assert config["nested"]["key1"] == "value1"
    
    def test_load_yaml_not_found(self, config_loader, temp_config_dir):
        """测试：加载不存在的YAML文件"""
        yaml_file = temp_config_dir / "nonexistent.yaml"
        
        with pytest.raises(FileNotFoundError):
            config_loader.load_yaml(yaml_file)
    
    def test_load_yaml_invalid(self, config_loader, temp_config_dir):
        """测试：加载无效的YAML文件"""
        yaml_content = """
invalid: yaml: content: [unclosed
"""
        yaml_file = temp_config_dir / "invalid.yaml"
        yaml_file.write_text(yaml_content)
        
        with pytest.raises(ValueError):
            config_loader.load_yaml(yaml_file)
    
    def test_load_yaml_caching(self, config_loader, temp_config_dir):
        """测试：YAML文件缓存"""
        yaml_content = """
test_key: test_value
"""
        yaml_file = temp_config_dir / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        # 第一次加载
        config1 = config_loader.load_yaml(yaml_file)
        
        # 修改文件内容
        yaml_file.write_text("test_key: modified_value")
        
        # 第二次加载（应该使用缓存）
        config2 = config_loader.load_yaml(yaml_file)
        
        # 缓存应该返回第一次的值
        assert config1 == config2
        assert config2["test_key"] == "test_value"
    
    def test_load_engine_config(self, config_loader, temp_config_dir):
        """测试：加载引擎配置"""
        yaml_content = """
engine:
  provider: openai
  model: gpt-4
  temperature: 0.7
"""
        yaml_file = temp_config_dir / "models" / "openai.yaml"
        yaml_file.write_text(yaml_content)
        
        config = config_loader.load_engine_config("openai")
        
        assert isinstance(config, dict)
        assert config["provider"] == "openai"
        assert config["model"] == "gpt-4"
        assert config["temperature"] == 0.7
    
    def test_load_tool_config(self, config_loader, temp_config_dir):
        """测试：加载工具配置"""
        builtin_content = """
tools:
  builtin:
    - calculator
    - time
    - weather
"""
        builtin_file = temp_config_dir / "tools" / "builtin.yaml"
        builtin_file.write_text(builtin_content)
        
        mcp_content = """
tools:
  mcp:
    enabled: true
"""
        mcp_file = temp_config_dir / "tools" / "mcp.yaml"
        mcp_file.write_text(mcp_content)
        
        config = config_loader.load_tool_config()
        
        assert isinstance(config, dict)
        # 如果文件存在，应该有builtin或mcp
        if builtin_file.exists():
            assert "builtin" in config or len(config) > 0
    
    def test_load_memory_config(self, config_loader, temp_config_dir):
        """测试：加载记忆配置"""
        yaml_content = """
memory:
  provider: chromadb
  persist_dir: ./data/chromadb
  collection_name: memories
"""
        # 记忆配置文件在config根目录
        yaml_file = temp_config_dir / "memory.yaml"
        yaml_file.write_text(yaml_content)
        
        config = config_loader.load_memory_config()
        
        assert isinstance(config, dict)
        assert config["provider"] == "chromadb"
        assert config["persist_dir"] == "./data/chromadb"
    
    def test_load_voice_config(self, config_loader, temp_config_dir):
        """测试：加载语音配置"""
        yaml_content = """
engines:
  stt:
    provider: openai
    model: whisper-1
  tts:
    provider: openai
    model: tts-1
"""
        yaml_file = temp_config_dir / "voice" / "stt.yaml"
        yaml_file.write_text(yaml_content)
        
        config = config_loader.load_voice_config("stt")
        
        assert isinstance(config, dict)
        assert config["provider"] == "openai"
        assert config["model"] == "whisper-1"
    
    def test_load_empty_yaml(self, config_loader, temp_config_dir):
        """测试：加载空YAML文件"""
        yaml_file = temp_config_dir / "empty.yaml"
        yaml_file.write_text("")
        
        config = config_loader.load_yaml(yaml_file)
        
        assert isinstance(config, dict)
        assert len(config) == 0

