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
        from unittest.mock import patch, MagicMock
        # 方法1：patch _connect方法，让它在__init__时不会真正连接Redis
        original_connect = CacheManager._connect
        
        def mock_connect(self):
            """Mock _connect方法，不真正连接Redis"""
            self.pool = MagicMock()
            self.client = mock_redis
        
        # 临时替换_connect方法
        CacheManager._connect = mock_connect
        try:
            manager = CacheManager()
            # 确保client是mock_redis
            manager.client = mock_redis
            return manager
        finally:
            # 恢复原始方法
            CacheManager._connect = original_connect
    
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
        # 需要patch装饰器内部使用的cache_manager
        with patch('app.utils.cache.cache_manager') as mock_manager:
            mock_manager.client = mock_redis
            mock_manager.get.return_value = None
            mock_manager.set.return_value = True
            # 确保patch在装饰器定义时生效
            yield mock_manager
    
    def test_cached_decorator_cache_hit(self, mock_cache_manager, mock_redis):
        """测试：@cached装饰器缓存命中"""
        # Mock缓存返回值：第一次返回None（缓存未命中），第二次返回缓存值
        call_count = [0]
        def mock_get(key):
            call_count[0] += 1
            if call_count[0] == 1:
                return None  # 第一次：缓存未命中
            else:
                return "cached_result"  # 后续：缓存命中
        
        mock_cache_manager.get.side_effect = mock_get
        mock_cache_manager.set.return_value = True
        
        # 在patch生效后定义装饰器
        @cached("test_prefix", ttl=300)
        def test_function(arg1, arg2):
            return f"result_{arg1}_{arg2}"
        
        # 第一次调用：缓存未命中，应该调用函数并设置缓存
        result1 = test_function("a", "b")
        assert result1 == "result_a_b"
        assert mock_cache_manager.get.call_count == 1
        assert mock_cache_manager.set.call_count == 1
        
        # 第二次调用：缓存命中，应该返回缓存值
        result2 = test_function("a", "b")
        assert result2 == "cached_result"
        assert mock_cache_manager.get.call_count == 2
        # 第二次调用时不应该再调用set
        assert mock_cache_manager.set.call_count == 1
    
    def test_cached_decorator_cache_miss(self, mock_cache_manager, mock_redis):
        """测试：@cached装饰器缓存未命中"""
        # Mock缓存未命中
        mock_cache_manager.get.return_value = None
        mock_cache_manager.set.return_value = True
        
        # 在patch生效后定义装饰器
        @cached("test_prefix", ttl=300)
        def test_function(arg1, arg2):
            return f"result_{arg1}_{arg2}"
        
        result = test_function("a", "b")
        
        assert result == "result_a_b"
        # 应该先尝试获取缓存（通过cache_manager.get）
        assert mock_cache_manager.get.call_count == 1
        # 然后设置缓存（通过cache_manager.set）
        assert mock_cache_manager.set.call_count == 1
        # 验证set被调用时传入了正确的参数
        call_args = mock_cache_manager.set.call_args
        assert call_args is not None
        assert "test_prefix" in call_args[0][0] or "test_prefix" in str(call_args)
    
    def test_cached_decorator_with_key_func(self, mock_cache_manager, mock_redis):
        """测试：@cached装饰器（自定义键函数）"""
        mock_cache_manager.get.return_value = None
        mock_cache_manager.set.return_value = True
        
        def custom_key_func(*args, **kwargs):
            return f"custom_key_{args[0]}"
        
        # 在patch生效后定义装饰器
        @cached("test_prefix", ttl=300, key_func=custom_key_func)
        def test_function(arg1):
            return f"result_{arg1}"
        
        result = test_function("test")
        
        assert result == "result_test"
        # 验证使用了自定义键函数（通过cache_manager.get）
        assert mock_cache_manager.get.call_count == 1
        # 验证get被调用时使用了自定义键
        get_call_args = mock_cache_manager.get.call_args[0][0]
        assert get_call_args == "custom_key_test"
        # 验证set被调用
        assert mock_cache_manager.set.call_count == 1
        # 验证set被调用时使用了相同的自定义键
        set_call_args = mock_cache_manager.set.call_args[0][0]
        assert set_call_args == "custom_key_test"

