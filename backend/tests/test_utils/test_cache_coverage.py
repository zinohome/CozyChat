"""
缓存工具覆盖率测试

补充cache.py的未覆盖行测试
"""

# 标准库
import pytest
import json
from unittest.mock import MagicMock, Mock, patch
from datetime import timedelta

# 本地库
from app.utils.cache import CacheManager, cached


class TestCacheManagerCoverage:
    """缓存管理器覆盖率测试"""
    
    @pytest.fixture
    def cache_manager(self, mock_redis):
        """创建缓存管理器（使用Mock Redis）"""
        with patch('app.utils.cache.redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis
            manager = CacheManager()
            manager.client = mock_redis
            return manager
    
    def test_connect_redis_ping_error(self):
        """测试：连接Redis（ping错误，覆盖73-79行）"""
        with patch('app.utils.cache.redis.Redis') as mock_redis_class:
            with patch('app.utils.cache.ConnectionPool') as mock_pool:
                mock_redis_instance = MagicMock()
                mock_redis_instance.ping.side_effect = Exception("Connection error")
                mock_redis_class.return_value = mock_redis_instance
                
                manager = CacheManager()
                
                # 验证client为None（连接失败）
                assert manager.client is None
    
    def test_connect_redis_connection_error(self):
        """测试：连接Redis（连接错误，覆盖81-87行）"""
        with patch('app.utils.cache.ConnectionPool') as mock_pool:
            mock_pool.from_url.side_effect = Exception("Connection pool error")
            
            manager = CacheManager()
            
            # 验证client为None（连接失败）
            assert manager.client is None
    
    def test_get_json_decode_error(self, cache_manager, mock_redis):
        """测试：获取缓存（JSON解析错误，覆盖109-110行）"""
        # Mock返回非JSON字符串
        mock_redis.get.return_value = "not a json string"
        
        result = cache_manager.get("test_key")
        
        # 应该返回原始值
        assert result == "not a json string"
    
    def test_get_type_error(self, cache_manager, mock_redis):
        """测试：获取缓存（类型错误，覆盖109-110行）"""
        # Mock返回非字符串值
        mock_redis.get.return_value = 123
        
        result = cache_manager.get("test_key")
        
        # 应该返回原始值
        assert result == 123
    
    def test_get_exception(self, cache_manager, mock_redis):
        """测试：获取缓存（异常，覆盖112-114行）"""
        mock_redis.get.side_effect = Exception("Redis error")
        
        result = cache_manager.get("test_key")
        
        assert result is None
    
    def test_set_with_timedelta_ttl(self, cache_manager, mock_redis):
        """测试：设置缓存（timedelta TTL，覆盖143-144行）"""
        mock_redis.setex.return_value = True
        
        result = cache_manager.set("test_key", "value", ttl=timedelta(seconds=300))
        
        assert result is True
        mock_redis.setex.assert_called_once_with("test_key", 300, "value")
    
    def test_set_without_ttl(self, cache_manager, mock_redis):
        """测试：设置缓存（无TTL，覆盖151-152行）"""
        mock_redis.set.return_value = True
        
        result = cache_manager.set("test_key", "value")
        
        assert result is True
        mock_redis.set.assert_called_once_with("test_key", "value")
    
    def test_set_exception(self, cache_manager, mock_redis):
        """测试：设置缓存（异常，覆盖156-158行）"""
        mock_redis.setex.side_effect = Exception("Redis error")
        
        result = cache_manager.set("test_key", "value", ttl=300)
        
        assert result is False
    
    def test_delete_exception(self, cache_manager, mock_redis):
        """测试：删除缓存（异常，覆盖174-176行）"""
        mock_redis.delete.side_effect = Exception("Redis error")
        
        result = cache_manager.delete("test_key")
        
        assert result is False
    
    def test_exists_exception(self, cache_manager, mock_redis):
        """测试：检查缓存存在（异常，覆盖192-194行）"""
        mock_redis.exists.side_effect = Exception("Redis error")
        
        result = cache_manager.exists("test_key")
        
        assert result is False
    
    def test_clear_pattern_with_keys(self, cache_manager, mock_redis):
        """测试：清除模式缓存（有键，覆盖209-211行）"""
        mock_redis.keys.return_value = ["key1", "key2"]
        mock_redis.delete.return_value = 2
        
        result = cache_manager.clear_pattern("test:*")
        
        assert result == 2
        mock_redis.keys.assert_called_once_with("test:*")
        mock_redis.delete.assert_called_once_with("key1", "key2")
    
    def test_clear_pattern_no_keys(self, cache_manager, mock_redis):
        """测试：清除模式缓存（无键，覆盖209-212行）"""
        mock_redis.keys.return_value = []
        
        result = cache_manager.clear_pattern("test:*")
        
        assert result == 0
    
    def test_clear_pattern_exception(self, cache_manager, mock_redis):
        """测试：清除模式缓存（异常，覆盖212-215行）"""
        mock_redis.keys.side_effect = Exception("Redis error")
        
        result = cache_manager.clear_pattern("test:*")
        
        assert result == 0
    
    def test_increment_exception(self, cache_manager, mock_redis):
        """测试：递增缓存（异常，覆盖232-234行）"""
        mock_redis.incrby.side_effect = Exception("Redis error")
        
        result = cache_manager.increment("test_key")
        
        assert result is None
    
    def test_get_or_set_cache_hit(self, cache_manager, mock_redis):
        """测试：获取或设置缓存（缓存命中，覆盖256-259行）"""
        # Mock缓存命中
        mock_redis.get.return_value = json.dumps({"cached": "value"})
        
        def test_func():
            return {"new": "value"}
        
        result = cache_manager.get_or_set("test_key", test_func, ttl=300)
        
        # 应该返回缓存的值
        assert result == {"cached": "value"}
        # 不应该调用函数
        mock_redis.setex.assert_not_called()
    
    def test_get_or_set_cache_miss(self, cache_manager, mock_redis):
        """测试：获取或设置缓存（缓存未命中，覆盖261-268行）"""
        # Mock缓存未命中
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        
        def test_func():
            return {"new": "value"}
        
        result = cache_manager.get_or_set("test_key", test_func, ttl=300)
        
        # 应该返回函数的值
        assert result == {"new": "value"}
        # 应该设置缓存
        mock_redis.setex.assert_called_once()
    
    def test_get_or_set_cache_miss_none_value(self, cache_manager, mock_redis):
        """测试：获取或设置缓存（缓存未命中，值为None，覆盖265-268行）"""
        # Mock缓存未命中
        mock_redis.get.return_value = None
        
        def test_func():
            return None
        
        result = cache_manager.get_or_set("test_key", test_func, ttl=300)
        
        # 应该返回None
        assert result is None
        # 不应该设置缓存（值为None）
        mock_redis.setex.assert_not_called()
    
    def test_close(self):
        """测试：关闭连接（覆盖270-274行）"""
        with patch('app.utils.cache.redis.Redis') as mock_redis_class:
            with patch('app.utils.cache.ConnectionPool') as mock_pool_class:
                mock_pool = MagicMock()
                mock_pool_class.from_url.return_value = mock_pool
                
                manager = CacheManager()
                manager.pool = mock_pool
                
                manager.close()
                
                # 验证disconnect被调用
                mock_pool.disconnect.assert_called_once()
    
    def test_cached_decorator_with_key_func(self, mock_redis):
        """测试：@cached装饰器（自定义键函数，覆盖302-303行）"""
        with patch('app.utils.cache.cache_manager') as mock_manager:
            mock_manager.client = mock_redis
            mock_manager.get.return_value = None
            mock_manager.set.return_value = True
            
            def custom_key_func(*args, **kwargs):
                return f"custom_{args[0]}"
            
            @cached("test_prefix", ttl=300, key_func=custom_key_func)
            def test_function(arg1):
                return f"result_{arg1}"
            
            result = test_function("test")
            
            assert result == "result_test"
            # 验证使用了自定义键函数
            mock_manager.get.assert_called()
            mock_manager.set.assert_called()
    
    def test_cached_decorator_with_kwargs(self, mock_redis):
        """测试：@cached装饰器（带kwargs，覆盖309-310行）"""
        with patch('app.utils.cache.cache_manager') as mock_manager:
            mock_manager.client = mock_redis
            mock_manager.get.return_value = None
            mock_manager.set.return_value = True
            
            @cached("test_prefix", ttl=300)
            def test_function(arg1, kwarg1=None):
                return f"result_{arg1}_{kwarg1}"
            
            result = test_function("test", kwarg1="value")
            
            assert result == "result_test_value"
            # 验证kwargs被包含在缓存键中
            mock_manager.get.assert_called()
            mock_manager.set.assert_called()

