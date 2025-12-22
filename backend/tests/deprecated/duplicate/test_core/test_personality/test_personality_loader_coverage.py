"""
人格加载器覆盖率测试

补充personality/loader.py的未覆盖行测试
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


class TestPersonalityLoaderCoverage:
    """人格加载器覆盖率测试"""
    
    @pytest.fixture
    def temp_personality_dir(self):
        """创建临时人格配置目录"""
        temp_dir = tempfile.mkdtemp(prefix="test_personality_")
        yield Path(temp_dir)
        # 清理
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def personality_loader(self, temp_personality_dir):
        """创建人格加载器实例"""
        return PersonalityLoader(config_dir=str(temp_personality_dir))
    
    def test_init_with_config_dir(self, temp_personality_dir):
        """测试：初始化（带配置目录，覆盖33行）"""
        loader = PersonalityLoader(config_dir=str(temp_personality_dir))
        assert loader.config_dir == temp_personality_dir
    
    def test_load_from_file_invalid_config(self, personality_loader, temp_personality_dir):
        """测试：从文件加载（无效配置，覆盖64行）"""
        # 创建无效配置的YAML文件
        invalid_yaml = temp_personality_dir / "invalid.yaml"
        invalid_yaml.write_text("invalid: config")
        
        with pytest.raises(ValueError):
            personality_loader.load_from_file(invalid_yaml)
    
    def test_load_from_file_yaml_error(self, personality_loader, temp_personality_dir):
        """测试：从文件加载（YAML错误，覆盖78-81行）"""
        # 创建无效YAML文件
        invalid_yaml = temp_personality_dir / "invalid.yaml"
        invalid_yaml.write_text("invalid: yaml: content: [")
        
        with pytest.raises(ValueError):
            personality_loader.load_from_file(invalid_yaml)
    
    def test_load_from_dict_with_personality_key(self, personality_loader):
        """测试：从字典加载（带personality键，覆盖95-97行）"""
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
        
        personality = personality_loader.load_from_dict(config)
        assert personality is not None
        assert personality.id == "test_personality"
    
    def test_load_from_dict_without_personality_key(self, personality_loader):
        """测试：从字典加载（不带personality键，覆盖99行）"""
        config = {
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
        
        personality = personality_loader.load_from_dict(config)
        assert personality is not None
        assert personality.id == "test_personality"
    
    def test_load_from_dict_error(self, personality_loader):
        """测试：从字典加载（错误，覆盖111-112行）"""
        config = {"invalid": "config"}
        
        with pytest.raises(ValueError):
            personality_loader.load_from_dict(config)
    
    def test_save_to_file_with_path(self, personality_loader, temp_personality_dir):
        """测试：保存到文件（带路径，覆盖121-146行）"""
        # 创建测试人格
        config = {
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
        
        personality = personality_loader.load_from_dict(config)
        file_path = temp_personality_dir / "custom_path.yaml"
        
        personality_loader.save_to_file(personality, file_path)
        
        assert file_path.exists()
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_config = yaml.safe_load(f)
            assert "personality" in saved_config
    
    def test_save_to_file_without_path(self, personality_loader, temp_personality_dir):
        """测试：保存到文件（不带路径，覆盖122行）"""
        # 创建测试人格
        config = {
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
        
        personality = personality_loader.load_from_dict(config)
        
        personality_loader.save_to_file(personality)
        
        file_path = temp_personality_dir / "test_personality.yaml"
        assert file_path.exists()
    
    def test_save_to_file_error(self, personality_loader, temp_personality_dir):
        """测试：保存到文件（错误，覆盖144-146行）"""
        # 创建测试人格
        config = {
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
        
        personality = personality_loader.load_from_dict(config)
        file_path = temp_personality_dir / "invalid" / "path.yaml"
        
        # Mock open失败
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with pytest.raises(IOError):
                personality_loader.save_to_file(personality, file_path)
    
    def test_validate_personality_missing_id(self, personality_loader):
        """测试：验证人格（缺少ID，覆盖158行）"""
        config = {
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
        
        with pytest.raises(ValueError, match="Personality id is required"):
            personality_loader.load_from_dict(config)
    
    def test_validate_personality_missing_name(self, personality_loader):
        """测试：验证人格（缺少名称，覆盖160-161行）"""
        config = {
            "id": "test_personality",
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
        
        with pytest.raises(ValueError, match="Personality name is required"):
            personality_loader.load_from_dict(config)
    
    def test_validate_personality_invalid_trait(self, personality_loader):
        """测试：验证人格（无效trait，覆盖164-168行）"""
        config = {
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
                "friendliness": 1.5,  # 无效值
                "formality": 0.5,
                "humor": 0.5,
                "empathy": 0.5
            }
        }
        
        with pytest.raises(ValueError, match="Trait.*must be between 0 and 1"):
            personality_loader.load_from_dict(config)
    
    def test_validate_personality_invalid_provider(self, personality_loader):
        """测试：验证人格（无效provider，覆盖171-172行）"""
        config = {
            "id": "test_personality",
            "name": "Test Personality",
            "version": "1.0.0",
            "description": "Test personality",
            "ai": {
                "provider": "invalid_provider",
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
        
        with pytest.raises(ValueError, match="Unsupported AI provider"):
            personality_loader.load_from_dict(config)
    
    def test_validate_personality_invalid_temperature(self, personality_loader):
        """测试：验证人格（无效temperature，覆盖174-175行）"""
        config = {
            "id": "test_personality",
            "name": "Test Personality",
            "version": "1.0.0",
            "description": "Test personality",
            "ai": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "temperature": 3.0  # 无效值
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
        
        with pytest.raises(ValueError, match="Temperature must be between 0 and 2"):
            personality_loader.load_from_dict(config)
    
    def test_validate_personality_invalid_vector_db(self, personality_loader):
        """测试：验证人格（无效vector_db，覆盖178-179行）"""
        config = {
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
                "vector_db": "invalid_db"
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
        
        with pytest.raises(ValueError, match="Unsupported vector DB"):
            personality_loader.load_from_dict(config)
    
    def test_validate_personality_invalid_save_mode(self, personality_loader):
        """测试：验证人格（无效save_mode，覆盖181-182行）"""
        config = {
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
                "save_mode": "invalid_mode",
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
        
        with pytest.raises(ValueError, match="Invalid save_mode"):
            personality_loader.load_from_dict(config)

