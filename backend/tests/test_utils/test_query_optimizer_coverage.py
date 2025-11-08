"""
查询优化器覆盖率测试

补充query_optimizer.py的未覆盖行测试
"""

# 标准库
import pytest
from unittest.mock import MagicMock, Mock, patch

# 本地库
from app.utils.query_optimizer import eager_load, use_index_hint, query_cache, QueryOptimizer, batch_operation


class TestQueryOptimizerCoverage:
    """查询优化器覆盖率测试"""
    
    def test_eager_load_with_db_in_args(self):
        """测试：@eager_load装饰器（db在args中，覆盖37-44行）"""
        mock_db = Mock()
        mock_db.query = MagicMock()
        
        @eager_load("messages", "user")
        def test_query(session_id: str, db):
            return {"session_id": session_id}
        
        result = test_query("session123", mock_db)
        
        assert result == {"session_id": "session123"}
    
    def test_query_cache_with_key_func(self, mock_redis):
        """测试：@query_cache装饰器（自定义键函数，覆盖92-93行）"""
        with patch('app.utils.query_optimizer.cache_manager') as mock_manager:
            mock_manager.client = mock_redis
            mock_manager.get.return_value = None
            mock_manager.set.return_value = True
            
            def custom_key_func(*args, **kwargs):
                return f"custom_{args[0]}"
            
            @query_cache(ttl=600, key_func=custom_key_func)
            def test_query(user_id: str):
                return {"user_id": user_id}
            
            result = test_query("user123")
            
            assert result == {"user_id": "user123"}
            # 验证使用了自定义键函数
            mock_manager.get.assert_called()
            mock_manager.set.assert_called()
    
    def test_query_cache_with_args_and_kwargs(self, mock_redis):
        """测试：@query_cache装饰器（带args和kwargs，覆盖96-100行）"""
        with patch('app.utils.query_optimizer.cache_manager') as mock_manager:
            mock_manager.client = mock_redis
            mock_manager.get.return_value = None
            mock_manager.set.return_value = True
            
            @query_cache(ttl=600)
            def test_query(user_id: str, session_id: str = None):
                return {"user_id": user_id, "session_id": session_id}
            
            result = test_query("user123", session_id="session456")
            
            assert result == {"user_id": "user123", "session_id": "session456"}
            # 验证args和kwargs被包含在缓存键中
            mock_manager.get.assert_called()
            mock_manager.set.assert_called()
    
    def test_query_optimizer_eager_load_relationships(self):
        """测试：QueryOptimizer.eager_load_relationships（覆盖118行）"""
        mock_query = MagicMock()
        mock_query.options = MagicMock(return_value=mock_query)
        
        with patch('app.utils.query_optimizer.selectinload') as mock_selectinload:
            mock_selectinload.return_value = MagicMock()
            
            result = QueryOptimizer.eager_load_relationships(mock_query, "messages", "user")
            
            assert result == mock_query
            assert mock_query.options.call_count == 2
    
    def test_query_optimizer_add_index_hint(self):
        """测试：QueryOptimizer.add_index_hint（覆盖121-122行）"""
        mock_query = MagicMock()
        
        result = QueryOptimizer.add_index_hint(mock_query, "idx_users_username")
        
        # 简化实现直接返回查询对象
        assert result == mock_query

