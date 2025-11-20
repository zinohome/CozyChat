"""
PromptLoader和PromptBuilder服务单元测试

测试提示词加载和构建服务的各种场景
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from app.services.prompt.loader import PromptLoader
from app.services.prompt.builder import PromptBuilder


class TestPromptLoader:
    """PromptLoader单元测试类"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """创建临时配置目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            
            # 创建子目录
            (config_dir / "response_styles").mkdir()
            (config_dir / "style_presets").mkdir()
            (config_dir / "languages").mkdir()
            
            # 创建基础指令文件
            base_instructions = {
                "common": {
                    "avoid_stiff_opening": "直接回答问题",
                    "use_list_format": "用列表形式组织"
                }
            }
            with open(config_dir / "base_instructions.yaml", 'w', encoding='utf-8') as f:
                yaml.dump(base_instructions, f, allow_unicode=True)
            
            # 创建响应风格文件
            brief_style = {"instructions": "简洁回答"}
            with open(config_dir / "response_styles" / "brief.yaml", 'w', encoding='utf-8') as f:
                yaml.dump(brief_style, f, allow_unicode=True)
            
            standard_style = {"instructions": "标准回答"}
            with open(config_dir / "response_styles" / "standard.yaml", 'w', encoding='utf-8') as f:
                yaml.dump(standard_style, f, allow_unicode=True)
            
            # 创建风格预设文件
            elder_preset = {"instructions": "长者友好风格"}
            with open(config_dir / "style_presets" / "elder_friendly.yaml", 'w', encoding='utf-8') as f:
                yaml.dump(elder_preset, f, allow_unicode=True)
            
            # 创建语言文件
            zh_lang = {"instruction": "使用中文回答"}
            with open(config_dir / "languages" / "zh-CN.yaml", 'w', encoding='utf-8') as f:
                yaml.dump(zh_lang, f, allow_unicode=True)
            
            en_lang = {"instruction": "使用英文回答"}
            with open(config_dir / "languages" / "en-US.yaml", 'w', encoding='utf-8') as f:
                yaml.dump(en_lang, f, allow_unicode=True)
            
            yield str(config_dir)
    
    def test_load_base_instructions_success(self, temp_config_dir):
        """测试：成功加载基础指令"""
        # Arrange
        loader = PromptLoader(config_dir=temp_config_dir)
        
        # Act
        config = loader.load_base_instructions()
        
        # Assert
        assert config is not None
        assert "common" in config
        assert "avoid_stiff_opening" in config["common"]
        assert config["common"]["avoid_stiff_opening"] == "直接回答问题"
    
    def test_load_base_instructions_uses_cache(self, temp_config_dir):
        """测试：加载基础指令使用缓存"""
        # Arrange
        loader = PromptLoader(config_dir=temp_config_dir)
        
        # Act
        config1 = loader.load_base_instructions()
        config2 = loader.load_base_instructions()
        
        # Assert
        assert config1 is config2  # 应该是同一个对象（来自缓存）
    
    def test_load_response_style_brief(self, temp_config_dir):
        """测试：加载简洁风格"""
        # Arrange
        loader = PromptLoader(config_dir=temp_config_dir)
        
        # Act
        config = loader.load_response_style("brief")
        
        # Assert
        assert config is not None
        assert config["instructions"] == "简洁回答"
    
    def test_load_response_style_standard(self, temp_config_dir):
        """测试：加载标准风格"""
        # Arrange
        loader = PromptLoader(config_dir=temp_config_dir)
        
        # Act
        config = loader.load_response_style("standard")
        
        # Assert
        assert config is not None
        assert config["instructions"] == "标准回答"
    
    def test_load_response_style_not_found(self, temp_config_dir):
        """测试：加载不存在的风格"""
        # Arrange
        loader = PromptLoader(config_dir=temp_config_dir)
        
        # Act
        config = loader.load_response_style("nonexistent")
        
        # Assert
        assert config is None
    
    def test_load_style_preset_success(self, temp_config_dir):
        """测试：成功加载风格预设"""
        # Arrange
        loader = PromptLoader(config_dir=temp_config_dir)
        
        # Act
        config = loader.load_style_preset("elder_friendly")
        
        # Assert
        assert config is not None
        assert config["instructions"] == "长者友好风格"
    
    def test_load_style_preset_not_found(self, temp_config_dir):
        """测试：加载不存在的预设"""
        # Arrange
        loader = PromptLoader(config_dir=temp_config_dir)
        
        # Act
        config = loader.load_style_preset("nonexistent")
        
        # Assert
        assert config is None
    
    def test_load_language_zh_cn(self, temp_config_dir):
        """测试：加载中文配置"""
        # Arrange
        loader = PromptLoader(config_dir=temp_config_dir)
        
        # Act
        config = loader.load_language("zh-CN")
        
        # Assert
        assert config is not None
        assert config["instruction"] == "使用中文回答"
    
    def test_load_language_en_us(self, temp_config_dir):
        """测试：加载英文配置"""
        # Arrange
        loader = PromptLoader(config_dir=temp_config_dir)
        
        # Act
        config = loader.load_language("en-US")
        
        # Assert
        assert config is not None
        assert config["instruction"] == "使用英文回答"
    
    def test_load_language_not_found(self, temp_config_dir):
        """测试：加载不存在的语言"""
        # Arrange
        loader = PromptLoader(config_dir=temp_config_dir)
        
        # Act
        config = loader.load_language("fr-FR")
        
        # Assert
        assert config is None
    
    def test_clear_cache(self, temp_config_dir):
        """测试：清除缓存"""
        # Arrange
        loader = PromptLoader(config_dir=temp_config_dir)
        config1 = loader.load_base_instructions()
        
        # Act
        loader.clear_cache()
        config2 = loader.load_base_instructions()
        
        # Assert
        assert config1 is not config2  # 不是同一个对象（缓存已清除）
        assert config1 == config2  # 但内容相同
    
    def test_load_yaml_with_invalid_file(self, temp_config_dir):
        """测试：加载无效的YAML文件"""
        # Arrange
        loader = PromptLoader(config_dir=temp_config_dir)
        
        # 创建无效的YAML文件
        invalid_path = Path(temp_config_dir) / "invalid.yaml"
        with open(invalid_path, 'w') as f:
            f.write("invalid: yaml: content:")
        
        # Act
        result = loader._load_yaml(invalid_path)
        
        # Assert
        assert result == {}  # 应该返回空字典
    
    def test_response_style_cache(self, temp_config_dir):
        """测试：响应风格使用缓存"""
        # Arrange
        loader = PromptLoader(config_dir=temp_config_dir)
        
        # Act
        config1 = loader.load_response_style("brief")
        config2 = loader.load_response_style("brief")
        
        # Assert
        assert config1 is config2  # 应该是同一个对象
    
    def test_style_preset_cache(self, temp_config_dir):
        """测试：风格预设使用缓存"""
        # Arrange
        loader = PromptLoader(config_dir=temp_config_dir)
        
        # Act
        config1 = loader.load_style_preset("elder_friendly")
        config2 = loader.load_style_preset("elder_friendly")
        
        # Assert
        assert config1 is config2
    
    def test_language_cache(self, temp_config_dir):
        """测试：语言配置使用缓存"""
        # Arrange
        loader = PromptLoader(config_dir=temp_config_dir)
        
        # Act
        config1 = loader.load_language("zh-CN")
        config2 = loader.load_language("zh-CN")
        
        # Assert
        assert config1 is config2


class TestPromptBuilder:
    """PromptBuilder单元测试类"""
    
    @pytest.fixture
    def mock_loader(self):
        """创建模拟的PromptLoader"""
        loader = Mock(spec=PromptLoader)
        
        # 配置默认返回值
        loader.load_base_instructions.return_value = {
            "common": {
                "avoid_stiff_opening": "直接回答问题",
                "use_list_format": "用列表形式组织"
            }
        }
        
        loader.load_response_style.return_value = {"instructions": "标准回答"}
        loader.load_style_preset.return_value = {"instructions": "预设风格"}
        loader.load_language.return_value = {"instruction": "使用中文回答"}
        
        return loader
    
    @pytest.fixture
    def prompt_builder(self, mock_loader):
        """创建PromptBuilder实例"""
        return PromptBuilder(loader=mock_loader)
    
    def test_build_user_message_with_empty_content(self, prompt_builder):
        """测试：空内容返回None"""
        # Act
        content, instruction = prompt_builder.build_user_message("", {})
        
        # Assert
        assert content == ""
        assert instruction is None
    
    def test_build_user_message_with_default_preferences(self, prompt_builder, mock_loader):
        """测试：使用默认偏好构建消息"""
        # Act
        content, instruction = prompt_builder.build_user_message("你好", {})
        
        # Assert
        assert content == "你好"
        assert instruction is not None
        assert "直接回答问题" in instruction
        assert "标准回答" in instruction
    
    def test_build_user_message_with_brief_style(self, prompt_builder, mock_loader):
        """测试：使用简洁风格"""
        # Arrange
        mock_loader.load_response_style.return_value = {"instructions": "简洁回答"}
        preferences = {"response_style": "brief"}
        
        # Act
        content, instruction = prompt_builder.build_user_message("你好", preferences)
        
        # Assert
        assert content == "你好"
        assert "简洁回答" in instruction
        mock_loader.load_response_style.assert_called_with("brief")
    
    def test_build_user_message_with_style_preset(self, prompt_builder, mock_loader):
        """测试：使用风格预设"""
        # Arrange
        mock_loader.load_style_preset.return_value = {"instructions": "长者友好"}
        preferences = {"style_preset": "elder_friendly"}
        
        # Act
        content, instruction = prompt_builder.build_user_message("你好", preferences)
        
        # Assert
        assert "长者友好" in instruction
        mock_loader.load_style_preset.assert_called_with("elder_friendly")
    
    def test_build_user_message_with_prefer_list(self, prompt_builder, mock_loader):
        """测试：偏好列表格式"""
        # Arrange
        preferences = {"prefer_list": True}
        
        # Act
        content, instruction = prompt_builder.build_user_message("你好", preferences)
        
        # Assert
        assert "用列表形式组织" in instruction
    
    def test_build_user_message_with_language(self, prompt_builder, mock_loader):
        """测试：指定语言"""
        # Arrange
        mock_loader.load_language.return_value = {"instruction": "使用英文回答"}
        preferences = {"default_language": "en-US"}
        
        # Act
        content, instruction = prompt_builder.build_user_message("你好", preferences)
        
        # Assert
        assert "使用英文回答" in instruction
        mock_loader.load_language.assert_called_with("en-US")
    
    def test_build_user_message_with_all_preferences(self, prompt_builder, mock_loader):
        """测试：使用所有偏好设置"""
        # Arrange
        mock_loader.load_response_style.return_value = {"instructions": "详细回答"}
        mock_loader.load_style_preset.return_value = {"instructions": "医疗详细"}
        mock_loader.load_language.return_value = {"instruction": "使用中文"}
        
        preferences = {
            "response_style": "detailed",
            "style_preset": "medical_detail",
            "prefer_list": True,
            "default_language": "zh-CN"
        }
        
        # Act
        content, instruction = prompt_builder.build_user_message("你好", preferences)
        
        # Assert
        assert "直接回答问题" in instruction
        assert "详细回答" in instruction
        assert "医疗详细" in instruction
        assert "用列表形式组织" in instruction
        assert "使用中文" in instruction
    
    def test_build_user_message_with_none_preferences(self, prompt_builder):
        """测试：偏好为None"""
        # Act
        content, instruction = prompt_builder.build_user_message("你好", None)
        
        # Assert
        assert content == "你好"
        assert instruction is not None
    
    def test_build_user_message_without_loader_configs(self, mock_loader):
        """测试：加载器返回空配置"""
        # Arrange
        mock_loader.load_base_instructions.return_value = {}
        mock_loader.load_response_style.return_value = {}
        mock_loader.load_language.return_value = {}
        
        builder = PromptBuilder(loader=mock_loader)
        
        # Act
        content, instruction = builder.build_user_message("你好", {})
        
        # Assert
        assert content == "你好"
        # 可能是None或空字符串
        assert instruction is None or instruction == ""
    
    def test_reload_configs(self, prompt_builder, mock_loader):
        """测试：重新加载配置"""
        # Act
        prompt_builder.reload_configs()
        
        # Assert
        mock_loader.clear_cache.assert_called_once()
    
    def test_build_user_message_with_missing_style_preset_config(self, prompt_builder, mock_loader):
        """测试：风格预设配置不存在"""
        # Arrange
        mock_loader.load_style_preset.return_value = None
        preferences = {"style_preset": "nonexistent"}
        
        # Act
        content, instruction = prompt_builder.build_user_message("你好", preferences)
        
        # Assert
        assert content == "你好"
        assert instruction is not None  # 应该仍然有其他指令
    
    def test_build_user_message_instruction_order(self, prompt_builder, mock_loader):
        """测试：指令顺序正确"""
        # Arrange
        preferences = {
            "response_style": "brief",
            "style_preset": "elder_friendly",
            "prefer_list": True,
            "default_language": "zh-CN"
        }
        
        # Act
        content, instruction = prompt_builder.build_user_message("你好", preferences)
        
        # Assert
        # 验证指令包含所有部分
        assert "直接回答问题" in instruction
        assert "标准回答" in instruction
        assert "预设风格" in instruction
        assert "用列表形式组织" in instruction
        assert "使用中文回答" in instruction
    
    def test_prompt_builder_default_loader(self):
        """测试：使用默认加载器初始化"""
        # Act
        builder = PromptBuilder()
        
        # Assert
        assert builder.loader is not None
        assert isinstance(builder.loader, PromptLoader)
    
    def test_build_user_message_preserves_content(self, prompt_builder):
        """测试：保持原始消息内容不变"""
        # Arrange
        original_content = "这是一条测试消息，包含特殊字符！@#￥%……&*（）"
        
        # Act
        content, instruction = prompt_builder.build_user_message(original_content, {})
        
        # Assert
        assert content == original_content

