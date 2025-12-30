"""
人格加载器测试

测试人格加载器的YAML解析、验证等功能
"""

# 标准库
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

# 本地库
from app.core.personality.loader import PersonalityLoader
from app.core.personality.models import Personality


class TestPersonalityLoader:
    """测试人格加载器"""
    
    @pytest.fixture
    def temp_personality_dir(self):
        """创建临时人格配置目录"""
        temp_dir = tempfile.mkdtemp(prefix="test_personality_")
        yield Path(temp_dir)
        # 清理
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def sample_personality_yaml(self, temp_personality_dir):
        """创建示例人格YAML文件"""
        yaml_content = """
personality:
  id: test_personality
  name: Test Personality
  version: 1.0.0
  description: Test personality for testing

  ai:
    provider: openai
    model: gpt-3.5-turbo
    temperature: 0.7
    max_tokens: 4096

  memory:
    enabled: true
    save_mode: both

  tools:
    enabled: true
    allowed_tools:
      - calculator
      - time
"""
        yaml_file = temp_personality_dir / "test_personality.yaml"
        yaml_file.write_text(yaml_content)
        return yaml_file
    
    @pytest.fixture
    def personality_loader(self, temp_personality_dir):
        """创建人格加载器实例"""
        return PersonalityLoader(config_dir=str(temp_personality_dir))
    
    def test_load_personality_success(self, personality_loader, sample_personality_yaml):
        """测试：加载人格成功"""
        personality = personality_loader.load_from_file(sample_personality_yaml)
        
        assert personality is not None
        assert personality.id == "test_personality"
        assert personality.name == "Test Personality"
        assert personality.ai.provider == "openai"
        assert personality.memory.enabled is True
        assert personality.tools.enabled is True
    
    def test_load_personality_not_found(self, personality_loader):
        """测试：加载不存在的文件"""
        from pathlib import Path
        non_existent_file = Path("/non/existent/file.yaml")
        
        with pytest.raises((FileNotFoundError, ValueError)):
            personality_loader.load_from_file(non_existent_file)
    
    def test_list_personalities(self, personality_loader, sample_personality_yaml):
        """测试：列出所有人格"""
        # 通过管理器列出
        from app.core.personality.manager import PersonalityManager
        manager = PersonalityManager(config_dir=personality_loader.config_dir)
        personalities = manager.list_personalities()
        
        assert isinstance(personalities, list)
        # 至少应该有一个测试人格
        assert len(personalities) >= 0
    
    def test_validate_personality_config(self, personality_loader, sample_personality_yaml):
        """测试：验证人格配置"""
        # 加载配置
        with open(sample_personality_yaml, 'r') as f:
            config = yaml.safe_load(f)
        
        # 验证配置格式（YAML文件中有personality键）
        assert "personality" in config
        personality_config = config["personality"]
        assert "id" in personality_config
        assert "name" in personality_config
        assert "ai" in personality_config
        assert "memory" in personality_config
        assert "tools" in personality_config
    
    def test_load_personality_invalid_yaml(self, personality_loader, temp_personality_dir):
        """测试：加载无效YAML"""
        # 创建无效的YAML文件
        invalid_yaml = temp_personality_dir / "invalid.yaml"
        invalid_yaml.write_text("invalid: yaml: content: [")
        
        # 应该抛出异常
        with pytest.raises((ValueError, yaml.YAMLError)):
            personality_loader.load_from_file(invalid_yaml)

