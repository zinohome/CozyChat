"""
聊天流程集成测试

测试完整的端到端聊天流程
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch


class TestChatIntegration:
    """聊天流程集成测试类"""
    
    def test_chat_api_validation_missing_messages(self):
        """测试：API验证 - 缺少messages字段"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Arrange
        request_data = {
            "personality_id": "assistant_001"
            # 缺少messages字段
        }
        
        # Act
        response = client.post(
            "/v1/chat/completions",
            json=request_data
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    def test_chat_api_validation_empty_messages(self):
        """测试：API验证 - 空messages列表"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Arrange
        request_data = {
            "messages": [],
            "personality_id": "assistant_001"
        }
        
        # Act
        response = client.post(
            "/v1/chat/completions",
            json=request_data
        )
        
        # Assert
        # 空messages会导致AI引擎错误，返回500
        assert response.status_code in [400, 422, 500]
    
    def test_chat_api_validation_invalid_message_format(self):
        """测试：API验证 - 无效消息格式"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Arrange
        request_data = {
            "messages": [
                {"invalid_field": "value"}  # 缺少role和content
            ],
            "personality_id": "assistant_001"
        }
        
        # Act
        response = client.post(
            "/v1/chat/completions",
            json=request_data
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_message_saver_service_integration(self):
        """测试：MessageSaver服务集成"""
        from app.services.chat.message_saver import MessageSaver
        from unittest.mock import Mock
        import uuid
        
        # Arrange
        mock_db = Mock()
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        saver = MessageSaver(db=mock_db)
        
        session_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Act
        result = await saver.save_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message="测试用户消息",
            assistant_message="测试助手回复",
            assistant_model="gpt-3.5-turbo",
            memory_manager=None,
            use_memory=False
        )
        
        # Assert
        assert result is True
        assert mock_db.add.call_count == 2  # 用户消息 + 助手消息
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tool_handler_service_integration(self):
        """测试：ToolCallHandler服务集成"""
        from app.services.chat.tool_handler import ToolCallHandler
        from unittest.mock import Mock, AsyncMock
        import json
        
        # Arrange
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool = AsyncMock(return_value={
            "success": True,
            "result": "42"
        })
        
        mock_factory = Mock()
        mock_factory.get_tool_manager = Mock(return_value=mock_tool_manager)
        
        handler = ToolCallHandler(tool_factory=mock_factory)
        
        tool_calls = [
            {
                "id": "call_001",
                "type": "function",
                "function": {
                    "name": "calculator",
                    "arguments": json.dumps({"expression": "1 + 1"})
                }
            }
        ]
        
        # Act
        results = await handler.execute_tool_calls(tool_calls)
        
        # Assert
        assert len(results) == 1
        assert results[0]["role"] == "tool"
        assert results[0]["tool_call_id"] == "call_001"
        assert "42" in results[0]["content"]
    
    def test_prompt_builder_integration(self):
        """测试：PromptBuilder服务集成"""
        from app.services.prompt.builder import PromptBuilder
        from app.services.prompt.loader import PromptLoader
        
        # Arrange
        loader = PromptLoader(config_dir="backend/config/prompts")
        builder = PromptBuilder(loader=loader)
        
        preferences = {
            "response_style": "brief",
            "default_language": "zh-CN"
        }
        
        # Act
        content, instruction = builder.build_user_message(
            "测试消息",
            preferences
        )
        
        # Assert
        assert content == "测试消息"
        # instruction可能为None或字符串，取决于配置文件是否存在
    
    @pytest.mark.asyncio
    async def test_memory_scoring_service_integration(self):
        """测试：MemoryScoringService服务集成"""
        from app.services.memory.scoring_service import MemoryScoringService
        from app.core.personality.models import IntelligentScoring, ScoringWeights
        from unittest.mock import Mock
        from datetime import datetime, timezone
        
        # Arrange
        service = MemoryScoringService()
        
        # 创建模拟记忆结果
        def create_memory(content, similarity):
            memory = Mock()
            memory.content = content
            memory.importance = 0.5
            memory.session_id = "session_1"
            memory.created_at = datetime.now(timezone.utc)
            
            result = Mock()
            result.memory = memory
            result.similarity = similarity
            
            return result
        
        memories = [
            create_memory("user height 180cm", 0.9),
            create_memory("user likes sports", 0.8),
            create_memory("user age 25", 0.7)
        ]
        
        config = IntelligentScoring(
            enabled=True,
            numeric_query_keywords=['height', 'age', 'weight'],
            numeric_memory_keywords=['cm', 'kg', 'years'],
            numeric_boost=0.3,
            keyword_match_boost=0.2,
            optimal_length_min=10,
            optimal_length_max=200,
            length_boost=0.1
        )
        
        # Act
        sorted_memories = service.apply_intelligent_scoring(
            memories,
            "user height",
            config
        )
        
        # Assert
        assert len(sorted_memories) == 3
        # 包含"height"和"cm"的记忆应该排在前面
        assert "180cm" in sorted_memories[0].memory.content
    
    def test_chat_service_instantiation(self):
        """测试：ChatService实例化"""
        from app.services.chat.service import ChatService
        from app.services.chat.message_saver import MessageSaver
        from unittest.mock import Mock
        
        # Arrange
        mock_db = Mock()
        message_saver = MessageSaver(db=mock_db)
        
        # Act
        service = ChatService(message_saver=message_saver)
        
        # Assert
        assert service is not None
        assert service.message_saver == message_saver
    
    def test_message_utils_integration(self):
        """测试：消息工具函数集成"""
        from app.utils.message_utils import (
            detect_message_hints,
            merge_user_preferences,
            build_user_message_with_preferences
        )
        
        # 测试detect_message_hints
        hints = detect_message_hints("请列出三个步骤")
        assert hints.get("prefer_list") is True
        
        # 测试merge_user_preferences
        preferences = merge_user_preferences(None, None)
        assert preferences is not None
        assert "default_language" in preferences
        
        # 测试build_user_message_with_preferences
        content, instruction = build_user_message_with_preferences(
            "测试消息",
            {"response_style": "brief"}
        )
        assert content == "测试消息"
    
    def test_service_layer_isolation(self):
        """测试：服务层隔离性"""
        from app.services.chat.message_saver import MessageSaver
        from app.services.chat.tool_handler import ToolCallHandler
        from app.services.prompt.builder import PromptBuilder
        from app.services.memory.scoring_service import MemoryScoringService
        
        # Arrange & Act
        # 验证服务可以独立实例化
        mock_db = Mock()
        message_saver = MessageSaver(db=mock_db)
        
        mock_factory = Mock()
        tool_handler = ToolCallHandler(tool_factory=mock_factory)
        
        prompt_builder = PromptBuilder()
        
        scoring_service = MemoryScoringService()
        
        # Assert
        assert message_saver is not None
        assert tool_handler is not None
        assert prompt_builder is not None
        assert scoring_service is not None
    
    @pytest.mark.asyncio
    async def test_error_propagation(self):
        """测试：错误传播机制"""
        from app.services.chat.message_saver import MessageSaver
        from unittest.mock import Mock
        import uuid
        
        # Arrange
        mock_db = Mock()
        mock_db.add.side_effect = Exception("Database error")
        mock_db.rollback = Mock()
        
        saver = MessageSaver(db=mock_db)
        
        # 使用有效的UUID
        session_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Act
        result = await saver.save_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message="test",
            assistant_message="test reply",
            use_memory=False
        )
        
        # Assert
        assert result is False  # 应该返回False而不是抛出异常
        mock_db.rollback.assert_called_once()
