"""
音频处理器

提供音频格式转换、压缩、缓存等功能
"""

# 标准库
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional

# 本地库
from app.utils.logger import logger


class AudioProcessor:
    """音频处理器
    
    提供音频格式转换、压缩、缓存等功能
    """
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_cache_size: int = 100 * 1024 * 1024  # 100MB
    ):
        """初始化音频处理器
        
        Args:
            cache_dir: 缓存目录（可选）
            max_cache_size: 最大缓存大小（字节）
        """
        if cache_dir is None:
            cache_dir = Path("./data/audio_cache")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_size = max_cache_size
        
        logger.info(
            f"Audio processor initialized",
            extra={"cache_dir": str(self.cache_dir), "max_cache_size": max_cache_size}
        )
    
    def get_cache_key(self, text: str, voice: str, speed: float) -> str:
        """生成缓存key
        
        Args:
            text: 文本内容
            voice: 语音名称
            speed: 语速
            
        Returns:
            str: 缓存key（MD5哈希）
        """
        key_string = f"{text}:{voice}:{speed}"
        return hashlib.md5(key_string.encode("utf-8")).hexdigest()
    
    def get_cache_path(self, cache_key: str, format: str = "mp3") -> Path:
        """获取缓存文件路径
        
        Args:
            cache_key: 缓存key
            format: 音频格式
            
        Returns:
            Path: 缓存文件路径
        """
        return self.cache_dir / f"{cache_key}.{format}"
    
    def is_cached(self, cache_key: str, format: str = "mp3") -> bool:
        """检查是否已缓存
        
        Args:
            cache_key: 缓存key
            format: 音频格式
            
        Returns:
            bool: 是否已缓存
        """
        cache_path = self.get_cache_path(cache_key, format)
        return cache_path.exists()
    
    async def save_to_cache(
        self,
        cache_key: str,
        audio_data: bytes,
        format: str = "mp3"
    ) -> Path:
        """保存音频到缓存
        
        Args:
            cache_key: 缓存key
            audio_data: 音频数据
            format: 音频格式
            
        Returns:
            Path: 缓存文件路径
        """
        cache_path = self.get_cache_path(cache_key, format)
        
        try:
            cache_path.write_bytes(audio_data)
            
            logger.debug(
                f"Audio cached",
                extra={"cache_key": cache_key, "size": len(audio_data), "path": str(cache_path)}
            )
            
            return cache_path
            
        except Exception as e:
            logger.error(f"Failed to save audio to cache: {e}", exc_info=True)
            raise
    
    async def load_from_cache(
        self,
        cache_key: str,
        format: str = "mp3"
    ) -> Optional[bytes]:
        """从缓存加载音频
        
        Args:
            cache_key: 缓存key
            format: 音频格式
            
        Returns:
            Optional[bytes]: 音频数据，如果不存在返回None
        """
        cache_path = self.get_cache_path(cache_key, format)
        
        if not cache_path.exists():
            return None
        
        try:
            audio_data = cache_path.read_bytes()
            
            logger.debug(
                f"Audio loaded from cache",
                extra={"cache_key": cache_key, "size": len(audio_data)}
            )
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Failed to load audio from cache: {e}", exc_info=True)
            return None
    
    def clear_cache(self):
        """清除所有缓存"""
        try:
            for cache_file in self.cache_dir.glob("*"):
                if cache_file.is_file():
                    cache_file.unlink()
            
            logger.info(f"Audio cache cleared")
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}", exc_info=True)
    
    def get_cache_size(self) -> int:
        """获取当前缓存大小
        
        Returns:
            int: 缓存大小（字节）
        """
        total_size = 0
        for cache_file in self.cache_dir.glob("*"):
            if cache_file.is_file():
                total_size += cache_file.stat().st_size
        return total_size
    
    def cleanup_cache(self):
        """清理缓存（如果超过最大大小）"""
        current_size = self.get_cache_size()
        
        if current_size > self.max_cache_size:
            logger.warning(
                f"Cache size ({current_size}) exceeds max ({self.max_cache_size}), clearing cache"
            )
            self.clear_cache()

