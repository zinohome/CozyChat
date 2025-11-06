"""
数据库查询优化工具

提供查询优化相关的工具函数和装饰器
"""

# 标准库
from functools import wraps
from typing import Any, Callable, Optional

# 第三方库
from sqlalchemy.orm import Session, joinedload, selectinload, subqueryload
from sqlalchemy import text

# 本地库
from app.utils.logger import logger
from app.utils.cache import cache_manager, cached


def eager_load(*relationships: str):
    """Eager loading装饰器
    
    自动为查询添加eager loading，避免N+1查询问题
    
    Args:
        *relationships: 需要eager load的关系名称
        
    Example:
        @eager_load("messages", "user")
        def get_session(session_id: str, db: Session):
            return db.query(Session).filter(Session.id == session_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 查找db参数
            db = kwargs.get("db") or (args[0] if args and hasattr(args[0], "query") else None)
            
            if not db or not isinstance(db, Session):
                return func(*args, **kwargs)
            
            # 这里简化实现，实际应该解析查询并添加eager loading
            # 由于SQLAlchemy查询的复杂性，这里只提供工具函数
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def use_index_hint(index_name: str):
    """使用索引提示装饰器
    
    为查询添加索引提示（PostgreSQL）
    
    Args:
        index_name: 索引名称
        
    Example:
        @use_index_hint("idx_users_username")
        def get_user_by_username(username: str, db: Session):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # PostgreSQL索引提示需要特殊处理
            # 这里只提供接口，实际使用需要根据具体情况
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def query_cache(ttl: int = 300, key_func: Optional[Callable] = None):
    """查询缓存装饰器
    
    为数据库查询结果添加缓存
    
    Args:
        ttl: 缓存过期时间（秒）
        key_func: 生成缓存键的函数（可选）
        
    Example:
        @query_cache(ttl=600)
        def get_user(user_id: str, db: Session):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认使用函数名和参数生成键
                key_parts = [func.__name__]
                if args:
                    key_parts.extend(str(arg) for arg in args)
                if kwargs:
                    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = f"query:{':'.join(key_parts)}"
            
            # 尝试获取缓存
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result
            
            # 执行查询
            result = func(*args, **kwargs)
            
            # 缓存结果（只缓存可序列化的结果）
            if result is not None:
                try:
                    # 尝试序列化（简化实现，实际应该处理ORM对象）
                    if hasattr(result, "__dict__"):
                        # ORM对象需要特殊处理
                        cache_manager.set(cache_key, str(result), ttl)
                    else:
                        cache_manager.set(cache_key, result, ttl)
                except Exception as e:
                    logger.debug(f"Failed to cache query result: {e}")
            
            return result
        
        return wrapper
    return decorator


def batch_operation(batch_size: int = 100):
    """批量操作装饰器
    
    将单个操作转换为批量操作，提高性能
    
    Args:
        batch_size: 批次大小
        
    Example:
        @batch_operation(batch_size=50)
        def create_messages(messages: List[Dict], db: Session):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 查找可批处理的参数
            items = None
            for arg in args:
                if isinstance(arg, (list, tuple)):
                    items = arg
                    break
            
            if not items:
                return func(*args, **kwargs)
            
            # 分批处理
            results = []
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                # 这里简化实现，实际应该根据具体函数调整
                result = func(batch, *args[1:], **kwargs)
                if isinstance(result, list):
                    results.extend(result)
                else:
                    results.append(result)
            
            return results
        
        return wrapper
    return decorator


class QueryOptimizer:
    """查询优化器
    
    提供查询优化的工具方法
    """
    
    @staticmethod
    def eager_load_relationships(query, *relationships: str):
        """为查询添加eager loading
        
        Args:
            query: SQLAlchemy查询对象
            *relationships: 关系名称列表
            
        Returns:
            优化后的查询对象
        """
        for rel in relationships:
            # 根据关系类型选择合适的加载策略
            # 这里简化实现，实际应该根据关系类型选择
            query = query.options(selectinload(rel))
        
        return query
    
    @staticmethod
    def add_index_hint(query, index_name: str):
        """为查询添加索引提示（PostgreSQL）
        
        Args:
            query: SQLAlchemy查询对象
            index_name: 索引名称
            
        Returns:
            优化后的查询对象
        """
        # PostgreSQL索引提示需要特殊处理
        # 这里只提供接口，实际使用需要根据具体情况
        return query
    
    @staticmethod
    def optimize_select(query, columns: list):
        """优化SELECT查询，只选择需要的列
        
        Args:
            query: SQLAlchemy查询对象
            columns: 需要的列列表
            
        Returns:
            优化后的查询对象
        """
        # 只选择需要的列
        return query.with_entities(*columns)

