"""
人格管理器覆盖率测试

补充personality/manager.py的未覆盖行测试
"""

# 标准库
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# 本地库
from app.core.personality.manager import PersonalityManager
from app.core.personality.loader import PersonalityLoader
from app.core.personality.models import Personality


class TestPersonalityManagerCoverage:
    """人格管理器覆盖率测试"""
    
    @pytest.fixture
    def temp_personality_dir(self):
        """创建临时人格配置目录"""
        temp_dir = tempfile.mkdtemp(prefix="test_personality_")
        yield Path(temp_dir)
        # 清理
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def personality_manager(self, temp_personality_dir):
        """创建人格管理器实例"""
        return PersonalityManager(config_dir=temp_personality_dir)
    
    def test_load_all_personalities_error(self, temp_personality_dir):
        """测试：加载所有人格（错误，覆盖50-56行）"""
        # Mock glob失败
        with patch.object(Path, 'glob', side_effect=Exception("File system error")):
            manager = PersonalityManager(config_dir=temp_personality_dir)
            # 应该能正常初始化，即使加载失败
            assert manager is not None
    
    def test_load_all_personalities_file_error(self, temp_personality_dir):
        """测试：加载所有人格（文件错误，覆盖50-54行）"""
        # 创建无效的YAML文件
        invalid_yaml = temp_personality_dir / "invalid.yaml"
        invalid_yaml.write_text("invalid: yaml: content: [")
        
        manager = PersonalityManager(config_dir=temp_personality_dir)
        # 应该能正常初始化，即使文件加载失败
        assert manager is not None
    
    def test_create_personality_success(self, personality_manager, temp_personality_dir):
        """测试：创建人格成功（覆盖90-117行）"""
        config = {
            "personality": {
                "id": "new_personality",
                "name": "New Personality",
                "version": "1.0.0",
                "description": "New personality",
                "ai": {
                    "provider": "openai",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7
                },
                "memory": {
                    "enabled": True,
                    "save_mode": "both",
                    "vector_db": "chromadb"
                },
                "tools": {
                    "enabled": True
                },
                "traits": {
                    "friendliness": 0.5,
                    "formality": 0.5,
                    "humor": 0.5,
                    "empathy": 0.5
                }
            }
        }
        
        personality = personality_manager.create_personality(config)
        
        assert personality is not None
        assert personality.id == "new_personality"
        assert personality.id in personality_manager.personalities
        
        # 验证文件已创建
        file_path = temp_personality_dir / "new_personality.yaml"
        assert file_path.exists()
    
    def test_create_personality_duplicate(self, personality_manager, temp_personality_dir):
        """测试：创建人格（重复ID，覆盖104-105行）"""
        config = {
            "personality": {
                "id": "test_personality",
                "name": "Test Personality",
                "version": "1.0.0",
                "description": "Test personality",
                "ai": {
                    "provider": "openai",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7
                },
                "memory": {
                    "enabled": True,
                    "save_mode": "both",
                    "vector_db": "chromadb"
                },
                "tools": {
                    "enabled": True
                },
                "traits": {
                    "friendliness": 0.5,
                    "formality": 0.5,
                    "humor": 0.5,
                    "empathy": 0.5
                }
            }
        }
        
        # 先创建一个
        personality_manager.create_personality(config)
        
        # 尝试创建重复的
        with pytest.raises(ValueError, match="already exists"):
            personality_manager.create_personality(config)
    
    def test_update_personality_success(self, personality_manager, temp_personality_dir):
        """测试：更新人格成功（覆盖119-150行）"""
        # 先创建一个人格
        config = {
            "personality": {
                "id": "test_personality",
                "name": "Test Personality",
                "version": "1.0.0",
                "description": "Test personality",
                "ai": {
                    "provider": "openai",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7
                },
                "memory": {
                    "enabled": True,
                    "save_mode": "both",
                    "vector_db": "chromadb"
                },
                "tools": {
                    "enabled": True
                },
                "traits": {
                    "friendliness": 0.5,
                    "formality": 0.5,
                    "humor": 0.5,
                    "empathy": 0.5
                }
            }
        }
        
        personality_manager.create_personality(config)
        
        # 更新人格
        updates = {
            "name": "Updated Personality",
            "description": "Updated description"
        }
        
        updated_personality = personality_manager.update_personality("test_personality", updates)
        
        assert updated_personality is not None
        assert updated_personality.name == "Updated Personality"
    
    def test_update_personality_not_found(self, personality_manager):
        """测试：更新人格（不存在，覆盖136-138行）"""
        updates = {
            "name": "Updated Personality"
        }
        
        with pytest.raises(ValueError, match="not found"):
            personality_manager.update_personality("nonexistent", updates)
    
    def test_delete_personality_success(self, personality_manager, temp_personality_dir):
        """测试：删除人格成功（覆盖152-169行）"""
        # 先创建一个人格
        config = {
            "personality": {
                "id": "test_personality",
                "name": "Test Personality",
                "version": "1.0.0",
                "description": "Test personality",
                "ai": {
                    "provider": "openai",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7
                },
                "memory": {
                    "enabled": True,
                    "save_mode": "both",
                    "vector_db": "chromadb"
                },
                "tools": {
                    "enabled": True
                },
                "traits": {
                    "friendliness": 0.5,
                    "formality": 0.5,
                    "humor": 0.5,
                    "empathy": 0.5
                }
            }
        }
        
        personality_manager.create_personality(config)
        
        # 验证文件存在
        file_path = temp_personality_dir / "test_personality.yaml"
        assert file_path.exists()
        
        # 删除人格
        personality_manager.delete_personality("test_personality")
        
        # 验证已删除
        assert "test_personality" not in personality_manager.personalities
        # 文件可能还存在（取决于实现），但人格应该已从内存中删除
    
    def test_delete_personality_not_found(self, personality_manager):
        """测试：删除人格（不存在，覆盖158-160行）"""
        # 删除不存在的人格应该不会抛出异常
        personality_manager.delete_personality("nonexistent")
        # 应该正常执行，不抛出异常
    
    def test_reload_personality_success(self, personality_manager, temp_personality_dir):
        """测试：重新加载人格成功（覆盖171-200行）"""
        # 先创建一个人格
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
    vector_db: chromadb

  tools:
    enabled: true

  traits:
    friendliness: 0.5
    formality: 0.5
    humor: 0.5
    empathy: 0.5
"""
        yaml_file = temp_personality_dir / "test_personality.yaml"
        yaml_file.write_text(yaml_content)
        
        # 重新加载管理器
        manager = PersonalityManager(config_dir=temp_personality_dir)
        
        # 重新加载人格
        reloaded = manager.reload_personality("test_personality")
        
        assert reloaded is not None
        assert reloaded.id == "test_personality"
    
    def test_reload_personality_not_found(self, personality_manager, temp_personality_dir):
        """测试：重新加载人格（文件不存在，覆盖180-183行）"""
        reloaded = personality_manager.reload_personality("nonexistent")
        
        assert reloaded is None
    
    def test_reload_personality_error(self, personality_manager, temp_personality_dir):
        """测试：重新加载人格（错误，覆盖195-200行）"""
        # 创建无效的YAML文件
        invalid_yaml = temp_personality_dir / "invalid.yaml"
        invalid_yaml.write_text("invalid: yaml: content: [")
        
        # 尝试重新加载
        reloaded = personality_manager.reload_personality("invalid")
        
        # 应该返回None（加载失败）
        assert reloaded is None
    
    def test_reload_all(self, personality_manager, temp_personality_dir):
        """测试：重新加载所有人格（覆盖202-206行）"""
        # 先创建一个人格
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
    vector_db: chromadb

  tools:
    enabled: true

  traits:
    friendliness: 0.5
    formality: 0.5
    humor: 0.5
    empathy: 0.5
"""
        yaml_file = temp_personality_dir / "test_personality.yaml"
        yaml_file.write_text(yaml_content)
        
        # 重新加载管理器
        manager = PersonalityManager(config_dir=temp_personality_dir)
        
        # 重新加载所有人格
        manager.reload_all()
        
        # 验证人格已重新加载
        assert "test_personality" in manager.personalities

