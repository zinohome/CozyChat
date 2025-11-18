"""
人格注册表

启动时加载所有人格配置并缓存，避免每次请求重新加载。
"""

# 标准库
import os
from pathlib import Path
from typing import Dict, List, Optional
import threading

# 本地库
from app.core.personality.models import Personality
from app.core.personality.loader import PersonalityLoader
from app.utils.logger import logger


class PersonalityRegistry:
    """人格注册表
    
    应用级单例，在启动时扫描并加载所有人格配置。
    提供线程安全的人格查询和管理功能。
    """
    
    _instance: Optional['PersonalityRegistry'] = None
    _lock = threading.Lock()
    
    def __init__(self, personalities_dir: Optional[str] = None):
        """初始化注册表
        
        Args:
            personalities_dir: 人格配置文件目录，默认为 config/personalities
        """
        if personalities_dir is None:
            # 默认使用 config/personalities 目录
            base_dir = Path(__file__).parent.parent.parent.parent
            personalities_dir = str(base_dir / "config" / "personalities")
        
        self.personalities_dir = personalities_dir
        self.personalities: Dict[str, Personality] = {}
        self._loader = PersonalityLoader()
        self._load_lock = threading.Lock()
        
        # 初始化时加载所有人格
        self._load_all_personalities()
        
        logger.info(
            f"PersonalityRegistry initialized with {len(self.personalities)} personalities",
            extra={"personalities_dir": personalities_dir, "count": len(self.personalities)}
        )
    
    @classmethod
    def get_instance(cls, personalities_dir: Optional[str] = None) -> 'PersonalityRegistry':
        """获取单例实例
        
        Args:
            personalities_dir: 人格配置文件目录
            
        Returns:
            PersonalityRegistry: 单例实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(personalities_dir)
        return cls._instance
    
    def _load_all_personalities(self) -> None:
        """扫描并加载所有人格配置文件"""
        personalities_path = Path(self.personalities_dir)
        
        if not personalities_path.exists():
            logger.warning(
                f"Personalities directory not found: {self.personalities_dir}",
                extra={"personalities_dir": str(self.personalities_dir)}
            )
            return
        
        yaml_files = list(personalities_path.glob("*.yaml")) + list(personalities_path.glob("*.yml"))
        
        for yaml_file in yaml_files:
            try:
                personality = self._loader.load_from_file(yaml_file)
                self.personalities[personality.id] = personality
                logger.debug(
                    f"Loaded personality: {personality.id}",
                    extra={"personality_id": personality.id, "file": str(yaml_file)}
                )
            except Exception as e:
                logger.error(
                    f"Failed to load personality from {yaml_file}: {e}",
                    exc_info=True,
                    extra={"file": str(yaml_file)}
                )
    
    def get_personality(self, personality_id: str) -> Optional[Personality]:
        """获取人格配置
        
        Args:
            personality_id: 人格ID
            
        Returns:
            Optional[Personality]: 人格对象，不存在返回None
        """
        return self.personalities.get(personality_id)
    
    def list_personalities(self) -> List[Personality]:
        """列出所有人格
        
        Returns:
            List[Personality]: 所有人格对象列表
        """
        return list(self.personalities.values())
    
    def list_personality_ids(self) -> List[str]:
        """列出所有人格ID
        
        Returns:
            List[str]: 所有人格ID列表
        """
        return list(self.personalities.keys())
    
    def reload(self, personality_id: Optional[str] = None) -> None:
        """重新加载人格配置
        
        Args:
            personality_id: 要重新加载的人格ID，为None时重新加载所有人格
        """
        with self._load_lock:
            if personality_id is None:
                # 重新加载所有人格
                logger.info("Reloading all personalities")
                self.personalities.clear()
                self._load_all_personalities()
            else:
                # 重新加载指定人格
                logger.info(f"Reloading personality: {personality_id}")
                personalities_path = Path(self.personalities_dir)
                yaml_files = list(personalities_path.glob(f"{personality_id}.yaml")) + \
                            list(personalities_path.glob(f"{personality_id}.yml"))
                
                if not yaml_files:
                    logger.warning(f"Personality file not found for: {personality_id}")
                    return
                
                try:
                    personality = self._loader.load_from_file(str(yaml_files[0]))
                    self.personalities[personality.id] = personality
                    logger.info(f"Reloaded personality: {personality.id}")
                except Exception as e:
                    logger.error(
                        f"Failed to reload personality {personality_id}: {e}",
                        exc_info=True
                    )
    
    def has_personality(self, personality_id: str) -> bool:
        """检查人格是否存在
        
        Args:
            personality_id: 人格ID
            
        Returns:
            bool: 是否存在
        """
        return personality_id in self.personalities


# 创建全局实例（在应用启动时初始化）
_registry: Optional[PersonalityRegistry] = None


def get_personality_registry() -> PersonalityRegistry:
    """获取全局人格注册表
    
    Returns:
        PersonalityRegistry: 人格注册表单例
    """
    global _registry
    if _registry is None:
        _registry = PersonalityRegistry.get_instance()
    return _registry


def init_personality_registry(personalities_dir: Optional[str] = None) -> PersonalityRegistry:
    """初始化全局人格注册表
    
    应在应用启动时调用一次。
    
    Args:
        personalities_dir: 人格配置文件目录
        
    Returns:
        PersonalityRegistry: 人格注册表实例
    """
    global _registry
    _registry = PersonalityRegistry.get_instance(personalities_dir)
    return _registry

