"""
AI引擎工厂测试

测试AI引擎工厂的所有功能，包括：
- 创建OpenAI引擎
- 创建Ollama引擎
- 从配置创建引擎
- 列出可用引擎
"""

import pytest
from unittest.mock import patch, MagicMock

from app.engines.ai.factory import AIEngineFactory
from app.engines.ai.openai_engine import OpenAIEngine
from app.engines.ai.ollama_engine import OllamaEngine
from app.engines.ai.base import AIEngineBase


class TestAIEngineFactory:
    """测试AI引擎工厂"""
    
    @pytest.fixture
    def factory(self):
        """AI引擎工厂实例"""
        return AIEngineFactory()
    
    @pytest.fixture
    def openai_config(self):
        """OpenAI引擎配置"""
        return {
            "engine_type": "openai",
            "model": "gpt-3.5-turbo",
            "api_key": "test-api-key",
            "base_url": "https://api.openai.com/v1"
        }
    
    @pytest.fixture
    def ollama_config(self):
        """Ollama引擎配置"""
        return {
            "engine_type": "ollama",
            "model": "llama2",
            "base_url": "http://localhost:11434"
        }
    
    # ========== 创建引擎测试 ==========
    
    def test_create_openai_engine(self, factory, openai_config):
        """测试：创建OpenAI引擎"""
        engine = factory.create_engine(**openai_config)
        
        assert isinstance(engine, OpenAIEngine)
        assert engine.engine_name == "openai"
        assert engine.model == openai_config["model"]
        assert engine.api_key == openai_config["api_key"]
        assert engine.base_url == openai_config["base_url"]
    
    def test_create_ollama_engine(self, factory, ollama_config):
        """测试：创建Ollama引擎"""
        engine = factory.create_engine(**ollama_config)
        
        assert isinstance(engine, OllamaEngine)
        assert engine.engine_name == "ollama"
        assert engine.model == ollama_config["model"]
        assert engine.base_url == ollama_config["base_url"]
    
    def test_create_engine_invalid_type(self, factory):
        """测试：创建无效类型的引擎"""
        with pytest.raises(ValueError) as exc_info:
            factory.create_engine(engine_type="invalid_type")
        
        assert "Unsupported engine type" in str(exc_info.value)
    
    def test_create_engine_from_config(self, factory):
        """测试：从配置创建引擎"""
        config = {
            "type": "openai",  # 注意：应该是type而不是engine_type
            "model": "gpt-4",
            "api_key": "test-key",
            "base_url": "https://api.openai.com/v1"
        }
        
        engine = factory.create_from_config(config)
        
        assert isinstance(engine, OpenAIEngine)
        assert engine.model == "gpt-4"
    
    def test_list_available_engines(self, factory):
        """测试：列出可用引擎"""
        engines = factory.list_available_engines()
        
        assert isinstance(engines, dict)
        assert "openai" in engines
        assert "ollama" in engines
        # 引擎描述可能是类名或描述字符串
        assert "openai" in str(engines["openai"]).lower() or "OpenAI" in str(engines["openai"])
        assert "ollama" in str(engines["ollama"]).lower() or "Ollama" in str(engines["ollama"])
    
    def test_create_engine_with_default_config(self, factory):
        """测试：使用默认配置创建引擎"""
        # 直接测试创建引擎，使用默认模型
        engine = factory.create_engine(engine_type="openai", api_key="test-key")
        
        assert isinstance(engine, OpenAIEngine)
        assert engine.engine_name == "openai"
        assert engine.api_key == "test-key"

