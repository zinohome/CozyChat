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


class TestQueryOptimizer:
    """测试QueryOptimizer类"""
    
    def test_eager_load_relationships(self):
        """测试：eager_load_relationships方法"""
        from app.utils.query_optimizer import QueryOptimizer
        
        # Mock查询对象和selectinload
        mock_query = MagicMock()
        mock_query.options = MagicMock(return_value=mock_query)
        
        # Mock selectinload以避免SQLAlchemy错误
        with patch('app.utils.query_optimizer.selectinload') as mock_selectinload:
            mock_selectinload.return_value = MagicMock()
            
            result = QueryOptimizer.eager_load_relationships(mock_query, "messages", "user")
            
            assert result == mock_query
            # 应该调用options两次（每个关系一次）
            assert mock_query.options.call_count == 2
            # 验证使用了selectinload
            assert mock_selectinload.call_count == 2
    
    def test_add_index_hint(self):
        """测试：add_index_hint方法"""
        from app.utils.query_optimizer import QueryOptimizer
        
        # Mock查询对象
        mock_query = MagicMock()
        
        result = QueryOptimizer.add_index_hint(mock_query, "idx_users_username")
        
        # 简化实现直接返回查询对象
        assert result == mock_query
    
    def test_optimize_select(self):
        """测试：optimize_select方法"""
        from app.utils.query_optimizer import QueryOptimizer
        
        # Mock查询对象
        mock_query = MagicMock()
        mock_query.with_entities = MagicMock(return_value=mock_query)
        
        result = QueryOptimizer.optimize_select(mock_query, ["id", "username"])
        
        assert result == mock_query
        mock_query.with_entities.assert_called_once_with("id", "username")


class TestBatchOperationDecorator:
    """测试@batch_operation装饰器"""
    
    def test_batch_operation_decorator(self):
        """测试：@batch_operation装饰器"""
        from app.utils.query_optimizer import batch_operation
        
        @batch_operation(batch_size=2)
        def test_function(items):
            return [item * 2 for item in items]
        
        result = test_function([1, 2, 3, 4, 5])
        
        # 应该分批处理
        assert result == [2, 4, 6, 8, 10]
    
    def test_batch_operation_single_batch(self):
        """测试：@batch_operation装饰器（单批）"""
        from app.utils.query_optimizer import batch_operation
        
        @batch_operation(batch_size=10)
        def test_function(items):
            return [item * 2 for item in items]
        
        result = test_function([1, 2, 3])
        
        assert result == [2, 4, 6]
    
    def test_batch_operation_no_items(self):
        """测试：@batch_operation装饰器（无items）"""
        from app.utils.query_optimizer import batch_operation
        
        @batch_operation(batch_size=2)
        def test_function(arg1, arg2):
            return f"{arg1}_{arg2}"
        
        result = test_function("a", "b")
        
        # 没有items参数时，应该正常执行
        assert result == "a_b"
    
    def test_batch_operation_non_list_result(self):
        """测试：@batch_operation装饰器（非列表结果）"""
        from app.utils.query_optimizer import batch_operation
        
        @batch_operation(batch_size=2)
        def test_function(items):
            return len(items)  # 返回非列表结果
        
        result = test_function([1, 2, 3, 4])
        
        # 非列表结果应该被包装在列表中
        assert isinstance(result, list)
        assert len(result) == 2  # 两个批次

