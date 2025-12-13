"""
配置加载器

从YAML文件加载引擎、工具、记忆等配置
支持环境变量占位符解析和配置合并
"""

# 标准库
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

# 第三方库
import yaml

# 本地库
from app.config.config import settings
from app.utils.logger import logger


class ConfigLoader:
    """配置加载器
    
    负责从YAML文件加载各种配置
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """初始化配置加载器
        
        Args:
            config_dir: 配置目录路径（可选）
        """
        if config_dir is None:
            # 默认配置目录：backend/config
            config_dir = Path(__file__).parent.parent.parent / "config"
        
        self.config_dir = Path(config_dir)
        self._cache: Dict[str, Any] = {}
        
        logger.info(
            "Config loader initialized",
            extra={"config_dir": str(self.config_dir)}
        )
    
    def load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """加载YAML文件
        
        Args:
            file_path: YAML文件路径
            
        Returns:
            Dict[str, Any]: 配置字典
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: YAML解析失败
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        # 检查缓存
        cache_key = str(file_path)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if config is None:
                config = {}
            
            # 缓存配置
            self._cache[cache_key] = config
            
            logger.debug(
                f"Loaded config from: {file_path}",
                extra={"file_path": str(file_path)}
            )
            
            return config
            
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML file {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load config from {file_path}: {e}")
    
    def load_engine_config(self, engine_name: str) -> Dict[str, Any]:
        """加载AI引擎配置
        
        Args:
            engine_name: 引擎名称（openai, ollama, lmstudio）
            
        Returns:
            Dict[str, Any]: 引擎配置字典
        """
        file_path = self.config_dir / "models" / f"{engine_name}.yaml"
        config = self.load_yaml(file_path)
        # 返回 engine 配置，如果没有则返回整个配置
        return config.get("engine", config)
    
    def load_tool_config(self) -> Dict[str, Any]:
        """加载工具配置
        
        Returns:
            Dict[str, Any]: 工具配置字典
        """
        builtin_path = self.config_dir / "tools" / "builtin.yaml"
        mcp_path = self.config_dir / "tools" / "mcp.yaml"
        
        config = {}
        
        if builtin_path.exists():
            builtin_config = self.load_yaml(builtin_path)
            config["builtin"] = builtin_config.get("tools", {}).get("builtin", [])
        
        if mcp_path.exists():
            mcp_config = self.load_yaml(mcp_path)
            config["mcp"] = mcp_config.get("tools", {}).get("mcp", {})
        
        return config
    
    def load_memory_config(self) -> Dict[str, Any]:
        """加载记忆配置
        
        Returns:
            Dict[str, Any]: 记忆配置字典
        """
        file_path = self.config_dir / "memory.yaml"
        config = self.load_yaml(file_path)
        memory_config = config.get("memory", {})
        # 解析环境变量占位符
        return self.resolve_env_placeholders(memory_config)
    
    def load_voice_config(self, voice_type: str) -> Dict[str, Any]:
        """加载语音配置
        
        Args:
            voice_type: 语音类型（stt, tts, realtime）
            
        Returns:
            Dict[str, Any]: 语音配置字典
        """
        file_path = self.config_dir / "voice" / f"{voice_type}.yaml"
        config = self.load_yaml(file_path)
        return config.get("engines", {}).get(voice_type, {})
    
    def load_session_config(self) -> Dict[str, Any]:
        """加载会话配置
        
        Returns:
            Dict[str, Any]: 会话配置字典
        """
        file_path = self.config_dir / "session.yaml"
        config = self.load_yaml(file_path)
        session_config = config.get("session", {})
        # 解析环境变量占位符
        return self.resolve_env_placeholders(session_config)
    
    def load_context_config(self) -> Dict[str, Any]:
        """加载上下文配置
        
        Returns:
            Dict[str, Any]: 上下文配置字典
        """
        file_path = self.config_dir / "context.yaml"
        if not file_path.exists():
            return {}
        config = self.load_yaml(file_path)
        context_config = config.get("context", {})
        # 解析环境变量占位符
        return self.resolve_env_placeholders(context_config)
    
    def load_performance_config(self) -> Dict[str, Any]:
        """加载性能配置
        
        Returns:
            Dict[str, Any]: 性能配置字典
        """
        file_path = self.config_dir / "performance.yaml"
        if not file_path.exists():
            return {}
        config = self.load_yaml(file_path)
        performance_config = config.get("performance", {})
        # 解析环境变量占位符
        return self.resolve_env_placeholders(performance_config)
    
    def resolve_env_placeholders(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """递归解析配置中的环境变量占位符
        
        支持 ${VAR_NAME} 格式，从 settings 或 os.environ 读取
        
        Args:
            config: 配置字典
            
        Returns:
            Dict[str, Any]: 解析后的配置字典
        """
        if not isinstance(config, dict):
            if isinstance(config, str):
                return self._resolve_string_placeholders(config)
            return config
        
        resolved = {}
        for key, value in config.items():
            if isinstance(value, dict):
                resolved[key] = self.resolve_env_placeholders(value)
            elif isinstance(value, list):
                resolved[key] = [
                    self.resolve_env_placeholders(item) if isinstance(item, dict) else
                    self._resolve_string_placeholders(item) if isinstance(item, str) else item
                    for item in value
                ]
            elif isinstance(value, str):
                resolved[key] = self._resolve_string_placeholders(value)
            else:
                resolved[key] = value
        
        return resolved
    
    def _resolve_string_placeholders(self, value: str) -> str:
        """解析字符串中的环境变量占位符
        
        Args:
            value: 可能包含 ${VAR_NAME} 格式的字符串
            
        Returns:
            str: 解析后的字符串
        """
        if not isinstance(value, str):
            return value
        
        # 匹配 ${VAR_NAME} 格式
        pattern = r'\$\{([^}]+)\}'
        
        def replace_var(match):
            var_name = match.group(1)
            # 先从 settings 获取（使用小写和下划线）
            settings_attr = var_name.lower().replace('-', '_')
            env_value = getattr(settings, settings_attr, None)
            
            # 如果 settings 中没有，从环境变量获取
            if env_value is None:
                env_value = os.getenv(var_name)
            
            # 如果都没有，记录警告并返回空字符串
            if env_value is None:
                logger.warning(
                    f"Environment variable {var_name} not found, using empty string",
                    extra={"var_name": var_name}
                )
                return ""
            
            return str(env_value)
        
        return re.sub(pattern, replace_var, value)
    
    @staticmethod
    def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并配置字典
        
        合并规则：
        - override 中的值会覆盖 base 中的值
        - 对于字典类型，递归合并
        - 对于列表类型，直接使用 override 的值
        
        Args:
            base: 基础配置字典
            override: 覆盖配置字典
            
        Returns:
            Dict[str, Any]: 合并后的配置字典
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # 递归合并字典
                result[key] = ConfigLoader.deep_merge(result[key], value)
            else:
                # 直接覆盖
                result[key] = value
        
        return result
    
    def clear_cache(self):
        """清除配置缓存"""
        self._cache.clear()
        logger.debug("Config cache cleared")


# 全局配置加载器实例
_config_loader: Optional[ConfigLoader] = None


def get_config_loader(config_dir: Optional[Path] = None) -> ConfigLoader:
    """获取配置加载器实例（单例模式）
    
    Args:
        config_dir: 配置目录路径（可选）
        
    Returns:
        ConfigLoader: 配置加载器实例
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader(config_dir)
    return _config_loader

