"""
人格管理器

提供人格的加载、管理、切换等功能
"""

# 标准库
from pathlib import Path
from typing import Any, Dict, List, Optional

# 本地库
from app.utils.logger import logger
from .loader import PersonalityLoader
from .models import Personality


class PersonalityManager:
    """人格管理器
    
    负责加载、管理、切换人格配置
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """初始化人格管理器
        
        Args:
            config_dir: 配置目录路径（可选）
        """
        self.loader = PersonalityLoader(config_dir)
        self.personalities: Dict[str, Personality] = {}
        self._load_all_personalities()
        
        logger.info(
            "Personality manager initialized",
            extra={"personalities_count": len(self.personalities)}
        )
    
    def _load_all_personalities(self):
        """从配置目录加载所有人格"""
        try:
            personality_files = self.loader.config_dir.glob("*.yaml")
            for file_path in personality_files:
                try:
                    personality = self.loader.load_from_file(file_path)
                    self.personalities[personality.id] = personality
                    logger.info(
                        f"Loaded personality: {personality.name}",
                        extra={"personality_id": personality.id}
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to load personality from {file_path}: {e}",
                        exc_info=True
                    )
        except Exception as e:
            logger.warning(
                f"Failed to load personalities from directory: {e}",
                exc_info=True
            )
    
    def get_personality(self, personality_id: str) -> Optional[Personality]:
        """获取指定人格
        
        Args:
            personality_id: 人格ID
            
        Returns:
            Optional[Personality]: Personality对象，如果不存在返回None
        """
        return self.personalities.get(personality_id)
    
    def list_personalities(self) -> List[Dict[str, Any]]:
        """列出所有可用人格
        
        Returns:
            List[Dict[str, Any]]: 人格信息列表
        """
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "version": p.version,
                "icon": p.metadata.get("icon", ""),
                "tags": p.metadata.get("tags", [])
            }
            for p in self.personalities.values()
        ]
    
    def create_personality(self, config: Dict[str, Any]) -> Personality:
        """动态创建人格（用户自定义人格）
        
        Args:
            config: 人格配置字典
            
        Returns:
            Personality: Personality对象
            
        Raises:
            ValueError: 如果配置无效或人格ID已存在
        """
        personality = self.loader.load_from_dict(config)
        
        if personality.id in self.personalities:
            raise ValueError(f"Personality {personality.id} already exists")
        
        self.personalities[personality.id] = personality
        
        # 保存到配置文件
        self.loader.save_to_file(personality)
        
        logger.info(
            f"Created personality: {personality.name}",
            extra={"personality_id": personality.id}
        )
        
        return personality
    
    def update_personality(
        self,
        personality_id: str,
        updates: Dict[str, Any]
    ) -> Personality:
        """更新人格配置
        
        Args:
            personality_id: 人格ID
            updates: 更新字典
            
        Returns:
            Personality: 更新后的Personality对象
            
        Raises:
            ValueError: 如果人格不存在
        """
        personality = self.get_personality(personality_id)
        if not personality:
            raise ValueError(f"Personality {personality_id} not found")
        
        personality.update(updates)
        
        # 保存到配置文件
        self.loader.save_to_file(personality)
        
        logger.info(
            f"Updated personality: {personality.name}",
            extra={"personality_id": personality_id}
        )
        
        return personality
    
    def delete_personality(self, personality_id: str):
        """删除人格
        
        Args:
            personality_id: 人格ID
        """
        if personality_id not in self.personalities:
            logger.warning(f"Personality {personality_id} not found")
            return
        
        del self.personalities[personality_id]
        
        # 删除配置文件
        file_path = self.loader.config_dir / f"{personality_id}.yaml"
        if file_path.exists():
            file_path.unlink()
        
        logger.info(f"Deleted personality: {personality_id}")
    
    def reload_personality(self, personality_id: str) -> Optional[Personality]:
        """重新加载人格配置
        
        Args:
            personality_id: 人格ID
            
        Returns:
            Optional[Personality]: Personality对象，如果不存在返回None
        """
        file_path = self.loader.config_dir / f"{personality_id}.yaml"
        if not file_path.exists():
            logger.warning(f"Personality file not found: {file_path}")
            return None
        
        try:
            personality = self.loader.load_from_file(file_path)
            self.personalities[personality_id] = personality
            
            logger.info(
                f"Reloaded personality: {personality.name}",
                extra={"personality_id": personality_id}
            )
            
            return personality
        except Exception as e:
            logger.error(
                f"Failed to reload personality {personality_id}: {e}",
                exc_info=True
            )
            return None
    
    def reload_all(self):
        """重新加载所有人格配置"""
        self.personalities.clear()
        self._load_all_personalities()
        logger.info("Reloaded all personalities")

