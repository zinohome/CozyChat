"""
Qdrant记忆引擎测试

测试Qdrant记忆引擎的添加、搜索、删除等功能
"""

# 标准库
import pytest
from datetime import datetime, timedelta
from typing import List
from unittest.mock import Mock, AsyncMock, patch

# 本地库
from app.engines.memory.qdrant_engine import QdrantMemoryEngine
from app.engines.memory.models import Memory, MemoryType, MemorySearchResult


class TestQdrantEngine:
    """测试Qdrant引擎"""
    
    @pytest.fixture
    def mock_qdrant_client(self):
        """Mock Qdrant客户端"""
        with patch('app.engines.memory.qdrant_engine.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock get_collections
            mock_collections = Mock()
            mock_collections.collections = []
            mock_client.get_collections.return_value = mock_collections
            
            # Mock create_collection
            mock_client.create_collection.return_value = None
            
            # Mock upsert
            mock_client.upsert.return_value = None
            
            # Mock search
            mock_client.search.return_value = []
            
            # Mock delete
            mock_client.delete.return_value = True
            
            # Mock scroll
            mock_client.scroll.return_value = ([], None)
            
            # Mock get_collection
            mock_collection_info = Mock()
            mock_client.get_collection.return_value = mock_collection_info
            
            yield mock_client
    
    @pytest.fixture
    def mock_sentence_transformer(self):
        """Mock sentence-transformers模型"""
        with patch('app.engines.memory.qdrant_engine.SentenceTransformer') as mock_st:
            mock_model = Mock()
            # 返回固定维度的向量
            mock_model.encode.return_value = [0.1] * 384
            mock_st.return_value = mock_model
            yield mock_model
    
    @pytest.fixture
    def qdrant_engine(self, mock_qdrant_client, mock_sentence_transformer):
        """创建Qdrant引擎实例"""
        config = {
            "url": "http://localhost:6333",
            "collection_prefix": "test_",
            "embedding": {
                "model": "all-MiniLM-L6-v2",
                "dimension": 384
            }
        }
        return QdrantMemoryEngine(config=config)
    
    @pytest.fixture
    def sample_memory_user(self):
        """示例用户记忆"""
        return Memory(
            id="mem-user-1",
            user_id="test-user-1",
            session_id="test-session-1",
            memory_type=MemoryType.USER,
            content="I like Python programming",
            importance=0.8
        )
    
    @pytest.fixture
    def sample_memory_assistant(self):
        """示例AI记忆"""
        return Memory(
            id="mem-assistant-1",
            user_id="test-user-1",
            session_id="test-session-1",
            memory_type=MemoryType.ASSISTANT,
            content="You mentioned you like Python programming",
            importance=0.7
        )
    
    @pytest.mark.asyncio
    async def test_add_memory_user(
        self,
        qdrant_engine,
        sample_memory_user,
        mock_qdrant_client
    ):
        """测试：添加用户记忆"""
        memory_id = await qdrant_engine.add_memory(sample_memory_user)
        
        assert memory_id == sample_memory_user.id
        
        # 验证调用了upsert
        mock_qdrant_client.upsert.assert_called_once()
        call_args = mock_qdrant_client.upsert.call_args
        assert call_args.kwargs["collection_name"] == "test_user_memories"
    
    @pytest.mark.asyncio
    async def test_add_memory_assistant(
        self,
        qdrant_engine,
        sample_memory_assistant,
        mock_qdrant_client
    ):
        """测试：添加AI记忆"""
        memory_id = await qdrant_engine.add_memory(sample_memory_assistant)
        
        assert memory_id == sample_memory_assistant.id
        
        # 验证调用了upsert
        mock_qdrant_client.upsert.assert_called_once()
        call_args = mock_qdrant_client.upsert.call_args
        assert call_args.kwargs["collection_name"] == "test_assistant_memories"
    
    @pytest.mark.asyncio
    async def test_search_memories(
        self,
        qdrant_engine,
        sample_memory_user,
        mock_qdrant_client
    ):
        """测试：搜索记忆"""
        # Mock搜索结果
        mock_scored_point = Mock()
        mock_scored_point.id = sample_memory_user.id
        mock_scored_point.score = 0.85
        mock_scored_point.payload = {
            "user_id": sample_memory_user.user_id,
            "session_id": sample_memory_user.session_id,
            "content": sample_memory_user.content,
            "importance": sample_memory_user.importance,
            "created_at": sample_memory_user.created_at.timestamp(),
            "memory_type": sample_memory_user.memory_type.value
        }
        
        mock_qdrant_client.search.return_value = [mock_scored_point]
        
        # 搜索记忆
        results = await qdrant_engine.search_memories(
            query="Python programming",
            user_id="test-user-1",
            limit=5,
            similarity_threshold=0.7
        )
        
        # 验证结果
        assert isinstance(results, list)
        assert len(results) > 0
        assert isinstance(results[0], MemorySearchResult)
        assert results[0].memory.user_id == "test-user-1"
        assert results[0].similarity == 0.85
        
        # 验证调用了search（两次，一次user collection，一次assistant collection）
        assert mock_qdrant_client.search.call_count == 2
    
    @pytest.mark.asyncio
    async def test_search_memories_with_session(
        self,
        qdrant_engine,
        sample_memory_user,
        mock_qdrant_client
    ):
        """测试：按会话搜索记忆"""
        # Mock搜索结果
        mock_scored_point = Mock()
        mock_scored_point.id = sample_memory_user.id
        mock_scored_point.score = 0.85
        mock_scored_point.payload = {
            "user_id": sample_memory_user.user_id,
            "session_id": sample_memory_user.session_id,
            "content": sample_memory_user.content,
            "importance": sample_memory_user.importance,
            "created_at": sample_memory_user.created_at.timestamp(),
            "memory_type": sample_memory_user.memory_type.value
        }
        
        mock_qdrant_client.search.return_value = [mock_scored_point]
        
        # 搜索特定会话的记忆
        results = await qdrant_engine.search_memories(
            query="Python",
            user_id="test-user-1",
            session_id="test-session-1",
            limit=5,
            similarity_threshold=0.7
        )
        
        # 验证结果
        assert isinstance(results, list)
        if len(results) > 0:
            assert results[0].memory.session_id == "test-session-1"
    
    @pytest.mark.asyncio
    async def test_search_memories_with_type(
        self,
        qdrant_engine,
        sample_memory_user,
        mock_qdrant_client
    ):
        """测试：按类型搜索记忆"""
        # Mock搜索结果
        mock_scored_point = Mock()
        mock_scored_point.id = sample_memory_user.id
        mock_scored_point.score = 0.85
        mock_scored_point.payload = {
            "user_id": sample_memory_user.user_id,
            "session_id": sample_memory_user.session_id,
            "content": sample_memory_user.content,
            "importance": sample_memory_user.importance,
            "created_at": sample_memory_user.created_at.timestamp(),
            "memory_type": sample_memory_user.memory_type.value
        }
        
        mock_qdrant_client.search.return_value = [mock_scored_point]
        
        # 只搜索用户记忆
        results = await qdrant_engine.search_memories(
            query="Python",
            user_id="test-user-1",
            memory_type=MemoryType.USER,
            limit=5,
            similarity_threshold=0.7
        )
        
        # 验证结果
        assert isinstance(results, list)
        if len(results) > 0:
            assert results[0].memory.memory_type == MemoryType.USER
        
        # 验证只调用了一次search（只搜索user collection）
        assert mock_qdrant_client.search.call_count == 1
    
    @pytest.mark.asyncio
    async def test_delete_memory(
        self,
        qdrant_engine,
        sample_memory_user,
        mock_qdrant_client
    ):
        """测试：删除记忆"""
        # Mock删除成功
        mock_qdrant_client.delete.return_value = True
        
        # 删除记忆
        deleted = await qdrant_engine.delete_memory(
            memory_id=sample_memory_user.id,
            user_id="test-user-1"
        )
        
        assert deleted is True
        
        # 验证调用了delete
        assert mock_qdrant_client.delete.called
    
    @pytest.mark.asyncio
    async def test_delete_session_memories(
        self,
        qdrant_engine,
        mock_qdrant_client
    ):
        """测试：删除会话的所有记忆"""
        # Mock删除成功
        mock_qdrant_client.delete.return_value = True
        
        # 删除test-session-1的所有记忆
        deleted_count = await qdrant_engine.delete_session_memories(
            user_id="test-user-1",
            session_id="test-session-1"
        )
        
        assert deleted_count >= 0
        
        # 验证调用了delete（两次，一次user collection，一次assistant collection）
        assert mock_qdrant_client.delete.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_memory_stats(
        self,
        qdrant_engine,
        mock_qdrant_client
    ):
        """测试：获取记忆统计"""
        # Mock scroll返回结果
        mock_point = Mock()
        mock_qdrant_client.scroll.return_value = ([mock_point], None)
        
        # 获取统计信息
        stats = await qdrant_engine.get_memory_stats(user_id="test-user-1")
        
        assert isinstance(stats, dict)
        # 验证统计信息包含必要的字段
        assert "user_id" in stats
        assert "user_memories_count" in stats
        assert "assistant_memories_count" in stats
        assert "total_memories_count" in stats
    
    @pytest.mark.asyncio
    async def test_add_memory_with_metadata(
        self,
        qdrant_engine,
        mock_qdrant_client
    ):
        """测试：添加带元数据的记忆"""
        memory = Memory(
            id="mem-metadata-1",
            user_id="test-user-1",
            session_id="test-session-1",
            memory_type=MemoryType.USER,
            content="Test memory with metadata",
            importance=0.5,
            metadata={"source": "test", "category": "test"}
        )
        
        memory_id = await qdrant_engine.add_memory(memory)
        
        assert memory_id == memory.id
        
        # 验证元数据被包含在payload中
        mock_qdrant_client.upsert.assert_called_once()
        call_args = mock_qdrant_client.upsert.call_args
        points = call_args.kwargs["points"]
        assert len(points) > 0
        assert "source" in points[0].payload
        assert "category" in points[0].payload
    
    @pytest.mark.asyncio
    async def test_add_memory_with_expires_at(
        self,
        qdrant_engine,
        mock_qdrant_client
    ):
        """测试：添加带过期时间的记忆"""
        memory = Memory(
            id="mem-expires-1",
            user_id="test-user-1",
            session_id="test-session-1",
            memory_type=MemoryType.USER,
            content="Test memory with expiration",
            importance=0.5,
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
        
        memory_id = await qdrant_engine.add_memory(memory)
        
        assert memory_id == memory.id
        
        # 验证expires_at被包含在payload中
        mock_qdrant_client.upsert.assert_called_once()
        call_args = mock_qdrant_client.upsert.call_args
        points = call_args.kwargs["points"]
        assert len(points) > 0
        assert "expires_at" in points[0].payload
    
    @pytest.mark.asyncio
    async def test_search_memories_similarity_threshold(
        self,
        qdrant_engine,
        sample_memory_user,
        mock_qdrant_client
    ):
        """测试：搜索记忆的相似度阈值"""
        # Mock两个不同相似度的结果
        mock_point_high = Mock()
        mock_point_high.id = "mem-1"
        mock_point_high.score = 0.95
        mock_point_high.payload = {
            "user_id": "test-user-1",
            "session_id": "test-session-1",
            "content": "Python programming",
            "importance": 0.8,
            "created_at": datetime.utcnow().timestamp(),
            "memory_type": "user"
        }
        
        mock_point_low = Mock()
        mock_point_low.id = "mem-2"
        mock_point_low.score = 0.5
        mock_point_low.payload = {
            "user_id": "test-user-1",
            "session_id": "test-session-1",
            "content": "Different topic",
            "importance": 0.6,
            "created_at": datetime.utcnow().timestamp(),
            "memory_type": "user"
        }
        
        # 第一次搜索（低阈值）返回两个结果
        mock_qdrant_client.search.return_value = [mock_point_high, mock_point_low]
        
        results_low = await qdrant_engine.search_memories(
            query="Python",
            user_id="test-user-1",
            similarity_threshold=0.3,
            limit=5
        )
        
        # 第二次搜索（高阈值）只返回高相似度结果
        mock_qdrant_client.search.return_value = [mock_point_high]
        
        results_high = await qdrant_engine.search_memories(
            query="Python",
            user_id="test-user-1",
            similarity_threshold=0.9,
            limit=5
        )
        
        # 低阈值应该返回更多结果
        assert len(results_low) >= len(results_high)
    
    @pytest.mark.asyncio
    async def test_add_memory_with_custom_embedding(
        self,
        qdrant_engine,
        mock_qdrant_client
    ):
        """测试：添加带自定义向量的记忆"""
        custom_embedding = [0.5] * 384
        memory = Memory(
            id="mem-custom-emb-1",
            user_id="test-user-1",
            session_id="test-session-1",
            memory_type=MemoryType.USER,
            content="Test memory with custom embedding",
            importance=0.5,
            embedding=custom_embedding
        )
        
        memory_id = await qdrant_engine.add_memory(memory)
        
        assert memory_id == memory.id
        
        # 验证使用了自定义向量
        mock_qdrant_client.upsert.assert_called_once()
        call_args = mock_qdrant_client.upsert.call_args
        points = call_args.kwargs["points"]
        assert len(points) > 0
        assert points[0].vector == custom_embedding
    
    def test_get_collection_name(self, qdrant_engine):
        """测试：获取集合名称"""
        # 测试用户记忆集合
        user_collection = qdrant_engine._get_collection_name(MemoryType.USER)
        assert user_collection == "test_user_memories"
        
        # 测试AI记忆集合
        assistant_collection = qdrant_engine._get_collection_name(MemoryType.ASSISTANT)
        assert assistant_collection == "test_assistant_memories"
        
        # 测试不支持的类型
        with pytest.raises(ValueError):
            qdrant_engine._get_collection_name(MemoryType.SYSTEM)
    
    @pytest.mark.asyncio
    async def test_search_memories_empty_results(
        self,
        qdrant_engine,
        mock_qdrant_client
    ):
        """测试：搜索无结果"""
        # Mock空搜索结果
        mock_qdrant_client.search.return_value = []
        
        results = await qdrant_engine.search_memories(
            query="nonexistent topic",
            user_id="test-user-1",
            limit=5,
            similarity_threshold=0.7
        )
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_memory(
        self,
        qdrant_engine,
        mock_qdrant_client
    ):
        """测试：删除不存在的记忆"""
        # Mock删除失败（抛出异常）
        mock_qdrant_client.delete.side_effect = Exception("Not found")
        
        deleted = await qdrant_engine.delete_memory(
            memory_id="nonexistent-id",
            user_id="test-user-1"
        )
        
        assert deleted is False

