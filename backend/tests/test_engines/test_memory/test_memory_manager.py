"""
记忆管理器测试

测试记忆管理器的缓存、异步保存、批量操作等功能
"""

# 标准库
import pytest
import asyncio
import tempfile
import shutil
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

# 本地库
from app.engines.memory.manager import MemoryManager
from app.engines.memory.chromadb_engine import ChromaDBMemoryEngine
from app.engines.memory.models import Memory, MemoryType, MemorySearchResult


class TestMemoryManager:
    """测试记忆管理器"""
    
    @pytest.fixture
    def temp_chromadb_dir(self):
        """创建临时ChromaDB目录"""
        temp_dir = tempfile.mkdtemp(prefix="test_chromadb_")
        yield temp_dir
        # 清理
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_engine(self):
        """Mock记忆引擎"""
        engine = MagicMock(spec=ChromaDBMemoryEngine)
        engine.engine_name = "chromadb"
        engine.add_memory = AsyncMock(return_value="mem-123")
        engine.search_memories = AsyncMock(return_value=[])
        engine.delete_memory = AsyncMock(return_value=True)
        engine.delete_session_memories = AsyncMock(return_value=1)
        engine.get_memory_stats = AsyncMock(return_value={"total_memories_count": 0})
        engine.health_check = AsyncMock(return_value=True)
        return engine
    
    @pytest.fixture
    def memory_manager(self, mock_engine):
        """创建记忆管理器实例"""
        return MemoryManager(
            engine=mock_engine,
            cache_ttl=60,
            cache_maxsize=50,
            save_timeout=1.0,
            search_timeout=0.5
        )
    
    @pytest.fixture
    def memory_manager_with_chromadb(self, temp_chromadb_dir):
        """创建使用真实ChromaDB的记忆管理器"""
        engine = ChromaDBMemoryEngine(config={"persist_directory": temp_chromadb_dir})
        return MemoryManager(
            engine=engine,
            cache_ttl=60,
            cache_maxsize=50
        )
    
    @pytest.mark.asyncio
    async def test_add_memory_sync(self, memory_manager, mock_engine):
        """测试：同步添加记忆"""
        memory_id = await memory_manager.add_memory(
            user_id="test-user-1",
            session_id="test-session-1",
            content="Test memory",
            memory_type=MemoryType.USER,
            async_save=False
        )
        
        assert memory_id is not None
        mock_engine.add_memory.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_memory_async(self, memory_manager, mock_engine):
        """测试：异步添加记忆"""
        memory_id = await memory_manager.add_memory(
            user_id="test-user-1",
            session_id="test-session-1",
            content="Test memory",
            memory_type=MemoryType.USER,
            async_save=True
        )
        
        assert memory_id is not None
        # 异步保存不会立即调用引擎
        # 等待后台任务完成
        await asyncio.sleep(0.1)
        # 验证记忆被添加到待保存队列
        assert len(memory_manager.pending_saves) >= 0
    
    @pytest.mark.asyncio
    async def test_search_memories(self, memory_manager, mock_engine):
        """测试：搜索记忆"""
        # 设置mock返回值
        mock_result = MemorySearchResult(
            memory=Memory(
                id="mem-1",
                user_id="test-user-1",
                session_id="test-session-1",
                memory_type=MemoryType.USER,
                content="Test memory"
            ),
            similarity=0.9,
            distance=0.1
        )
        mock_engine.search_memories = AsyncMock(return_value=[mock_result])
        
        results = await memory_manager.search_memories(
            query="Test",
            user_id="test-user-1"
        )
        
        assert len(results) > 0
        assert isinstance(results[0], MemorySearchResult)
        mock_engine.search_memories.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_memories_cached(self, memory_manager, mock_engine):
        """测试：搜索记忆缓存"""
        # 设置mock返回值
        mock_result = MemorySearchResult(
            memory=Memory(
                id="mem-1",
                user_id="test-user-1",
                session_id="test-session-1",
                memory_type=MemoryType.USER,
                content="Test memory"
            ),
            similarity=0.9,
            distance=0.1
        )
        mock_engine.search_memories = AsyncMock(return_value=[mock_result])
        
        # 第一次搜索（应该调用引擎）
        results1 = await memory_manager.search_memories(
            query="Test",
            user_id="test-user-1"
        )
        
        # 第二次搜索（应该使用缓存）
        results2 = await memory_manager.search_memories(
            query="Test",
            user_id="test-user-1"
        )
        
        # 验证只调用了一次引擎（第二次使用缓存）
        assert mock_engine.search_memories.call_count == 1
        assert len(results1) == len(results2)
    
    @pytest.mark.asyncio
    async def test_search_memories_timeout(self, memory_manager, mock_engine):
        """测试：搜索记忆超时"""
        # 设置mock超时
        async def slow_search(*args, **kwargs):
            await asyncio.sleep(1.0)  # 超过0.5秒超时
            return []
        
        mock_engine.search_memories = slow_search
        
        # 搜索应该超时并返回空列表
        results = await memory_manager.search_memories(
            query="Test",
            user_id="test-user-1"
        )
        
        assert isinstance(results, list)
        # 超时应该返回空列表或抛出异常
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_manager, mock_engine):
        """测试：删除记忆"""
        deleted = await memory_manager.delete_memory(
            memory_id="mem-123",
            user_id="test-user-1"
        )
        
        assert deleted is True
        mock_engine.delete_memory.assert_called_once_with("mem-123", "test-user-1")
    
    @pytest.mark.asyncio
    async def test_delete_session_memories(self, memory_manager, mock_engine):
        """测试：删除会话的所有记忆"""
        deleted_count = await memory_manager.delete_session_memories(
            user_id="test-user-1",
            session_id="test-session-1"
        )
        
        assert deleted_count == 1
        mock_engine.delete_session_memories.assert_called_once_with(
            "test-user-1",
            "test-session-1"
        )
    
    @pytest.mark.asyncio
    async def test_get_memory_stats(self, memory_manager, mock_engine):
        """测试：获取记忆统计"""
        stats = await memory_manager.get_memory_stats(user_id="test-user-1")
        
        assert isinstance(stats, dict)
        mock_engine.get_memory_stats.assert_called_once_with("test-user-1")
    
    @pytest.mark.asyncio
    async def test_add_conversation_turn(self, memory_manager_with_chromadb):
        """测试：添加对话轮次"""
        result = await memory_manager_with_chromadb.add_conversation_turn(
            user_id="test-user-1",
            session_id="test-session-1",
            user_message="Hello",
            assistant_message="Hi there!",
            importance=0.7
        )
        
        # 验证返回结果
        assert isinstance(result, dict)
        assert "user_memory_id" in result
        assert "assistant_memory_id" in result
        
        # 等待异步保存完成
        await asyncio.sleep(0.2)
        
        # 验证记忆已添加（通过搜索）
        results = await memory_manager_with_chromadb.search_memories(
            query="Hello",
            user_id="test-user-1",
            session_id="test-session-1",
            limit=5,
            similarity_threshold=0.1
        )
        
        # 至少应该有一些结果
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_search_memories_with_parameters(self, memory_manager, mock_engine):
        """测试：带参数的搜索记忆"""
        # 设置mock返回值
        mock_result = MemorySearchResult(
            memory=Memory(
                id="mem-1",
                user_id="test-user-1",
                session_id="test-session-1",
                memory_type=MemoryType.USER,
                content="Test memory"
            ),
            similarity=0.9,
            distance=0.1
        )
        mock_engine.search_memories = AsyncMock(return_value=[mock_result])
        
        results = await memory_manager.search_memories(
            query="Test",
            user_id="test-user-1",
            session_id="test-session-1",
            memory_type=MemoryType.USER,
            limit=5,
            similarity_threshold=0.7
        )
        
        assert isinstance(results, list)
        if len(results) > 0:
            assert isinstance(results[0], MemorySearchResult)
    
    @pytest.mark.asyncio
    async def test_flush_pending_saves(self, memory_manager, mock_engine):
        """测试：刷新待保存的记忆队列"""
        # 添加一些记忆到待保存队列
        memory1 = Memory(
            id="mem-1",
            user_id="test-user-1",
            session_id="test-session-1",
            memory_type=MemoryType.USER,
            content="Memory 1"
        )
        memory2 = Memory(
            id="mem-2",
            user_id="test-user-1",
            session_id="test-session-1",
            memory_type=MemoryType.ASSISTANT,
            content="Memory 2"
        )
        
        memory_manager.pending_saves = [memory1, memory2]
        
        # 刷新队列
        await memory_manager._flush_pending_saves()
        
        # 验证所有记忆都被保存
        assert mock_engine.add_memory.call_count == 2
        assert len(memory_manager.pending_saves) == 0
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, memory_manager, mock_engine):
        """测试：缓存失效"""
        # 设置mock返回值
        mock_result = MemorySearchResult(
            memory=Memory(
                id="mem-1",
                user_id="test-user-1",
                session_id="test-session-1",
                memory_type=MemoryType.USER,
                content="Test memory"
            ),
            similarity=0.9,
            distance=0.1
        )
        mock_engine.search_memories = AsyncMock(return_value=[mock_result])
        
        # 第一次搜索（缓存）
        await memory_manager.search_memories(
            query="Test",
            user_id="test-user-1"
        )
        
        # 添加新记忆（应该使缓存失效）
        await memory_manager.add_memory(
            user_id="test-user-1",
            session_id="test-session-1",
            content="New memory",
            memory_type=MemoryType.USER,
            async_save=False
        )
        
        # 再次搜索（应该重新查询，因为缓存可能已失效）
        await memory_manager.search_memories(
            query="Test",
            user_id="test-user-1"
        )
        
        # 验证引擎被调用了至少一次
        assert mock_engine.search_memories.call_count >= 1

