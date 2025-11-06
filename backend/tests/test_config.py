"""
配置模块测试

测试应用配置加载和验证
"""

# 标准库
import os

# 第三方库
import pytest

# 本地库
from app.config.config import Settings, settings


class TestSettings:
    """测试Settings配置类"""
    
    def test_settings_instance(self):
        """测试配置实例创建"""
        assert settings is not None
        assert isinstance(settings, Settings)
    
    def test_app_name(self):
        """测试应用名称"""
        assert settings.app_name == "CozyChat"
    
    def test_cors_origins_parsing(self):
        """测试CORS origins解析"""
        assert isinstance(settings.cors_origins, list)
        assert len(settings.cors_origins) > 0
    
    def test_database_url_exists(self):
        """测试数据库URL配置存在"""
        assert settings.database_url is not None
        assert "postgresql" in settings.database_url
    
    def test_environment_detection(self):
        """测试环境检测"""
        if settings.app_env == "development":
            assert settings.is_development is True
            assert settings.is_production is False
        elif settings.app_env == "production":
            assert settings.is_development is False
            assert settings.is_production is True
    
    def test_log_level(self):
        """测试日志级别配置"""
        assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    
    def test_chroma_directory_created(self):
        """测试ChromaDB目录自动创建"""
        assert os.path.exists(settings.chroma_persist_directory)

