"""
LLM引擎池

缓存LLM引擎实例，避免重复创建。
"""

# 标准库
from typing import Any, Dict, Optional, Tuple
import threading

# 本地库
from app.engines.ai.factory import AIEngineFactory
from app.engines.ai.base import AIEngineBase
from app.utils.logger import logger


class LLMEnginePool:
    """LLM引擎池
    
    按(provider, model)作为key缓存引擎实例，
    避免每次请求重新创建引擎。
    """
    
    _instance: Optional['LLMEnginePool'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        """初始化引擎池"""
        # 引擎缓存：key为(provider, model)，value为引擎实例
        self._engines: Dict[Tuple[str, str], AIEngineBase] = {}
        self._pool_lock = threading.Lock()
        
        logger.info("LLMEnginePool initialized")
    
    @classmethod
    def get_instance(cls) -> 'LLMEnginePool':
        """获取单例实例
        
        Returns:
            LLMEnginePool: 单例实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def get_engine(
        self,
        provider: str,
        model: str,
        **kwargs
    ) -> AIEngineBase:
        """获取或创建引擎实例
        
        Args:
            provider: 引擎提供商（openai/ollama/lmstudio）
            model: 模型名称
            **kwargs: 引擎配置参数
            
        Returns:
            AIEngineBase: 引擎实例
        """
        cache_key = (provider, model)
        
        with self._pool_lock:
            # 检查缓存
            if cache_key in self._engines:
                logger.debug(
                    f"Using cached engine: {provider}/{model}",
                    extra={"provider": provider, "model": model}
                )
                return self._engines[cache_key]
            
            # 创建新引擎
            try:
                engine = AIEngineFactory.create_engine(
                    engine_type=provider,
                    model=model,
                    **kwargs
                )
                
                # 缓存引擎
                self._engines[cache_key] = engine
                
                logger.info(
                    f"Created new engine: {provider}/{model}",
                    extra={
                        "provider": provider,
                        "model": model,
                        "total_engines": len(self._engines)
                    }
                )
                
                return engine
            except Exception as e:
                logger.error(
                    f"Failed to create engine: {provider}/{model}: {e}",
                    exc_info=True,
                    extra={"provider": provider, "model": model}
                )
                raise
    
    def remove_engine(self, provider: str, model: str) -> bool:
        """从池中移除引擎
        
        Args:
            provider: 引擎提供商
            model: 模型名称
            
        Returns:
            bool: 是否成功移除
        """
        cache_key = (provider, model)
        
        with self._pool_lock:
            if cache_key in self._engines:
                del self._engines[cache_key]
                logger.info(
                    f"Removed engine from pool: {provider}/{model}",
                    extra={"provider": provider, "model": model}
                )
                return True
            return False
    
    def clear_pool(self) -> None:
        """清空引擎池"""
        with self._pool_lock:
            self._engines.clear()
            logger.info("LLMEnginePool cleared")
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """获取池统计信息
        
        Returns:
            Dict[str, Any]: 池统计信息
        """
        with self._pool_lock:
            return {
                "total_engines": len(self._engines),
                "engines": [
                    {"provider": provider, "model": model}
                    for provider, model in self._engines.keys()
                ],
            }


# 创建全局实例
_pool: Optional[LLMEnginePool] = None


def get_llm_engine_pool() -> LLMEnginePool:
    """获取全局LLM引擎池
    
    Returns:
        LLMEnginePool: 引擎池单例
    """
    global _pool
    if _pool is None:
        _pool = LLMEnginePool.get_instance()
    return _pool


def init_llm_engine_pool() -> LLMEnginePool:
    """初始化全局LLM引擎池
    
    应在应用启动时调用一次。
    
    Returns:
        LLMEnginePool: 引擎池实例
    """
    global _pool
    _pool = LLMEnginePool.get_instance()
    return _pool

