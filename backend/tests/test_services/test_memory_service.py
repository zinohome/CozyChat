"""
MemoryService单元测试

测试记忆服务的所有功能，包括：
- 保存记忆
- 检索记忆
- 删除记忆
- 列出记忆
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Any

from app.services.memory_service import MemoryService
from app.engines.memory.manager import MemoryManager


class TestMemoryService:
    """MemoryService单元测试类"""
    
    @pytest.fixture
    def mock_memory_manager(self):
        """创建模拟记忆管理器"""
        manager = MagicMock(spec=MemoryManager)
        manager.add_memory = AsyncMock(return_value="memory-id-123")
        manager.retrieve_memories = AsyncMock(return_value={
            "user_memories": [],
            "ai_memories": []
        })
        manager.delete_memory = AsyncMock(return_value=True)
        manager.list_memories = AsyncMock(return_value=[])
        return manager
    
    @pytest.fixture
    def memory_service(self, mock_memory_manager):
        """创建MemoryService实例"""
        return MemoryService(memory_manager=mock_memory_manager)
    
    @pytest.mark.asyncio
    async def test_save_memory_success(
        self,
        memory_service,
        mock_memory_manager
    ):
        """测试：成功保存记忆"""
        # Arrange
        user_id = "test-user-id"
        session_id = "test-session-id"
        content = "User likes Python programming"
        memory_type = "user"
        
        # Act
        result = await memory_service.save_memory(
            user_id=user_id,
            session_id=session_id,
            content=content,
            memory_type=memory_type
        )
        
        # Assert
        assert result == "memory-id-123"
        mock_memory_manager.add_memory.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_memories_success(
        self,
        memory_service,
        mock_memory_manager
    ):
        """测试：成功检索记忆"""
        # Arrange
        user_id = "test-user-id"
        session_id = "test-session-id"
        query = "Python programming"
        
        # Act
        result = await memory_service.retrieve_memories(
            user_id=user_id,
            session_id=session_id,
            query=query
        )
        
        # Assert
        assert result is not None
        assert "user_memories" in result
        assert "ai_memories" in result
        mock_memory_manager.retrieve_memories.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_memory_success(
        self,
        memory_service,
        mock_memory_manager
    ):
        """测试：成功删除记忆"""
        # Arrange
        user_id = "test-user-id"
        memory_id = "memory-id-123"
        
        # Act
        result = await memory_service.delete_memory(
            user_id=user_id,
            memory_id=memory_id
        )
        
        # Assert
        assert result is True
        mock_memory_manager.delete_memory.assert_called_once_with(
            user_id=user_id,
            memory_id=memory_id
        )
    
    @pytest.mark.asyncio
    async def test_list_memories_success(
        self,
        memory_service,
        mock_memory_manager
    ):
        """测试：成功列出记忆"""
        # Arrange
        user_id = "test-user-id"
        session_id = "test-session-id"
        limit = 20
        
        # Act
        result = await memory_service.list_memories(
            user_id=user_id,
            session_id=session_id,
            limit=limit
        )
        
        # Assert
        assert result is not None
        assert isinstance(result, list)
        mock_memory_manager.list_memories.assert_called_once()
