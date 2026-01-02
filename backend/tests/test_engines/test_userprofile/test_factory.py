"""
UserProfileEngineFactory单元测试

测试用户画像引擎工厂的所有方法
"""

# 标准库
from typing import Dict, Any

# 第三方库
import pytest

# 本地库
from app.engines.userprofile.factory import UserProfileEngineFactory
from app.engines.userprofile.base import UserProfileEngineBase
from app.engines.userprofile.memobase_engine import MemobaseUserProfileEngine


class TestUserProfileEngineFactory:
    """UserProfileEngineFactory测试类"""
    
    @pytest.fixture
    def memobase_config(self) -> Dict[str, Any]:
        """Memobase引擎配置"""
        return {
            "project_url": "http://localhost:8019",
            "api_key": "test-api-key"
        }
    
    def test_create_engine_memobase(self, memobase_config: Dict[str, Any]):
        """测试：创建Memobase引擎"""
        engine = UserProfileEngineFactory.create_engine(
            provider="memobase",
            config=memobase_config
        )
        
        assert engine is not None
        assert isinstance(engine, MemobaseUserProfileEngine)
        assert isinstance(engine, UserProfileEngineBase)
        assert engine.project_url == "http://localhost:8019"
        assert engine.api_key == "test-api-key"
    
    def test_create_engine_memobase_case_insensitive(self, memobase_config: Dict[str, Any]):
        """测试：创建Memobase引擎（大小写不敏感）"""
        engine1 = UserProfileEngineFactory.create_engine(
            provider="MEMOBASE",
            config=memobase_config
        )
        engine2 = UserProfileEngineFactory.create_engine(
            provider="Memobase",
            config=memobase_config
        )
        engine3 = UserProfileEngineFactory.create_engine(
            provider="  memobase  ",
            config=memobase_config
        )
        
        assert isinstance(engine1, MemobaseUserProfileEngine)
        assert isinstance(engine2, MemobaseUserProfileEngine)
        assert isinstance(engine3, MemobaseUserProfileEngine)
    
    def test_create_engine_unknown_provider(self, memobase_config: Dict[str, Any]):
        """测试：创建未知引擎提供商（应该抛出异常）"""
        with pytest.raises(ValueError) as exc_info:
            UserProfileEngineFactory.create_engine(
                provider="unknown_provider",
                config=memobase_config
            )
        
        assert "Unknown userprofile engine provider" in str(exc_info.value)
        assert "memobase" in str(exc_info.value)
    
    def test_create_engine_empty_provider(self, memobase_config: Dict[str, Any]):
        """测试：创建引擎（空提供商）"""
        with pytest.raises(ValueError):
            UserProfileEngineFactory.create_engine(
                provider="",
                config=memobase_config
            )
    
    def test_create_engine_empty_config(self):
        """测试：创建引擎（空配置）"""
        engine = UserProfileEngineFactory.create_engine(
            provider="memobase",
            config={}
        )
        
        assert engine is not None
        assert isinstance(engine, MemobaseUserProfileEngine)
        # 使用默认配置
        assert engine.project_url == "http://localhost:8019"
        assert engine.api_key == "secret"
    
    def test_create_engine_with_custom_config(self):
        """测试：创建引擎（自定义配置）"""
        custom_config = {
            "project_url": "http://custom:8020",
            "api_key": "custom-key"
        }
        
        engine = UserProfileEngineFactory.create_engine(
            provider="memobase",
            config=custom_config
        )
        
        assert engine.project_url == "http://custom:8020"
        assert engine.api_key == "custom-key"
