"""提示词配置加载器"""

# 标准库
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# 本地库
from app.utils.logger import logger


class PromptLoader:
    """提示词配置加载器
    
    负责从YAML文件加载提示词配置,支持缓存和热更新
    """
    
    def __init__(self, config_dir: str = "backend/config/prompts"):
        """初始化PromptLoader
        
        Args:
            config_dir: 配置文件目录路径
        """
        self.config_dir = Path(config_dir)
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def load_base_instructions(self) -> Dict[str, Any]:
        """加载基础指令"""
        cache_key = "base_instructions"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        config_path = self.config_dir / "base_instructions.yaml"
        data = self._load_yaml(config_path)
        self._cache[cache_key] = data
        return data
    
    def load_response_style(self, style: str) -> Optional[Dict[str, Any]]:
        """加载响应风格配置
        
        Args:
            style: 风格名称 (brief, standard, detailed)
            
        Returns:
            配置字典或None
        """
        cache_key = f"response_style_{style}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        config_path = self.config_dir / "response_styles" / f"{style}.yaml"
        if not config_path.exists():
            logger.warning(f"Response style config not found: {style}")
            return None
        
        data = self._load_yaml(config_path)
        self._cache[cache_key] = data
        return data
    
    def load_style_preset(self, preset: str) -> Optional[Dict[str, Any]]:
        """加载风格预设配置
        
        Args:
            preset: 预设名称 (elder_friendly, medical_detail)
            
        Returns:
            配置字典或None
        """
        cache_key = f"style_preset_{preset}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        config_path = self.config_dir / "style_presets" / f"{preset}.yaml"
        if not config_path.exists():
            logger.warning(f"Style preset config not found: {preset}")
            return None
        
        data = self._load_yaml(config_path)
        self._cache[cache_key] = data
        return data
    
    def load_language(self, language: str) -> Optional[Dict[str, Any]]:
        """加载语言配置
        
        Args:
            language: 语言代码 (zh_CN, en_US)
            
        Returns:
            配置字典或None
        """
        cache_key = f"language_{language}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        config_path = self.config_dir / "languages" / f"{language}.yaml"
        if not config_path.exists():
            logger.warning(f"Language config not found: {language}")
            return None
        
        data = self._load_yaml(config_path)
        self._cache[cache_key] = data
        return data
    
    def clear_cache(self):
        """清除缓存(用于热更新)"""
        self._cache.clear()
        logger.info("Prompt loader cache cleared")
    
    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """加载YAML文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                logger.debug(f"Loaded prompt config: {path}")
                return data or {}
        except Exception as e:
            logger.error(f"Failed to load prompt config {path}: {e}")
            return {}

