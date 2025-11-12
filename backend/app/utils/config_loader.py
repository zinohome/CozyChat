"""
配置加载器

从YAML文件加载引擎、工具、记忆等配置
"""

# 标准库
from pathlib import Path
from typing import Any, Dict, Optional

# 第三方库
import yaml

# 本地库
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
        return config.get("memory", {})
    
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

