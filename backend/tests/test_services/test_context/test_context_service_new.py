"""
ContextServiceNew单元测试

测试ContextServiceNew的所有方法，包括：
- 三大引擎集成（Knowledge、UserProfile、ChatMemory）
- 超时控制
- 降级策略
- 各种意图场景
"""

# 标准库
import asyncio
import time
import uuid
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock, patch, Mock

# 第三方库
import pytest
import pytest_asyncio

# 本地库
from app.services.context.context_service_new import ContextServiceNew
from app.services.context.intent_analyzer import QueryIntent
from app.schemas.context import ContextBundle


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_knowledge_engine():
    """Mock Knowledge Engine"""
    engine = MagicMock()
    engine.initialize = AsyncMock(return_value=True)
    engine.health_check = AsyncMock(return_value=True)
    engine.search_knowledge = AsyncMock(return_value=[
        {"content": "Python是一种编程语言", "score": 0.9},
        {"content": "Python支持面向对象编程", "score": 0.8}
    ])
    return engine


@pytest.fixture
def mock_userprofile_engine():
    """Mock UserProfile Engine"""
    engine = MagicMock()
    engine.initialize = AsyncMock(return_value=True)
    engine.health_check = AsyncMock(return_value=True)
    engine.get_profile = AsyncMock(return_value={
        "user_id": "test_user",
        "profile_text": "用户喜欢编程，擅长Python",
        "token_size": 50
    })
    engine.update_profile = AsyncMock(return_value=True)
    return engine


@pytest.fixture
def mock_chatmemory_engine():
    """Mock ChatMemory Engine"""
    engine = MagicMock()
    engine.initialize = AsyncMock(return_value=True)
    engine.health_check = AsyncMock(return_value=True)
    engine.search_memories = AsyncMock(return_value=[
        {"content": "之前讨论过Python", "relevance": 0.85},
        {"content": "用户询问过编程问题", "relevance": 0.75}
    ])
    engine.add_memory = AsyncMock(return_value=True)
    return engine


@pytest.fixture
def context_service_with_mocks(mock_knowledge_engine, mock_userprofile_engine, mock_chatmemory_engine):
    """创建带Mock引擎的ContextServiceNew实例"""
    # 重置单例
    ContextServiceNew._instance = None
    
    # 使用patch替换引擎工厂
    with patch('app.services.context.context_service_new.KnowledgeEngineFactory') as mock_knowledge_factory, \
         patch('app.services.context.context_service_new.UserProfileEngineFactory') as mock_userprofile_factory, \
         patch('app.services.context.context_service_new.ChatMemoryEngineFactory') as mock_chatmemory_factory:
        
        # 配置工厂返回Mock引擎
        mock_knowledge_factory.create_engine.return_value = mock_knowledge_engine
        mock_userprofile_factory.create_engine.return_value = mock_userprofile_engine
        mock_chatmemory_factory.create_engine.return_value = mock_chatmemory_engine
        
        # 创建服务实例
        service = ContextServiceNew.get_instance()
        yield service
        
        # 清理
        ContextServiceNew._instance = None


@pytest.fixture
def db_session():
    """Mock数据库会话"""
    session = MagicMock()
    return session


# ============================================================================
# 测试：初始化和单例模式
# ============================================================================

class TestContextServiceNewInitialization:
    """测试ContextServiceNew的初始化"""
    
    @pytest.mark.asyncio
    async def test_get_instance_singleton(self, context_service_with_mocks):
        """测试：单例模式"""
        service1 = ContextServiceNew.get_instance()
        service2 = ContextServiceNew.get_instance()
        
        assert service1 is service2
        assert service1 is not None
    
    @pytest.mark.asyncio
    async def test_initialize_all_engines_success(self, context_service_with_mocks):
        """测试：所有引擎初始化成功"""
        service = context_service_with_mocks
        
        result = await service.initialize()
        
        assert result is True
        assert service._initialized is True
        service.knowledge_engine.initialize.assert_called_once()
        service.userprofile_engine.initialize.assert_called_once()
        service.chatmemory_engine.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_partial_success(self, context_service_with_mocks):
        """测试：部分引擎初始化成功（降级策略）"""
        service = context_service_with_mocks
        
        # 设置部分引擎初始化失败
        service.knowledge_engine.initialize = AsyncMock(return_value=False)
        service.userprofile_engine.initialize = AsyncMock(return_value=True)
        service.chatmemory_engine.initialize = AsyncMock(return_value=True)
        
        result = await service.initialize()
        
        # 至少一个引擎成功即可
        assert result is True
        assert service._initialized is True
    
    @pytest.mark.asyncio
    async def test_initialize_all_failed(self, context_service_with_mocks):
        """测试：所有引擎初始化失败"""
        service = context_service_with_mocks
        
        # 设置所有引擎初始化失败
        service.knowledge_engine.initialize = AsyncMock(return_value=False)
        service.userprofile_engine.initialize = AsyncMock(return_value=False)
        service.chatmemory_engine.initialize = AsyncMock(return_value=False)
        
        result = await service.initialize()
        
        assert result is False
        assert service._initialized is False
    
    @pytest.mark.asyncio
    async def test_initialize_with_exception(self, context_service_with_mocks):
        """测试：初始化时发生异常"""
        service = context_service_with_mocks
        
        # 设置引擎抛出异常
        service.knowledge_engine.initialize = AsyncMock(side_effect=Exception("Connection error"))
        service.userprofile_engine.initialize = AsyncMock(return_value=True)
        service.chatmemory_engine.initialize = AsyncMock(return_value=True)
        
        result = await service.initialize()
        
        # 即使有异常，只要其他引擎成功，仍然返回True
        assert result is True
    
    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, context_service_with_mocks):
        """测试：初始化是幂等的"""
        service = context_service_with_mocks
        
        # 第一次初始化
        result1 = await service.initialize()
        assert result1 is True
        
        # 第二次初始化（应该直接返回，不重复调用）
        call_count_before = service.knowledge_engine.initialize.call_count
        result2 = await service.initialize()
        assert result2 is True
        
        # 应该没有增加调用次数
        assert service.knowledge_engine.initialize.call_count == call_count_before


# ============================================================================
# 测试：超时控制
# ============================================================================

class TestContextServiceNewTimeout:
    """测试ContextServiceNew的超时控制"""
    
    @pytest.mark.asyncio
    async def test_safe_call_timeout(self, context_service_with_mocks):
        """测试：_safe_call超时处理"""
        service = context_service_with_mocks
        
        # 创建一个会超时的协程
        async def slow_operation():
            await asyncio.sleep(1.0)  # 超过超时时间
            return "result"
        
        # 使用较短的超时时间
        result = await service._safe_call(slow_operation(), timeout=0.1)
        
        # 应该返回None（超时）
        assert result is None
    
    @pytest.mark.asyncio
    async def test_safe_call_success(self, context_service_with_mocks):
        """测试：_safe_call成功执行"""
        service = context_service_with_mocks
        
        # 创建一个快速完成的协程
        async def fast_operation():
            await asyncio.sleep(0.01)
            return "success"
        
        result = await service._safe_call(fast_operation(), timeout=0.5)
        
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_safe_call_exception(self, context_service_with_mocks):
        """测试：_safe_call异常处理"""
        service = context_service_with_mocks
        
        # 创建一个会抛出异常的协程
        async def failing_operation():
            raise ValueError("Test error")
        
        result = await service._safe_call(failing_operation(), timeout=0.5)
        
        # 应该返回None（异常被捕获）
        assert result is None
    
    @pytest.mark.asyncio
    async def test_build_context_with_timeout(self, context_service_with_mocks):
        """测试：构建上下文时引擎超时"""
        service = context_service_with_mocks
        await service.initialize()
        
        # 设置引擎方法超时
        async def slow_search():
            await asyncio.sleep(1.0)
            return []
        
        service.knowledge_engine.search_knowledge = slow_search
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        context = await service.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query="测试查询",
            dataset_names=["test_dataset"]
        )
        
        # 即使超时，也应该返回有效的上下文结构
        assert isinstance(context, dict)
        assert "intent" in context
        assert "knowledge" in context
        assert "profile" in context
        assert "memories" in context


# ============================================================================
# 测试：降级策略
# ============================================================================

class TestContextServiceNewFallback:
    """测试ContextServiceNew的降级策略"""
    
    @pytest.mark.asyncio
    async def test_build_context_knowledge_failed(self, context_service_with_mocks):
        """测试：Knowledge引擎失败时的降级"""
        service = context_service_with_mocks
        await service.initialize()
        
        # 设置Knowledge引擎失败
        service.knowledge_engine.search_knowledge = AsyncMock(side_effect=Exception("Knowledge error"))
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        context = await service.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query="什么是Python？",
            dataset_names=["test_dataset"]
        )
        
        # 即使Knowledge失败，其他引擎应该正常工作
        assert isinstance(context, dict)
        assert context["knowledge"] == []  # 失败时返回空列表
        assert "profile" in context
        assert "memories" in context
    
    @pytest.mark.asyncio
    async def test_build_context_userprofile_failed(self, context_service_with_mocks):
        """测试：UserProfile引擎失败时的降级"""
        service = context_service_with_mocks
        await service.initialize()
        
        # 设置UserProfile引擎失败
        service.userprofile_engine.get_profile = AsyncMock(side_effect=Exception("Profile error"))
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        context = await service.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query="你好"
        )
        
        # 即使UserProfile失败，其他引擎应该正常工作
        assert isinstance(context, dict)
        assert "knowledge" in context
        assert context["profile"]["profile_text"] == ""  # 失败时返回空
        assert "memories" in context
    
    @pytest.mark.asyncio
    async def test_build_context_chatmemory_failed(self, context_service_with_mocks):
        """测试：ChatMemory引擎失败时的降级"""
        service = context_service_with_mocks
        await service.initialize()
        
        # 设置ChatMemory引擎失败
        service.chatmemory_engine.search_memories = AsyncMock(side_effect=Exception("Memory error"))
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        context = await service.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query="你好"
        )
        
        # 即使ChatMemory失败，其他引擎应该正常工作
        assert isinstance(context, dict)
        assert "knowledge" in context
        assert "profile" in context
        assert context["memories"] == []  # 失败时返回空列表
    
    @pytest.mark.asyncio
    async def test_build_context_all_engines_failed(self, context_service_with_mocks):
        """测试：所有引擎失败时的降级"""
        service = context_service_with_mocks
        await service.initialize()
        
        # 设置所有引擎失败
        service.knowledge_engine.search_knowledge = AsyncMock(side_effect=Exception("Error"))
        service.userprofile_engine.get_profile = AsyncMock(side_effect=Exception("Error"))
        service.chatmemory_engine.search_memories = AsyncMock(side_effect=Exception("Error"))
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        context = await service.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query="测试"
        )
        
        # 即使所有引擎失败，也应该返回有效的上下文结构
        assert isinstance(context, dict)
        assert "intent" in context
        assert context["knowledge"] == []
        assert context["profile"]["profile_text"] == ""
        assert context["memories"] == []


# ============================================================================
# 测试：意图场景
# ============================================================================

class TestContextServiceNewIntentScenarios:
    """测试ContextServiceNew的各种意图场景"""
    
    @pytest.mark.asyncio
    async def test_chitchat_intent(self, context_service_with_mocks):
        """测试：闲聊意图（CHITCHAT）"""
        service = context_service_with_mocks
        await service.initialize()
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        context = await service.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query="你好"
        )
        
        assert context["intent"] == QueryIntent.CHITCHAT.value
        # 闲聊意图：knowledge禁用，userprofile和chatmemory启用
        assert len(context["knowledge"]) == 0
        assert "profile" in context
        assert len(context["memories"]) > 0
    
    @pytest.mark.asyncio
    async def test_knowledge_query_intent(self, context_service_with_mocks):
        """测试：知识查询意图（KNOWLEDGE_QUERY）"""
        service = context_service_with_mocks
        await service.initialize()
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        context = await service.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query="什么是Python？",
            dataset_names=["test_dataset"]
        )
        
        assert context["intent"] == QueryIntent.KNOWLEDGE_QUERY.value
        # 知识查询意图：所有引擎启用
        assert len(context["knowledge"]) > 0
        assert "profile" in context
        assert len(context["memories"]) > 0
    
    @pytest.mark.asyncio
    async def test_task_execution_intent(self, context_service_with_mocks):
        """测试：任务执行意图（TASK_EXECUTION）"""
        service = context_service_with_mocks
        await service.initialize()
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        context = await service.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query="帮我写一个Python函数",
            dataset_names=["test_dataset"]
        )
        
        assert context["intent"] == QueryIntent.TASK_EXECUTION.value
        # 任务执行意图：所有引擎启用
        assert len(context["knowledge"]) > 0
        assert "profile" in context
        assert len(context["memories"]) > 0
    
    @pytest.mark.asyncio
    async def test_emotional_support_intent(self, context_service_with_mocks):
        """测试：情感支持意图（EMOTIONAL_SUPPORT）"""
        service = context_service_with_mocks
        await service.initialize()
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        context = await service.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query="我很难过"
        )
        
        assert context["intent"] == QueryIntent.EMOTIONAL_SUPPORT.value
        # 情感支持意图：knowledge禁用，userprofile和chatmemory启用
        assert len(context["knowledge"]) == 0
        assert "profile" in context
        assert len(context["memories"]) > 0
    
    @pytest.mark.asyncio
    async def test_learning_intent(self, context_service_with_mocks):
        """测试：学习辅导意图（LEARNING）"""
        service = context_service_with_mocks
        await service.initialize()
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        context = await service.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query="学习Python编程",
            dataset_names=["test_dataset"]
        )
        
        assert context["intent"] == QueryIntent.LEARNING.value
        # 学习意图：所有引擎启用
        assert len(context["knowledge"]) > 0
        assert "profile" in context
        assert len(context["memories"]) > 0
    
    @pytest.mark.asyncio
    async def test_intent_engine_config(self, context_service_with_mocks):
        """测试：不同意图的引擎配置"""
        service = context_service_with_mocks
        await service.initialize()
        
        test_cases = [
            ("你好", QueryIntent.CHITCHAT, {"knowledge": False, "userprofile": True, "chatmemory": True}),
            ("什么是Python？", QueryIntent.KNOWLEDGE_QUERY, {"knowledge": True, "userprofile": True, "chatmemory": True}),
            ("帮我计算", QueryIntent.TASK_EXECUTION, {"knowledge": True, "userprofile": True, "chatmemory": True}),
            ("我很难过", QueryIntent.EMOTIONAL_SUPPORT, {"knowledge": False, "userprofile": True, "chatmemory": True}),
            ("学习Python", QueryIntent.LEARNING, {"knowledge": True, "userprofile": True, "chatmemory": True}),
        ]
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        for query, expected_intent, expected_config in test_cases:
            # 重置Mock
            service.knowledge_engine.search_knowledge.reset_mock()
            service.userprofile_engine.get_profile.reset_mock()
            service.chatmemory_engine.search_memories.reset_mock()
            
            context = await service.build_personalized_context(
                user_id=user_id,
                session_id=session_id,
                query=query,
                dataset_names=["test_dataset"] if expected_config["knowledge"] else None
            )
            
            assert context["intent"] == expected_intent.value
            
            # 验证引擎调用情况
            if expected_config["knowledge"]:
                service.knowledge_engine.search_knowledge.assert_called_once()
            else:
                service.knowledge_engine.search_knowledge.assert_not_called()
            
            if expected_config["userprofile"]:
                service.userprofile_engine.get_profile.assert_called_once()
            else:
                service.userprofile_engine.get_profile.assert_not_called()
            
            if expected_config["chatmemory"]:
                service.chatmemory_engine.search_memories.assert_called_once()
            else:
                service.chatmemory_engine.search_memories.assert_not_called()


# ============================================================================
# 测试：build_personalized_context方法
# ============================================================================

class TestContextServiceNewBuildContext:
    """测试ContextServiceNew的build_personalized_context方法"""
    
    @pytest.mark.asyncio
    async def test_build_context_all_engines_success(self, context_service_with_mocks):
        """测试：所有引擎成功返回结果"""
        service = context_service_with_mocks
        await service.initialize()
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        context = await service.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query="什么是Python？",
            dataset_names=["test_dataset"]
        )
        
        # 验证返回结构
        assert isinstance(context, dict)
        assert "intent" in context
        assert "knowledge" in context
        assert "profile" in context
        assert "memories" in context
        
        # 验证数据内容
        assert len(context["knowledge"]) > 0
        assert context["profile"]["profile_text"] != ""
        assert len(context["memories"]) > 0
    
    @pytest.mark.asyncio
    async def test_build_context_user_id_normalization(self, context_service_with_mocks, db_session):
        """测试：用户ID标准化"""
        service = context_service_with_mocks
        await service.initialize()
        
        # Mock UserIDNormalizer
        with patch('app.services.context.context_service_new.UserIDNormalizer.normalize_user_id') as mock_normalize:
            mock_normalize.return_value = "normalized_user_id"
            
            user_id = "test_user"
            session_id = str(uuid.uuid4())
            
            context = await service.build_personalized_context(
                user_id=user_id,
                session_id=session_id,
                query="测试",
                db_session=db_session
            )
            
            # 验证标准化被调用
            mock_normalize.assert_called_once_with(user_id, db_session)
    
    @pytest.mark.asyncio
    async def test_build_context_without_dataset_names(self, context_service_with_mocks):
        """测试：不提供dataset_names时Knowledge引擎不调用"""
        service = context_service_with_mocks
        await service.initialize()
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        # 不提供dataset_names
        context = await service.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query="你好"
        )
        
        # Knowledge引擎不应该被调用（因为没有dataset_names）
        service.knowledge_engine.search_knowledge.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_build_context_parallel_execution(self, context_service_with_mocks):
        """测试：引擎并行执行"""
        service = context_service_with_mocks
        await service.initialize()
        
        # 记录调用时间
        call_times = {}
        
        async def track_time(engine_name, original_func):
            call_times[engine_name] = time.time()
            return await original_func()
        
        # 包装引擎方法以记录时间
        original_knowledge = service.knowledge_engine.search_knowledge
        original_profile = service.userprofile_engine.get_profile
        original_memory = service.chatmemory_engine.search_memories
        
        service.knowledge_engine.search_knowledge = AsyncMock(
            side_effect=lambda *args, **kwargs: track_time("knowledge", lambda: original_knowledge(*args, **kwargs))
        )
        service.userprofile_engine.get_profile = AsyncMock(
            side_effect=lambda *args, **kwargs: track_time("userprofile", lambda: original_profile(*args, **kwargs))
        )
        service.chatmemory_engine.search_memories = AsyncMock(
            side_effect=lambda *args, **kwargs: track_time("chatmemory", lambda: original_memory(*args, **kwargs))
        )
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        context = await service.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query="什么是Python？",
            dataset_names=["test_dataset"]
        )
        
        # 验证所有引擎都被调用
        assert len(call_times) == 3
        
        # 验证时间差很小（说明是并行执行的）
        max_time = max(call_times.values())
        min_time = min(call_times.values())
        time_diff = max_time - min_time
        
        # 并行执行时，时间差应该很小（小于0.1秒）
        assert time_diff < 0.1


# ============================================================================
# 测试：update_user_data方法
# ============================================================================

class TestContextServiceNewUpdateUserData:
    """测试ContextServiceNew的update_user_data方法"""
    
    @pytest.mark.asyncio
    async def test_update_user_data_success(self, context_service_with_mocks):
        """测试：更新用户数据成功"""
        service = context_service_with_mocks
        await service.initialize()
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}
        ]
        
        result = await service.update_user_data(
            user_id=user_id,
            session_id=session_id,
            messages=messages
        )
        
        assert isinstance(result, dict)
        assert result["userprofile_updated"] is True
        assert result["chatmemory_updated"] is True
        
        # 验证引擎方法被调用
        service.userprofile_engine.update_profile.assert_called_once_with(user_id, messages)
        service.chatmemory_engine.add_memory.assert_called_once_with(user_id, session_id, messages)
    
    @pytest.mark.asyncio
    async def test_update_user_data_userprofile_failed(self, context_service_with_mocks):
        """测试：UserProfile更新失败"""
        service = context_service_with_mocks
        await service.initialize()
        
        # 设置UserProfile更新失败
        service.userprofile_engine.update_profile = AsyncMock(return_value=False)
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        messages = [{"role": "user", "content": "测试"}]
        
        result = await service.update_user_data(
            user_id=user_id,
            session_id=session_id,
            messages=messages
        )
        
        assert result["userprofile_updated"] is False
        assert result["chatmemory_updated"] is True
    
    @pytest.mark.asyncio
    async def test_update_user_data_chatmemory_failed(self, context_service_with_mocks):
        """测试：ChatMemory更新失败"""
        service = context_service_with_mocks
        await service.initialize()
        
        # 设置ChatMemory更新失败
        service.chatmemory_engine.add_memory = AsyncMock(side_effect=Exception("Memory error"))
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        messages = [{"role": "user", "content": "测试"}]
        
        result = await service.update_user_data(
            user_id=user_id,
            session_id=session_id,
            messages=messages
        )
        
        assert result["userprofile_updated"] is True
        assert result["chatmemory_updated"] is False
    
    @pytest.mark.asyncio
    async def test_update_user_data_timeout(self, context_service_with_mocks):
        """测试：更新用户数据超时"""
        service = context_service_with_mocks
        await service.initialize()
        
        # 设置超时操作
        async def slow_update(*args, **kwargs):
            await asyncio.sleep(2.0)
            return True
        
        service.userprofile_engine.update_profile = slow_update
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        messages = [{"role": "user", "content": "测试"}]
        
        result = await service.update_user_data(
            user_id=user_id,
            session_id=session_id,
            messages=messages
        )
        
        # 超时后应该返回False
        assert result["userprofile_updated"] is False


# ============================================================================
# 测试：build_context方法（兼容接口）
# ============================================================================

class TestContextServiceNewBuildContextCompatible:
    """测试ContextServiceNew的build_context方法（兼容旧接口）"""
    
    @pytest.mark.asyncio
    async def test_build_context_compatible(self, context_service_with_mocks):
        """测试：build_context兼容接口"""
        service = context_service_with_mocks
        await service.initialize()
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        personality_config = MagicMock()
        
        context_bundle = await service.build_context(
            user_id=user_id,
            session_id=session_id,
            current_message="测试消息",
            personality_config=personality_config,
            dataset_names=["test_dataset"]
        )
        
        # 验证返回ContextBundle
        assert isinstance(context_bundle, ContextBundle)
        assert context_bundle.memories is not None
        assert context_bundle.user_profile is not None
        assert "intent" in context_bundle.metadata


# ============================================================================
# 测试：health_check方法
# ============================================================================

class TestContextServiceNewHealthCheck:
    """测试ContextServiceNew的health_check方法"""
    
    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, context_service_with_mocks):
        """测试：所有引擎健康"""
        service = context_service_with_mocks
        await service.initialize()
        
        health = await service.health_check()
        
        assert isinstance(health, dict)
        assert health["knowledge"] is True
        assert health["userprofile"] is True
        assert health["chatmemory"] is True
        assert health["overall"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_partial_healthy(self, context_service_with_mocks):
        """测试：部分引擎健康"""
        service = context_service_with_mocks
        await service.initialize()
        
        # 设置部分引擎不健康
        service.knowledge_engine.health_check = AsyncMock(return_value=False)
        service.userprofile_engine.health_check = AsyncMock(return_value=True)
        service.chatmemory_engine.health_check = AsyncMock(return_value=True)
        
        health = await service.health_check()
        
        assert health["knowledge"] is False
        assert health["userprofile"] is True
        assert health["chatmemory"] is True
        assert health["overall"] is True  # 至少一个健康即可
    
    @pytest.mark.asyncio
    async def test_health_check_all_unhealthy(self, context_service_with_mocks):
        """测试：所有引擎不健康"""
        service = context_service_with_mocks
        await service.initialize()
        
        # 设置所有引擎不健康
        service.knowledge_engine.health_check = AsyncMock(return_value=False)
        service.userprofile_engine.health_check = AsyncMock(return_value=False)
        service.chatmemory_engine.health_check = AsyncMock(return_value=False)
        
        health = await service.health_check()
        
        assert health["knowledge"] is False
        assert health["userprofile"] is False
        assert health["chatmemory"] is False
        assert health["overall"] is False
    
    @pytest.mark.asyncio
    async def test_health_check_with_exception(self, context_service_with_mocks):
        """测试：健康检查时发生异常"""
        service = context_service_with_mocks
        await service.initialize()
        
        # 设置引擎抛出异常
        service.knowledge_engine.health_check = AsyncMock(side_effect=Exception("Health check error"))
        service.userprofile_engine.health_check = AsyncMock(return_value=True)
        service.chatmemory_engine.health_check = AsyncMock(return_value=True)
        
        health = await service.health_check()
        
        assert health["knowledge"] is False  # 异常被视为不健康
        assert health["userprofile"] is True
        assert health["chatmemory"] is True
        assert health["overall"] is True


# ============================================================================
# 测试：边界情况和错误处理
# ============================================================================

class TestContextServiceNewEdgeCases:
    """测试ContextServiceNew的边界情况和错误处理"""
    
    @pytest.mark.asyncio
    async def test_build_context_empty_query(self, context_service_with_mocks):
        """测试：空查询"""
        service = context_service_with_mocks
        await service.initialize()
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        context = await service.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query=""
        )
        
        # 空查询应该返回默认意图（CHITCHAT）
        assert context["intent"] == QueryIntent.CHITCHAT.value
    
    @pytest.mark.asyncio
    async def test_build_context_none_result(self, context_service_with_mocks):
        """测试：引擎返回None"""
        service = context_service_with_mocks
        await service.initialize()
        
        # 设置引擎返回None
        service.knowledge_engine.search_knowledge = AsyncMock(return_value=None)
        service.userprofile_engine.get_profile = AsyncMock(return_value=None)
        service.chatmemory_engine.search_memories = AsyncMock(return_value=None)
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        context = await service.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query="测试",
            dataset_names=["test_dataset"]
        )
        
        # 应该返回默认值
        assert context["knowledge"] == []
        assert context["profile"]["profile_text"] == ""
        assert context["memories"] == []
    
    @pytest.mark.asyncio
    async def test_build_context_empty_result(self, context_service_with_mocks):
        """测试：引擎返回空结果"""
        service = context_service_with_mocks
        await service.initialize()
        
        # 设置引擎返回空结果
        service.knowledge_engine.search_knowledge = AsyncMock(return_value=[])
        service.userprofile_engine.get_profile = AsyncMock(return_value={"user_id": "test", "profile_text": "", "token_size": 0})
        service.chatmemory_engine.search_memories = AsyncMock(return_value=[])
        
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        context = await service.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query="测试",
            dataset_names=["test_dataset"]
        )
        
        # 应该正常返回空结果
        assert context["knowledge"] == []
        assert context["profile"]["profile_text"] == ""
        assert context["memories"] == []
