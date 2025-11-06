"""
AI引擎工厂测试

测试AI引擎工厂的创建功能
"""

# 第三方库
import pytest

# 本地库
from app.engines.ai import AIEngineFactory, OpenAIEngine
from app.engines.ai.ollama_engine import OllamaEngine


class TestAIEngineFactory:
    """测试AI引擎工厂"""
    
    def test_create_openai_engine(self):
        """测试创建OpenAI引擎"""
        engine = AIEngineFactory.create_engine(
            engine_type="openai",
            model="gpt-3.5-turbo"
        )
        
        assert isinstance(engine, OpenAIEngine)
        assert engine.model == "gpt-3.5-turbo"
        assert engine.engine_name == "openai"
    
    def test_create_ollama_engine(self):
        """测试创建Ollama引擎"""
        engine = AIEngineFactory.create_engine(
            engine_type="ollama",
            model="llama2"
        )
        
        assert isinstance(engine, OllamaEngine)
        assert engine.model == "llama2"
        assert engine.engine_name == "ollama"
    
    def test_create_engine_with_default_model(self):
        """测试使用默认模型创建引擎"""
        engine = AIEngineFactory.create_engine(engine_type="openai")
        assert engine.model == "gpt-3.5-turbo"  # 默认模型
        
        engine = AIEngineFactory.create_engine(engine_type="ollama")
        assert engine.model == "llama2"  # 默认模型
    
    def test_create_unsupported_engine(self):
        """测试创建不支持的引擎"""
        with pytest.raises(ValueError, match="Unsupported engine type"):
            AIEngineFactory.create_engine(
                engine_type="nonexistent",
                model="test"
            )
    
    def test_create_from_config(self):
        """测试从配置创建引擎"""
        config = {
            "type": "openai",
            "model": "gpt-4",
            "temperature": 0.8
        }
        
        engine = AIEngineFactory.create_from_config(config)
        
        assert isinstance(engine, OpenAIEngine)
        assert engine.model == "gpt-4"
    
    def test_create_from_config_missing_type(self):
        """测试从缺少type的配置创建引擎"""
        config = {"model": "gpt-4"}
        
        with pytest.raises(ValueError, match="must contain 'type' field"):
            AIEngineFactory.create_from_config(config)
    
    def test_list_available_engines(self):
        """测试列出可用引擎"""
        engines = AIEngineFactory.list_available_engines()
        
        assert "openai" in engines
        assert "ollama" in engines
        assert isinstance(engines, dict)

