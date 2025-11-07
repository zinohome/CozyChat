"""
查询优化器测试

测试QueryOptimizer的功能
"""

# 标准库
import pytest
from unittest.mock import MagicMock, Mock, patch

# 本地库
from app.utils.query_optimizer import eager_load, use_index_hint, query_cache


class TestEagerLoadDecorator:
    """测试@eager_load装饰器"""
    
    def test_eager_load_decorator(self):
        """测试：@eager_load装饰器"""
        @eager_load("messages", "user")
        def test_query(session_id: str, db):
            return {"session_id": session_id}
        
        # 装饰器应该不改变函数行为（简化实现）
        result = test_query("session123", Mock())
        
        assert result == {"session_id": "session123"}
    
    def test_eager_load_without_db(self):
        """测试：@eager_load装饰器（无db参数）"""
        @eager_load("messages")
        def test_function(arg1):
            return f"result_{arg1}"
        
        result = test_function("test")
        
        assert result == "result_test"


class TestUseIndexHintDecorator:
    """测试@use_index_hint装饰器"""
    
    def test_use_index_hint_decorator(self):
        """测试：@use_index_hint装饰器"""
        @use_index_hint("idx_users_username")
        def test_query(username: str, db):
            return {"username": username}
        
        # 装饰器应该不改变函数行为（简化实现）
        result = test_query("testuser", Mock())
        
        assert result == {"username": "testuser"}


class TestQueryCacheDecorator:
    """测试@query_cache装饰器"""
    
    @pytest.fixture
    def mock_cache_manager(self, mock_redis):
        """Mock缓存管理器"""
        with patch('app.utils.query_optimizer.cache_manager') as mock_manager:
            mock_manager.client = mock_redis
            mock_manager.get.return_value = None
            mock_manager.set.return_value = True
            yield mock_manager
    
    def test_query_cache_decorator_cache_hit(self, mock_cache_manager, mock_redis):
        """测试：@query_cache装饰器缓存命中"""
        import json
        
        # Mock缓存返回值（query_cache通过cache_manager.get获取）
        mock_cache_manager.get.return_value = {"cached": "data"}
        
        @query_cache(ttl=600)
        def test_query(user_id: str):
            return {"user_id": user_id}
        
        result = test_query("user123")
        
        # 缓存命中时返回缓存的值
        assert result == {"cached": "data"}
        mock_cache_manager.get.assert_called()
    
    def test_query_cache_decorator_cache_miss(self, mock_cache_manager, mock_redis):
        """测试：@query_cache装饰器缓存未命中"""
        mock_redis.get.return_value = None
        
        @query_cache(ttl=600)
        def test_query(user_id: str):
            return {"user_id": user_id}
        
        result = test_query("user123")
        
        assert result == {"user_id": "user123"}
        # 应该设置缓存（通过cache_manager.set）
        # 注意：query_cache内部使用cache_manager，不是直接调用redis
        mock_cache_manager.set.assert_called()
    
    def test_query_cache_with_custom_key_func(self, mock_cache_manager, mock_redis):
        """测试：@query_cache装饰器（自定义键函数）"""
        mock_redis.get.return_value = None
        
        def custom_key_func(*args, **kwargs):
            return f"custom_key_{args[0]}"
        
        @query_cache(ttl=600, key_func=custom_key_func)
        def test_query(user_id: str):
            return {"user_id": user_id}
        
        result = test_query("user123")
        
        assert result == {"user_id": "user123"}
        # 验证使用了自定义键函数（通过cache_manager.get）
        mock_cache_manager.get.assert_called()

