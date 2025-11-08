"""
音频处理器测试

测试音频处理器的功能（格式转换、压缩、缓存等）
"""

# 标准库
import pytest
import io
from unittest.mock import MagicMock, patch, mock_open
import tempfile
import os

# 本地库
from app.engines.voice.audio.processor import AudioProcessor


class TestAudioProcessor:
    """测试音频处理器"""
    
    @pytest.fixture
    def audio_processor(self):
        """创建音频处理器实例"""
        return AudioProcessor()
    
    @pytest.fixture
    def sample_audio_data(self):
        """示例音频数据"""
        return b"fake audio data for testing"
    
    def test_processor_initialization(self, audio_processor):
        """测试：处理器初始化"""
        assert audio_processor is not None
        assert hasattr(audio_processor, 'get_cache_key')
        assert hasattr(audio_processor, 'get_cache_path')
        assert hasattr(audio_processor, 'is_cached')
        assert hasattr(audio_processor, 'save_to_cache')
        assert hasattr(audio_processor, 'load_from_cache')
        assert hasattr(audio_processor, 'clear_cache')
        assert hasattr(audio_processor, 'get_cache_size')
        assert hasattr(audio_processor, 'cleanup_cache')
    
    def test_get_cache_key(self, audio_processor):
        """测试：生成缓存key"""
        key = audio_processor.get_cache_key("test text", "alloy", 1.0)
        
        assert isinstance(key, str)
        assert len(key) == 32  # MD5哈希长度
    
    def test_get_cache_key_different_inputs(self, audio_processor):
        """测试：不同输入生成不同key"""
        key1 = audio_processor.get_cache_key("text1", "alloy", 1.0)
        key2 = audio_processor.get_cache_key("text2", "alloy", 1.0)
        
        assert key1 != key2
    
    def test_get_cache_path(self, audio_processor):
        """测试：获取缓存路径"""
        cache_key = "test_key_123"
        path = audio_processor.get_cache_path(cache_key, "mp3")
        
        assert path.name == "test_key_123.mp3"
        assert str(cache_key) in str(path)
    
    def test_is_cached_false(self, audio_processor):
        """测试：检查缓存（不存在）"""
        cache_key = "nonexistent_key"
        result = audio_processor.is_cached(cache_key, "mp3")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_save_to_cache_success(self, audio_processor, sample_audio_data, tmp_path):
        """测试：保存到缓存成功"""
        # 使用临时目录
        audio_processor.cache_dir = tmp_path / "audio_cache"
        audio_processor.cache_dir.mkdir(parents=True, exist_ok=True)
        
        cache_key = "test_key"
        path = await audio_processor.save_to_cache(cache_key, sample_audio_data, "mp3")
        
        assert path.exists()
        assert path.read_bytes() == sample_audio_data
    
    @pytest.mark.asyncio
    async def test_load_from_cache_success(self, audio_processor, sample_audio_data, tmp_path):
        """测试：从缓存加载成功"""
        # 使用临时目录
        audio_processor.cache_dir = tmp_path / "audio_cache"
        audio_processor.cache_dir.mkdir(parents=True, exist_ok=True)
        
        cache_key = "test_key"
        await audio_processor.save_to_cache(cache_key, sample_audio_data, "mp3")
        
        loaded_data = await audio_processor.load_from_cache(cache_key, "mp3")
        
        assert loaded_data == sample_audio_data
    
    @pytest.mark.asyncio
    async def test_load_from_cache_not_found(self, audio_processor):
        """测试：从缓存加载（不存在）"""
        cache_key = "nonexistent_key"
        loaded_data = await audio_processor.load_from_cache(cache_key, "mp3")
        
        assert loaded_data is None
    
    def test_clear_cache(self, audio_processor, tmp_path):
        """测试：清除缓存"""
        # 使用临时目录
        audio_processor.cache_dir = tmp_path / "audio_cache"
        audio_processor.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建一些缓存文件
        (audio_processor.cache_dir / "file1.mp3").write_bytes(b"data1")
        (audio_processor.cache_dir / "file2.mp3").write_bytes(b"data2")
        
        audio_processor.clear_cache()
        
        # 验证文件已删除
        assert not (audio_processor.cache_dir / "file1.mp3").exists()
        assert not (audio_processor.cache_dir / "file2.mp3").exists()
    
    def test_get_cache_size(self, audio_processor, tmp_path):
        """测试：获取缓存大小"""
        # 使用临时目录
        audio_processor.cache_dir = tmp_path / "audio_cache"
        audio_processor.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建一些缓存文件
        (audio_processor.cache_dir / "file1.mp3").write_bytes(b"data1")
        (audio_processor.cache_dir / "file2.mp3").write_bytes(b"data2")
        
        size = audio_processor.get_cache_size()
        
        assert size > 0
        assert size == len(b"data1") + len(b"data2")
    
    def test_cleanup_cache_under_limit(self, audio_processor, tmp_path):
        """测试：清理缓存（未超限）"""
        # 使用临时目录
        audio_processor.cache_dir = tmp_path / "audio_cache"
        audio_processor.cache_dir.mkdir(parents=True, exist_ok=True)
        audio_processor.max_cache_size = 100 * 1024 * 1024  # 100MB
        
        # 创建小文件
        (audio_processor.cache_dir / "file1.mp3").write_bytes(b"small data")
        
        audio_processor.cleanup_cache()
        
        # 文件应该还在
        assert (audio_processor.cache_dir / "file1.mp3").exists()
    
    def test_cleanup_cache_over_limit(self, audio_processor, tmp_path):
        """测试：清理缓存（超限）"""
        # 使用临时目录
        audio_processor.cache_dir = tmp_path / "audio_cache"
        audio_processor.cache_dir.mkdir(parents=True, exist_ok=True)
        audio_processor.max_cache_size = 10  # 很小的限制
        
        # 创建大文件
        (audio_processor.cache_dir / "file1.mp3").write_bytes(b"x" * 100)
        
        audio_processor.cleanup_cache()
        
        # 文件应该被删除
        assert not (audio_processor.cache_dir / "file1.mp3").exists()
