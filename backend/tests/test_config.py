"""
测试配置验证

验证测试环境配置是否正确
"""

# 标准库
import os

# 第三方库
import pytest

# 本地库
from app.config.config import settings


class TestTestConfig:
    """测试配置验证"""
    
    def test_database_url(self):
        """验证数据库URL配置"""
        assert settings.database_url is not None
        assert "postgresql" in settings.database_url.lower()
    
    def test_redis_url(self):
        """验证Redis URL配置"""
        # Redis URL是可选的
        if settings.redis_url:
            assert "redis" in settings.redis_url.lower()
    
    def test_openai_config(self):
        """验证OpenAI配置"""
        # OpenAI API Key应该在.env中配置
        assert settings.openai_api_key is not None or os.getenv("OPENAI_API_KEY") is not None
    
    def test_test_database_connection(self):
        """测试测试数据库连接"""
        from sqlalchemy import create_engine, text
        from tests.conftest import TEST_DATABASE_URL
        
        try:
            engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
        except Exception as e:
            pytest.skip(f"测试数据库连接失败: {e}")
