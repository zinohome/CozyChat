"""
配置适配器

提供统一的配置访问接口，支持从YAML和Settings双重读取
实现配置优先级：YAML > 环境变量 > 代码默认值
"""

# 标准库
from typing import Any, Dict, Optional

# 本地库
from app.config.config import settings
from app.utils.config_loader import ConfigLoader, get_config_loader
from app.utils.logger import logger


class ConfigAdapter:
    """配置适配器，统一配置访问接口
    
    支持从YAML和Settings双重读取，实现配置优先级：
    - YAML配置（最高优先级）
    - 环境变量（通过Settings）
    - 代码默认值（最低优先级）
    """
    
    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        """初始化配置适配器
        
        Args:
            config_loader: 配置加载器实例（可选）
        """
        self.settings = settings
        self.config_loader = config_loader or get_config_loader()
        self._cache: Dict[str, Any] = {}
        
        logger.debug("Config adapter initialized")
    
    def get_memory_config(self) -> Dict[str, Any]:
        """获取记忆配置（优先YAML，回退到Settings）
        
        Returns:
            Dict[str, Any]: 记忆配置字典
        """
        cache_key = "memory"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 1. 尝试从YAML加载
        yaml_config = {}
        try:
            yaml_config = self.config_loader.load_memory_config()
        except Exception as e:
            logger.warning(
                f"Failed to load memory config from YAML: {e}",
                exc_info=True
            )
        
        # 2. 从Settings读取（作为后备）
        settings_config = {
            "storage_mode": self.settings.memory_storage_mode,
            "async_write": self.settings.memory_async_write,
            "batch_size": self.settings.memory_batch_size,
            "dedup": {
                "enabled": self.settings.memory_dedup_enabled,
                "mode": self.settings.memory_dedup_mode,
                "content_threshold": self.settings.memory_dedup_content_threshold,
                "storage_threshold": self.settings.memory_dedup_storage_threshold,
                "check_interval_seconds": self.settings.memory_dedup_check_interval,
            }
        }
        
        # 3. 合并：YAML优先（使用deep_merge，YAML覆盖Settings）
        merged_config = ConfigLoader.deep_merge(settings_config, yaml_config)
        
        # 缓存结果
        self._cache[cache_key] = merged_config
        
        return merged_config
    
    def get_session_config(self) -> Dict[str, Any]:
        """获取会话配置（优先YAML，回退到Settings）
        
        Returns:
            Dict[str, Any]: 会话配置字典
        """
        cache_key = "session"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 1. 尝试从YAML加载
        yaml_config = {}
        try:
            yaml_config = self.config_loader.load_session_config()
        except Exception as e:
            logger.warning(
                f"Failed to load session config from YAML: {e}",
                exc_info=True
            )
        
        # 2. 从Settings读取（作为后备）
        settings_config = {
            "title": {
                "trigger_length": self.settings.session_title_trigger_length,
                "max_messages": self.settings.session_title_max_messages,
                "model": self.settings.session_title_model,
                "temperature": self.settings.session_title_temperature,
                "max_tokens": self.settings.session_title_max_tokens,
            }
        }
        
        # 3. 合并：YAML优先
        merged_config = ConfigLoader.deep_merge(settings_config, yaml_config)
        
        # 缓存结果
        self._cache[cache_key] = merged_config
        
        return merged_config
    
    def get_context_config(self) -> Dict[str, Any]:
        """获取上下文配置（优先YAML，回退到Settings）
        
        Returns:
            Dict[str, Any]: 上下文配置字典
        """
        cache_key = "context"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 1. 尝试从YAML加载
        yaml_config = {}
        try:
            yaml_config = self.config_loader.load_context_config()
        except Exception as e:
            logger.warning(
                f"Failed to load context config from YAML: {e}",
                exc_info=True
            )
        
        # 2. 从Settings读取（作为后备）
        settings_config = {
            "intelligent_enabled": self.settings.context_intelligent_enabled,
            "recent": {
                "message_count": self.settings.context_recent_message_count,
            },
            "max_tokens": self.settings.context_max_tokens,
            "weights": {
                "summary": self.settings.context_summary_weight,
                "memory": self.settings.context_memory_weight,
            },
            "summary": {
                "trigger_count": self.settings.context_summary_trigger_count,
                "window_size": self.settings.context_summary_window_size,
                "model": self.settings.context_summary_model,
                "temperature": self.settings.context_summary_temperature,
            }
        }
        
        # 3. 合并：YAML优先
        merged_config = ConfigLoader.deep_merge(settings_config, yaml_config)
        
        # 缓存结果
        self._cache[cache_key] = merged_config
        
        return merged_config
    
    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能配置（优先YAML，回退到Settings）
        
        Returns:
            Dict[str, Any]: 性能配置字典
        """
        cache_key = "performance"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 1. 尝试从YAML加载
        yaml_config = {}
        try:
            yaml_config = self.config_loader.load_performance_config()
        except Exception as e:
            logger.warning(
                f"Failed to load performance config from YAML: {e}",
                exc_info=True
            )
        
        # 2. 从Settings读取（作为后备）
        settings_config = {
            "slow_request": {
                "threshold": self.settings.performance_slow_request_threshold,
                "delete_threshold": self.settings.performance_slow_delete_threshold,
            }
        }
        
        # 3. 合并：YAML优先
        merged_config = ConfigLoader.deep_merge(settings_config, yaml_config)
        
        # 缓存结果
        self._cache[cache_key] = merged_config
        
        return merged_config
    
    def clear_cache(self):
        """清除配置缓存"""
        self._cache.clear()
        logger.debug("Config adapter cache cleared")
    
    def get_memory_config_with_validation(self) -> Dict[str, Any]:
        """获取记忆配置（带验证）
        
        对比YAML配置和Settings配置，确保一致性
        
        Returns:
            Dict[str, Any]: 记忆配置字典
        """
        # 获取YAML配置
        yaml_config = {}
        try:
            yaml_config = self.config_loader.load_memory_config()
        except Exception as e:
            logger.warning(f"Failed to load memory config from YAML: {e}", exc_info=True)
        
        # 获取Settings配置
        settings_config = {
            "storage_mode": self.settings.memory_storage_mode,
            "async_write": self.settings.memory_async_write,
            "batch_size": self.settings.memory_batch_size,
            "dedup": {
                "enabled": self.settings.memory_dedup_enabled,
                "mode": self.settings.memory_dedup_mode,
                "content_threshold": self.settings.memory_dedup_content_threshold,
                "storage_threshold": self.settings.memory_dedup_storage_threshold,
                "check_interval_seconds": self.settings.memory_dedup_check_interval,
            }
        }
        
        # 对比验证（仅在开发环境或调试模式下）
        if self.settings.app_debug and yaml_config:
            self._validate_config_consistency(
                yaml_config, 
                settings_config, 
                "memory"
            )
        
        # 返回YAML配置（如果存在），否则返回Settings配置
        if yaml_config:
            return yaml_config
        return settings_config
    
    def _validate_config_consistency(
        self, 
        yaml_config: Dict[str, Any], 
        settings_config: Dict[str, Any],
        config_name: str
    ):
        """验证配置一致性
        
        Args:
            yaml_config: YAML配置字典
            settings_config: Settings配置字典
            config_name: 配置名称（用于日志）
        """
        def _compare_dicts(yaml_dict: Dict, settings_dict: Dict, path: str = ""):
            """递归对比字典"""
            for key, settings_value in settings_dict.items():
                current_path = f"{path}.{key}" if path else key
                
                if key not in yaml_dict:
                    logger.debug(
                        f"Config key {current_path} not in YAML, using Settings default",
                        extra={"config_name": config_name, "key": current_path}
                    )
                    continue
                
                yaml_value = yaml_dict[key]
                
                if isinstance(settings_value, dict) and isinstance(yaml_value, dict):
                    _compare_dicts(yaml_value, settings_value, current_path)
                elif yaml_value != settings_value:
                    logger.info(
                        f"Config value differs: {current_path}",
                        extra={
                            "config_name": config_name,
                            "key": current_path,
                            "yaml_value": yaml_value,
                            "settings_value": settings_value
                        }
                    )
        
        _compare_dicts(yaml_config, settings_config)


# 全局配置适配器实例
_config_adapter: Optional[ConfigAdapter] = None


def get_config_adapter(config_loader: Optional[ConfigLoader] = None) -> ConfigAdapter:
    """获取配置适配器实例（单例模式）
    
    Args:
        config_loader: 配置加载器实例（可选）
        
    Returns:
        ConfigAdapter: 配置适配器实例
    """
    global _config_adapter
    if _config_adapter is None:
        _config_adapter = ConfigAdapter(config_loader)
    return _config_adapter

