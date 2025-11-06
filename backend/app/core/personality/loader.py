"""
人格配置加载器

从YAML文件加载和验证人格配置
"""

# 标准库
from pathlib import Path
from typing import Any, Dict, Optional

# 第三方库
import yaml

# 本地库
from app.utils.logger import logger
from .models import Personality


class PersonalityLoader:
    """人格配置加载器
    
    负责从YAML文件加载和验证人格配置
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """初始化加载器
        
        Args:
            config_dir: 配置目录路径（可选）
        """
        if config_dir is None:
            # 默认配置目录
            config_dir = Path(__file__).parent.parent.parent.parent / "config" / "personalities"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            f"Personality loader initialized",
            extra={"config_dir": str(self.config_dir)}
        )
    
    def load_from_file(self, file_path: Path) -> Personality:
        """从YAML文件加载人格配置
        
        Args:
            file_path: YAML文件路径
            
        Returns:
            Personality: Personality对象
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 配置格式错误
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Personality config file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config or "personality" not in config:
                raise ValueError(f"Invalid personality config format: {file_path}")
            
            personality = Personality.from_config(config["personality"])
            
            # 验证配置
            self._validate_personality(personality)
            
            logger.info(
                f"Loaded personality from file: {personality.name}",
                extra={"personality_id": personality.id, "file_path": str(file_path)}
            )
            
            return personality
            
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML file {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load personality from {file_path}: {e}")
    
    def load_from_dict(self, config: Dict[str, Any]) -> Personality:
        """从配置字典加载人格配置
        
        Args:
            config: 配置字典
            
        Returns:
            Personality: Personality对象
            
        Raises:
            ValueError: 配置格式错误
        """
        try:
            if "personality" in config:
                config = config["personality"]
            
            personality = Personality.from_config(config)
            
            # 验证配置
            self._validate_personality(personality)
            
            logger.info(
                f"Loaded personality from dict: {personality.name}",
                extra={"personality_id": personality.id}
            )
            
            return personality
            
        except Exception as e:
            raise ValueError(f"Failed to load personality from dict: {e}")
    
    def save_to_file(self, personality: Personality, file_path: Optional[Path] = None):
        """保存人格配置到YAML文件
        
        Args:
            personality: Personality对象
            file_path: 文件路径（可选，如果不提供则使用默认路径）
        """
        if file_path is None:
            file_path = self.config_dir / f"{personality.id}.yaml"
        
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            config = {"personality": personality.to_config()}
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    config,
                    f,
                    allow_unicode=True,
                    sort_keys=False,
                    default_flow_style=False
                )
            
            logger.info(
                f"Saved personality to file: {personality.name}",
                extra={"personality_id": personality.id, "file_path": str(file_path)}
            )
            
        except Exception as e:
            logger.error(f"Failed to save personality to {file_path}: {e}", exc_info=True)
            raise
    
    def _validate_personality(self, personality: Personality):
        """验证人格配置
        
        Args:
            personality: Personality对象
            
        Raises:
            ValueError: 配置验证失败
        """
        if not personality.id:
            raise ValueError("Personality id is required")
        
        if not personality.name:
            raise ValueError("Personality name is required")
        
        # 验证traits范围
        traits = personality.traits
        for attr_name in ["friendliness", "formality", "humor", "empathy"]:
            value = getattr(traits, attr_name)
            if not 0 <= value <= 1:
                raise ValueError(f"Trait {attr_name} must be between 0 and 1, got {value}")
        
        # 验证AI配置
        if personality.ai.provider not in ["openai", "ollama", "lmstudio"]:
            raise ValueError(f"Unsupported AI provider: {personality.ai.provider}")
        
        if personality.ai.temperature < 0 or personality.ai.temperature > 2:
            raise ValueError(f"Temperature must be between 0 and 2, got {personality.ai.temperature}")
        
        # 验证记忆配置
        if personality.memory.vector_db not in ["chromadb", "qdrant"]:
            raise ValueError(f"Unsupported vector DB: {personality.memory.vector_db}")
        
        if personality.memory.save_mode not in ["both", "user_only", "assistant_only"]:
            raise ValueError(f"Invalid save_mode: {personality.memory.save_mode}")
        
        logger.debug(f"Personality validation passed: {personality.id}")

