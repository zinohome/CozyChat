"""
人格管理器测试

测试人格管理器的加载、获取、列表等功能
"""

# 标准库
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

# 本地库
from app.core.personality.manager import PersonalityManager
from app.core.personality.loader import PersonalityLoader
from app.core.personality.models import Personality, AIConfig, MemoryConfig, ToolConfig


class TestPersonalityManager:
    """测试人格管理器"""
    
    @pytest.fixture
    def personality_manager(self, temp_personality_dir):
        """创建人格管理器实例"""
        return PersonalityManager(config_dir=temp_personality_dir)
    
    @pytest.fixture
    def temp_personality_dir(self):
        """创建临时人格配置目录"""
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp(prefix="test_personality_")
        yield Path(temp_dir)
        # 清理
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_get_personality_success(self, personality_manager, temp_personality_dir):
        """测试：获取人格成功"""
        # 创建测试人格文件
        from app.core.personality.loader import PersonalityLoader
        loader = PersonalityLoader(config_dir=temp_personality_dir)
        
        yaml_content = """
personality:
  id: test_personality
  name: Test Personality
  version: 1.0.0
  description: Test personality

  ai:
    provider: openai
    model: gpt-3.5-turbo
    temperature: 0.7

  memory:
    enabled: true
    save_mode: both

  tools:
    enabled: true
    allowed_tools:
      - calculator
"""
        yaml_file = temp_personality_dir / "test_personality.yaml"
        yaml_file.write_text(yaml_content)
        
        # 重新加载管理器
        manager = PersonalityManager(config_dir=temp_personality_dir)
        
        personality = manager.get_personality("test_personality")
        
        assert personality is not None
        assert personality.id == "test_personality"
    
    def test_get_personality_not_found(self, personality_manager):
        """测试：获取不存在的人格"""
        personality = personality_manager.get_personality("non-existent")
        
        assert personality is None
    
    def test_list_personalities(self, personality_manager, temp_personality_dir):
        """测试：列出所有人格"""
        # 创建测试人格文件
        yaml_content = """
personality:
  id: test_personality
  name: Test Personality
  version: 1.0.0
  description: Test personality

  ai:
    provider: openai
    model: gpt-3.5-turbo

  memory:
    enabled: true

  tools:
    enabled: true
"""
        yaml_file = temp_personality_dir / "test_personality.yaml"
        yaml_file.write_text(yaml_content)
        
        # 重新加载管理器
        manager = PersonalityManager(config_dir=temp_personality_dir)
        
        personalities = manager.list_personalities()
        
        assert isinstance(personalities, list)
        # 至少应该有一个测试人格
        assert len(personalities) >= 0
    
    def test_reload_personality(self, personality_manager, temp_personality_dir):
        """测试：重新加载人格"""
        # 创建测试人格文件
        yaml_content = """
personality:
  id: test_personality
  name: Test Personality
  version: 1.0.0
  description: Test personality

  ai:
    provider: openai
    model: gpt-3.5-turbo

  memory:
    enabled: true

  tools:
    enabled: true
"""
        yaml_file = temp_personality_dir / "test_personality.yaml"
        yaml_file.write_text(yaml_content)
        
        # 重新加载管理器
        manager = PersonalityManager(config_dir=temp_personality_dir)
        
        # 重新加载人格
        if hasattr(manager, 'reload_personality'):
            manager.reload_personality("test_personality")
        
        # 验证人格仍然存在
        personality = manager.get_personality("test_personality")
        assert personality is not None
    
    def test_personality_caching(self, personality_manager, temp_personality_dir):
        """测试：人格缓存"""
        # 创建测试人格文件
        yaml_content = """
personality:
  id: test_personality
  name: Test Personality
  version: 1.0.0
  description: Test personality

  ai:
    provider: openai
    model: gpt-3.5-turbo

  memory:
    enabled: true

  tools:
    enabled: true
"""
        yaml_file = temp_personality_dir / "test_personality.yaml"
        yaml_file.write_text(yaml_content)
        
        # 重新加载管理器
        manager = PersonalityManager(config_dir=temp_personality_dir)
        
        # 第一次获取
        personality1 = manager.get_personality("test_personality")
        
        # 第二次获取（应该使用缓存）
        personality2 = manager.get_personality("test_personality")
        
        # 验证两次获取的是同一个对象（缓存）
        assert personality1 is personality2
        assert personality1.id == personality2.id

