"""
记忆去重器测试

测试记忆去重和合并功能
"""

# 标准库
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

# 本地库
from app.engines.memory.deduplicator import MemoryDeduplicator
from app.engines.memory.models import Memory, MemoryType, MemorySearchResult


class TestMemoryDeduplicator:
    """测试记忆去重器"""
    
    @pytest.fixture
    def mock_engine(self):
        """Mock记忆引擎"""
        engine = MagicMock()
        engine.search_memories = AsyncMock()
        return engine
    
    @pytest.fixture
    def deduplicator(self, mock_engine):
        """创建去重器实例"""
        return MemoryDeduplicator(engine=mock_engine, similarity_threshold=0.95)
    
    @pytest.fixture
    def sample_memory(self):
        """示例记忆"""
        return Memory(
            id="mem-1",
            user_id="user-1",
            session_id="session-1",
            memory_type=MemoryType.USER,
            content="我喜欢喝咖啡",
            importance=0.8,
            created_at=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_find_duplicates_no_duplicates(self, deduplicator, sample_memory, mock_engine):
        """测试：没有重复记忆"""
        mock_engine.search_memories.return_value = []
        
        duplicates = await deduplicator.find_duplicates(sample_memory)
        
        assert len(duplicates) == 0
        mock_engine.search_memories.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_duplicates_with_duplicates(self, deduplicator, sample_memory, mock_engine):
        """测试：找到重复记忆"""
        duplicate_memory = Memory(
            id="mem-2",
            user_id="user-1",
            session_id="session-2",
            memory_type=MemoryType.USER,
            content="我喜欢喝咖啡",
            importance=0.6,
            created_at=datetime.utcnow()
        )
        
        mock_result = MemorySearchResult(
            memory=duplicate_memory,
            similarity=0.96
        )
        
        mock_engine.search_memories.return_value = [mock_result]
        
        duplicates = await deduplicator.find_duplicates(sample_memory)
        
        assert len(duplicates) == 1
        assert duplicates[0].id == "mem-2"
    
    @pytest.mark.asyncio
    async def test_find_duplicates_excludes_self(self, deduplicator, sample_memory, mock_engine):
        """测试：排除自己"""
        # 返回包含自己的结果
        mock_result = MemorySearchResult(
            memory=sample_memory,
            similarity=0.99
        )
        
        mock_engine.search_memories.return_value = [mock_result]
        
        duplicates = await deduplicator.find_duplicates(sample_memory)
        
        # 应该排除自己
        assert len(duplicates) == 0
    
    @pytest.mark.asyncio
    async def test_merge_memories(self, deduplicator):
        """测试：合并记忆"""
        memory1 = Memory(
            id="mem-1",
            user_id="user-1",
            session_id="session-1",
            memory_type=MemoryType.USER,
            content="我喜欢喝咖啡",
            importance=0.8,
            metadata={"key1": "value1"},
            created_at=datetime.utcnow()
        )
        
        memory2 = Memory(
            id="mem-2",
            user_id="user-1",
            session_id="session-2",
            memory_type=MemoryType.USER,
            content="我喜欢喝咖啡和茶",
            importance=0.6,
            metadata={"key2": "value2", "access_count": 3},
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        
        merged = await deduplicator.merge_memories([memory1, memory2])
        
        # 应该保留重要性更高的记忆ID
        assert merged.id == "mem-1"
        # 应该合并内容
        assert "咖啡" in merged.content
        assert "茶" in merged.content
        # 应该保留最高重要性
        assert merged.importance == 0.8
        # 应该合并元数据
        assert "key1" in merged.metadata
        assert "key2" in merged.metadata
        # 应该合并访问频率
        assert merged.metadata.get("access_count") == 3
    
    @pytest.mark.asyncio
    async def test_merge_memories_single(self, deduplicator):
        """测试：合并单个记忆"""
        memory = Memory(
            id="mem-1",
            user_id="user-1",
            session_id="session-1",
            memory_type=MemoryType.USER,
            content="Test",
            importance=0.5
        )
        
        merged = await deduplicator.merge_memories([memory])
        
        assert merged.id == "mem-1"
        assert merged.content == "Test"
    
    @pytest.mark.asyncio
    async def test_merge_memories_empty(self, deduplicator):
        """测试：合并空列表"""
        with pytest.raises(ValueError):
            await deduplicator.merge_memories([])

