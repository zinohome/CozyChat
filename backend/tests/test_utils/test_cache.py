"""
缓存工具测试

测试CacheManager的功能
"""

# 标准库
import pytest
import json
from unittest.mock import MagicMock, Mock, patch

# 本地库
from app.utils.cache import CacheManager, cached


class TestCacheManager:
    """测试缓存管理器"""
    
    @pytest.fixture
    def cache_manager(self, mock_redis):
        """创建缓存管理器（使用Mock Redis）"""
        with patch('app.utils.cache.redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis
            manager = CacheManager()
            manager.client = mock_redis
            return manager
    
    def test_get_cache_hit(self, cache_manager, mock_redis):
        """测试：缓存命中"""
        mock_redis.get.return_value = json.dumps({"key": "value"})
        
        result = cache_manager.get("test_key")
        
        assert result == {"key": "value"}
        mock_redis.get.assert_called_once_with("test_key")
    
    def test_get_cache_miss(self, cache_manager, mock_redis):
        """测试：缓存未命中"""
        mock_redis.get.return_value = None
        
        result = cache_manager.get("test_key")
        
        assert result is None
        mock_redis.get.assert_called_once_with("test_key")
    
    def test_get_no_client(self):
        """测试：无Redis客户端时返回None"""
        manager = CacheManager()
        manager.client = None
        
        result = manager.get("test_key")
        
        assert result is None
    
    def test_set_success(self, cache_manager, mock_redis):
        """测试：设置缓存成功"""
        mock_redis.setex.return_value = True
        
        result = cache_manager.set("test_key", {"key": "value"}, ttl=300)
        
        assert result is True
        # 当有TTL时，使用setex
        mock_redis.setex.assert_called_once()
    
    def test_set_with_ttl(self, cache_manager, mock_redis):
        """测试：设置缓存（带TTL）"""
        mock_redis.setex.return_value = True
        
        result = cache_manager.set("test_key", "value", ttl=300)
        
        assert result is True
        mock_redis.setex.assert_called_once()
    
    def test_set_no_client(self):
        """测试：无Redis客户端时返回False"""
        manager = CacheManager()
        manager.client = None
        
        result = manager.set("test_key", "value")
        
        assert result is False
    
    def test_delete_success(self, cache_manager, mock_redis):
        """测试：删除缓存成功"""
        mock_redis.delete.return_value = 1
        
        result = cache_manager.delete("test_key")
        
        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")
    
    def test_delete_no_client(self):
        """测试：无Redis客户端时返回False"""
        manager = CacheManager()
        manager.client = None
        
        result = manager.delete("test_key")
        
        assert result is False
    
    def test_exists_success(self, cache_manager, mock_redis):
        """测试：检查缓存存在"""
        mock_redis.exists.return_value = 1
        
        result = cache_manager.exists("test_key")
        
        assert result is True
        mock_redis.exists.assert_called_once_with("test_key")
    
    def test_exists_no_client(self):
        """测试：无Redis客户端时返回False"""
        manager = CacheManager()
        manager.client = None
        
        result = manager.exists("test_key")
        
        assert result is False
    
    def test_increment_success(self, cache_manager, mock_redis):
        """测试：递增缓存值"""
        mock_redis.incrby.return_value = 2
        
        result = cache_manager.increment("test_key")
        
        assert result == 2
        mock_redis.incrby.assert_called_once_with("test_key", 1)
    
    def test_increment_no_client(self):
        """测试：无Redis客户端时返回None"""
        manager = CacheManager()
        manager.client = None
        
        result = manager.increment("test_key")
        
        assert result is None
    
    def test_clear_pattern(self, cache_manager, mock_redis):
        """测试：按模式清除缓存"""
        mock_redis.keys.return_value = ["key1", "key2", "key3"]
        mock_redis.delete.return_value = 3
        
        result = cache_manager.clear_pattern("test:*")
        
        assert result == 3
        mock_redis.keys.assert_called_once_with("test:*")
        mock_redis.delete.assert_called_once_with("key1", "key2", "key3")
    
    def test_clear_pattern_no_client(self):
        """测试：无Redis客户端时返回0"""
        manager = CacheManager()
        manager.client = None
        
        result = manager.clear_pattern("test:*")
        
        assert result == 0


class TestCachedDecorator:
    """测试@cached装饰器"""
    
    @pytest.fixture
    def mock_cache_manager(self, mock_redis):
        """Mock缓存管理器"""
        with patch('app.utils.cache.cache_manager') as mock_manager:
            mock_manager.client = mock_redis
            mock_manager.get.return_value = None
            mock_manager.set.return_value = True
            yield mock_manager
    
    def test_cached_decorator_cache_hit(self, mock_cache_manager, mock_redis):
        """测试：@cached装饰器缓存命中"""
        # Mock缓存返回值（通过cache_manager.get）
        mock_cache_manager.get.return_value = "cached_result"
        
        @cached("test_prefix", ttl=300)
        def test_function(arg1, arg2):
            return f"result_{arg1}_{arg2}"
        
        result = test_function("a", "b")
        
        assert result == "cached_result"
        mock_cache_manager.get.assert_called()
    
    def test_cached_decorator_cache_miss(self, mock_cache_manager, mock_redis):
        """测试：@cached装饰器缓存未命中"""
        # Mock缓存未命中
        mock_redis.get.return_value = None
        mock_cache_manager.get.return_value = None
        mock_cache_manager.set.return_value = True
        
        @cached("test_prefix", ttl=300)
        def test_function(arg1, arg2):
            return f"result_{arg1}_{arg2}"
        
        result = test_function("a", "b")
        
        assert result == "result_a_b"
        # 应该设置缓存（通过cache_manager.set）
        mock_cache_manager.set.assert_called()
    
    def test_cached_decorator_with_key_func(self, mock_cache_manager, mock_redis):
        """测试：@cached装饰器（自定义键函数）"""
        mock_redis.get.return_value = None
        mock_cache_manager.get.return_value = None
        
        def custom_key_func(*args, **kwargs):
            return f"custom_key_{args[0]}"
        
        @cached("test_prefix", ttl=300, key_func=custom_key_func)
        def test_function(arg1):
            return f"result_{arg1}"
        
        result = test_function("test")
        
        assert result == "result_test"
        # 验证使用了自定义键函数（通过cache_manager.get）
        mock_cache_manager.get.assert_called()

