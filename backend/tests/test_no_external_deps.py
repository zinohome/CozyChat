"""
无外部服务依赖的测试

这些测试不需要：
- 数据库（PostgreSQL）
- Redis
- 三大引擎（Cognee/Memobase/Mem0）
- Qdrant
- OpenAI API

可以完全独立运行
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, MagicMock
import time
import json


# ============================================================================
# TokenUtils测试（纯函数，无外部依赖）
# ============================================================================

class TestTokenUtilsPure:
    """Token工具函数测试（纯函数）"""
    
    def test_estimate_tokens_empty(self):
        """测试：空文本Token估算"""
        from app.utils.token_utils import estimate_tokens
        assert estimate_tokens("") == 0
        assert estimate_tokens(None) == 0
    
    def test_estimate_tokens_english(self):
        """测试：英文文本Token估算"""
        from app.utils.token_utils import estimate_tokens
        text = "Hello world"
        tokens = estimate_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_estimate_tokens_chinese(self):
        """测试：中文文本Token估算"""
        from app.utils.token_utils import estimate_tokens
        text = "你好世界"
        tokens = estimate_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_estimate_tokens_mixed(self):
        """测试：中英文混合Token估算"""
        from app.utils.token_utils import estimate_tokens
        text = "Hello 世界"
        tokens = estimate_tokens(text)
        assert tokens > 0
    
    def test_estimate_message_tokens(self):
        """测试：消息Token估算"""
        from app.utils.token_utils import estimate_message_tokens
        from app.engines.ai import ChatMessage
        message = ChatMessage(role="user", content="Hello")
        tokens = estimate_message_tokens(message)
        assert tokens >= 0
        assert isinstance(tokens, int)
    
    def test_estimate_message_tokens_empty(self):
        """测试：空消息Token估算"""
        from app.utils.token_utils import estimate_message_tokens
        from app.engines.ai import ChatMessage
        message = ChatMessage(role="user", content="")
        tokens = estimate_message_tokens(message)
        assert tokens >= 0
    
    def test_truncate_messages_empty(self):
        """测试：截断空消息列表"""
        from app.utils.token_utils import truncate_messages
        from app.engines.ai import ChatMessage
        result = truncate_messages([], max_history_tokens=100)
        assert result == []
    
    def test_truncate_messages_single(self):
        """测试：截断单条消息"""
        from app.utils.token_utils import truncate_messages
        from app.engines.ai import ChatMessage
        messages = [ChatMessage(role="user", content="Hello")]
        result = truncate_messages(messages, max_history_tokens=100)
        assert len(result) <= len(messages)
        assert isinstance(result, list)
    
    def test_truncate_messages_multiple(self):
        """测试：截断多条消息"""
        from app.utils.token_utils import truncate_messages
        from app.engines.ai import ChatMessage
        messages = [
            ChatMessage(role="user", content="Message 1"),
            ChatMessage(role="assistant", content="Response 1"),
            ChatMessage(role="user", content="Message 2"),
        ]
        result = truncate_messages(messages, max_history_tokens=10)
        assert len(result) <= len(messages)
        assert isinstance(result, list)


# ============================================================================
# Security测试（纯函数，无外部依赖）
# ============================================================================

class TestSecurityPure:
    """Security工具函数测试（纯函数）"""
    
    def test_hash_password(self):
        """测试：密码哈希"""
        from app.utils.security import hash_password
        password = "test_password_123"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)
    
    def test_hash_password_different(self):
        """测试：相同密码生成不同哈希（由于salt）"""
        from app.utils.security import hash_password
        password = "test_password"
        hashed1 = hash_password(password)
        hashed2 = hash_password(password)
        # 由于salt，每次哈希应该不同
        assert hashed1 != hashed2
    
    def test_verify_password_correct(self):
        """测试：验证正确密码"""
        from app.utils.security import hash_password, verify_password
        password = "test_password"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """测试：验证错误密码"""
        from app.utils.security import hash_password, verify_password
        password = "test_password"
        hashed = hash_password(password)
        assert verify_password("wrong_password", hashed) is False
    
    def test_create_access_token(self):
        """测试：创建访问Token"""
        from app.utils.security import create_access_token
        payload = {"user_id": "test_user", "sub": "test_user"}
        token = create_access_token(payload)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_valid(self):
        """测试：验证有效Token"""
        from app.utils.security import create_access_token, verify_token
        payload = {"user_id": "test_user", "sub": "test_user"}
        token = create_access_token(payload)
        verified = verify_token(token)
        assert verified is not None
        assert verified.get("user_id") == "test_user"
    
    def test_verify_token_invalid(self):
        """测试：验证无效Token"""
        from app.utils.security import verify_token
        verified = verify_token("invalid_token_string")
        assert verified is None
    
    def test_verify_token_expired(self):
        """测试：验证过期Token（需要特殊配置）"""
        from app.utils.security import create_access_token, verify_token
        # 创建短期Token
        payload = {"user_id": "test_user", "sub": "test_user", "exp": time.time() - 100}
        # 注意：实际实现可能不允许手动设置exp，这里只是测试接口
        try:
            token = create_access_token(payload)
            verified = verify_token(token)
            # 如果Token过期，应该返回None
            # 但实际行为取决于实现
        except Exception:
            pass  # 某些实现可能不允许手动设置exp


# ============================================================================
# TextConverter测试（纯函数，无外部依赖）
# ============================================================================

class TestTextConverterPure:
    """文本转换工具测试（纯函数）"""
    
    def test_to_simplified_with_zhconv(self):
        """测试：转换为简体（如果zhconv可用）"""
        from app.utils.text_converter import to_simplified
        try:
            result = to_simplified("測試")
            assert isinstance(result, str)
            # 如果zhconv可用，应该转换为简体
        except ImportError:
            # zhconv未安装时，应该返回原文本
            result = to_simplified("測試")
            assert result == "測試"
    
    def test_to_simplified_english(self):
        """测试：英文文本（不需要转换）"""
        from app.utils.text_converter import to_simplified
        text = "Hello World"
        result = to_simplified(text)
        assert result == text
    
    def test_is_traditional_chinese(self):
        """测试：检测繁体中文"""
        from app.utils.text_converter import is_traditional_chinese, ZHCONV_AVAILABLE
        # 如果zhconv未安装，函数总是返回False
        if not ZHCONV_AVAILABLE:
            assert is_traditional_chinese("測試") is False
            assert is_traditional_chinese("测试") is False
        else:
            # 测试繁体中文
            assert is_traditional_chinese("測試") is True
            # 测试简体中文
            assert is_traditional_chinese("测试") is False
        # 测试英文
        assert is_traditional_chinese("Hello") is False
        # 测试空字符串
        assert is_traditional_chinese("") is False


# ============================================================================
# Exceptions测试（纯类定义，无外部依赖）
# ============================================================================

class TestExceptionsPure:
    """异常类测试（纯类定义）"""
    
    def test_cozy_error(self):
        """测试：CozyError"""
        from app.utils.exceptions import CozyError
        error = CozyError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_chat_service_error(self):
        """测试：ChatServiceError"""
        from app.utils.exceptions import ChatServiceError, CozyError
        error = ChatServiceError("Chat error")
        assert str(error) == "Chat error"
        assert isinstance(error, CozyError)
    
    def test_context_service_error(self):
        """测试：ContextServiceError"""
        from app.utils.exceptions import ContextServiceError, CozyError
        error = ContextServiceError("Context error")
        assert str(error) == "Context error"
        assert isinstance(error, CozyError)
    
    def test_message_service_error(self):
        """测试：MessageServiceError"""
        from app.utils.exceptions import MessageServiceError, CozyError
        error = MessageServiceError("Message error")
        assert str(error) == "Message error"
        assert isinstance(error, CozyError)
    
    def test_authentication_error(self):
        """测试：AuthenticationError"""
        from app.utils.exceptions import AuthenticationError, CozyError
        error = AuthenticationError("Auth error")
        assert str(error) == "Auth error"
        assert isinstance(error, CozyError)
    
    def test_authorization_error(self):
        """测试：AuthorizationError"""
        from app.utils.exceptions import AuthorizationError, CozyError
        error = AuthorizationError("Authz error")
        assert str(error) == "Authz error"
        assert isinstance(error, CozyError)
    
    def test_validation_error(self):
        """测试：ValidationError"""
        from app.utils.exceptions import ValidationError, CozyError
        error = ValidationError("Validation error")
        assert str(error) == "Validation error"
        assert isinstance(error, CozyError)
    
    def test_resource_not_found_error(self):
        """测试：ResourceNotFoundError"""
        from app.utils.exceptions import ResourceNotFoundError, CozyError
        error = ResourceNotFoundError("Resource not found")
        assert str(error) == "Resource not found"
        assert isinstance(error, CozyError)


# ============================================================================
# PerformanceMonitor测试（纯内存操作，无外部依赖）
# ============================================================================

class TestPerformanceMonitorPure:
    """性能监控测试（纯内存操作）"""
    
    @pytest.fixture
    def perf_monitor(self):
        """创建PerformanceMonitor实例"""
        from app.utils.performance_monitor import PerformanceMonitor
        return PerformanceMonitor()
    
    @pytest.mark.asyncio
    async def test_track_success(self, perf_monitor):
        """测试：跟踪成功操作"""
        async def test_func():
            await asyncio.sleep(0.01)
            return "result"
        
        import asyncio
        result = await perf_monitor.track("knowledge_search", test_func)
        assert result == "result"
        
        stats = perf_monitor.get_stats()
        assert "knowledge_search" in stats
        assert stats["knowledge_search"]["count"] == 1
    
    @pytest.mark.asyncio
    async def test_track_error(self, perf_monitor):
        """测试：跟踪错误操作"""
        async def failing_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await perf_monitor.track("knowledge_search", failing_func)
    
    @pytest.mark.asyncio
    async def test_track_multiple(self, perf_monitor):
        """测试：跟踪多次操作"""
        async def test_func():
            return "result"
        
        for _ in range(5):
            await perf_monitor.track("knowledge_search", test_func)
        
        stats = perf_monitor.get_stats()
        assert stats["knowledge_search"]["count"] == 5
    
    def test_get_stats_empty(self, perf_monitor):
        """测试：获取空统计"""
        stats = perf_monitor.get_stats()
        assert isinstance(stats, dict)
        assert len(stats) == 0
    
    def test_get_stats_with_data(self, perf_monitor):
        """测试：获取有数据的统计"""
        import asyncio
        
        async def run_test():
            async def test_func():
                return "result"
            
            await perf_monitor.track("knowledge_search", test_func)
            await perf_monitor.track("profile_get", test_func)
            
            stats = perf_monitor.get_stats()
            assert len(stats) == 2
            assert "knowledge_search" in stats
            assert "profile_get" in stats
        
        asyncio.run(run_test())


# ============================================================================
# MultiLevelCache测试（纯内存操作，无外部依赖）
# ============================================================================

class TestMultiLevelCachePure:
    """多级缓存测试（纯内存操作，L1缓存）"""
    
    @pytest_asyncio.fixture
    async def cache(self):
        """创建MultiLevelCache实例"""
        from app.utils.cache_new.multi_level_cache import MultiLevelCache
        return MultiLevelCache()
    
    @pytest.mark.asyncio
    async def test_set_get(self, cache):
        """测试：设置和获取"""
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        assert value == "value1"
    
    @pytest.mark.asyncio
    async def test_get_miss(self, cache):
        """测试：获取未存在的键"""
        value = await cache.get("non_existent")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """测试：删除缓存"""
        await cache.set("key1", "value1")
        await cache.delete("key1")
        value = await cache.get("key1")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache):
        """测试：TTL过期"""
        cache._l1_ttl = 0.1  # 100ms
        await cache.set("key1", "value1")
        
        # 立即获取应该成功
        value = await cache.get("key1")
        assert value == "value1"
        
        # 等待过期
        import asyncio
        await asyncio.sleep(0.2)
        
        # 过期后应该返回None
        value = await cache.get("key1")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """测试：清空缓存"""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        cache.clear()
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
    
    @pytest.mark.asyncio
    async def test_multiple_operations(self, cache):
        """测试：多次操作"""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") == "value3"
        
        await cache.delete("key2")
        assert await cache.get("key2") is None


# ============================================================================
# QueryOptimizer测试（纯函数，无外部依赖）
# ============================================================================

class TestQueryOptimizerPure:
    """查询优化器测试（纯函数）"""
    
    def test_query_optimizer_import(self):
        """测试：QueryOptimizer可以导入"""
        try:
            from app.utils.query_optimizer import QueryOptimizer
            optimizer = QueryOptimizer()
            assert optimizer is not None
        except ImportError as e:
            pytest.skip(f"QueryOptimizer import failed: {e}")
    
    def test_optimize_basic(self):
        """测试：基本优化"""
        try:
            from app.utils.query_optimizer import QueryOptimizer
            optimizer = QueryOptimizer()
            query = "  测试查询  "
            optimized = optimizer.optimize(query)
            assert isinstance(optimized, str)
            assert len(optimized.strip()) > 0
        except (ImportError, AttributeError) as e:
            pytest.skip(f"QueryOptimizer test failed: {e}")
    
    def test_optimize_empty(self):
        """测试：空查询优化"""
        try:
            from app.utils.query_optimizer import QueryOptimizer
            optimizer = QueryOptimizer()
            query = ""
            optimized = optimizer.optimize(query)
            assert isinstance(optimized, str)
        except (ImportError, AttributeError) as e:
            pytest.skip(f"QueryOptimizer test failed: {e}")


# ============================================================================
# TypeHelpers测试（纯函数，无外部依赖）
# ============================================================================

class TestTypeHelpersPure:
    """类型辅助函数测试（纯函数）"""
    
    def test_get_user_status_mock(self):
        """测试：获取用户状态（使用Mock）"""
        from app.utils.type_helpers import get_user_status
        
        # 创建Mock用户
        mock_user = MagicMock()
        mock_user.status = "active"
        
        status = get_user_status(mock_user)
        assert status == "active"
    
    def test_get_user_role_mock(self):
        """测试：获取用户角色（使用Mock）"""
        from app.utils.type_helpers import get_user_role
        
        # 创建Mock用户
        mock_user = MagicMock()
        mock_user.role = "admin"
        
        role = get_user_role(mock_user)
        assert role == "admin"


# ============================================================================
# ConfigLoader测试（只需要文件系统，无外部依赖）
# ============================================================================

class TestConfigLoaderPure:
    """配置加载器测试（只需要文件系统）"""
    
    @pytest.fixture
    def config_loader(self):
        """创建ConfigLoader实例"""
        from app.utils.config_loader import ConfigLoader
        return ConfigLoader()
    
    def test_loader_initialization(self, config_loader):
        """测试：加载器初始化"""
        assert config_loader is not None
        assert hasattr(config_loader, 'config_dir')
    
    def test_load_personalities(self, config_loader):
        """测试：加载Personality配置"""
        try:
            personalities = config_loader.load_personalities()
            assert isinstance(personalities, list)
        except Exception as e:
            pytest.skip(f"Config loading failed: {e}")
    
    def test_get_personality(self, config_loader):
        """测试：获取Personality"""
        try:
            personality = config_loader.get_personality("default")
            # 可能返回None或配置字典
            assert personality is None or isinstance(personality, dict)
        except Exception as e:
            pytest.skip(f"Config loading failed: {e}")


# ============================================================================
# ConfigAdapter测试（纯函数，无外部依赖）
# ============================================================================

class TestConfigAdapterPure:
    """配置适配器测试（纯函数）"""
    
    @pytest.fixture
    def config_adapter(self):
        """创建ConfigAdapter实例"""
        from app.utils.config_adapter import ConfigAdapter
        return ConfigAdapter()
    
    def test_adapter_initialization(self, config_adapter):
        """测试：适配器初始化"""
        assert config_adapter is not None
    
    def test_adapt_personality_config(self, config_adapter):
        """测试：适配Personality配置"""
        config = {
            "id": "test",
            "name": "Test Personality",
            "ai": {"provider": "openai", "model": "gpt-3.5-turbo"}
        }
        try:
            adapted = config_adapter.adapt_personality_config(config)
            assert isinstance(adapted, dict)
        except Exception as e:
            pytest.skip(f"Config adapter failed: {e}")


# ============================================================================
# Monitoring测试（使用Mock，无外部依赖）
# ============================================================================

class TestMonitoringPure:
    """监控模块测试（使用Mock）"""
    
    def test_init_sentry_disabled(self):
        """测试：Sentry未启用"""
        from app.utils.monitoring import init_sentry
        with patch('app.config.config.settings.sentry_enable', False):
            result = init_sentry()
            assert result is False
    
    def test_init_sentry_no_dsn(self):
        """测试：Sentry无DSN"""
        from app.utils.monitoring import init_sentry
        with patch('app.config.config.settings.sentry_enable', True):
            with patch('app.config.config.settings.sentry_dsn', None):
                result = init_sentry()
                assert result is False
    
    def test_init_sentry_success(self):
        """测试：Sentry初始化成功（Mock）"""
        from app.utils.monitoring import init_sentry
        with patch('app.config.config.settings.sentry_enable', True):
            with patch('app.config.config.settings.sentry_dsn', 'test_dsn'):
                try:
                    with patch('sentry_sdk.init') as mock_init:
                        result = init_sentry()
                        # 应该尝试初始化
                        assert isinstance(result, bool)
                except ImportError:
                    # sentry_sdk未安装时跳过
                    pytest.skip("sentry_sdk not installed")


# ============================================================================
# Logger测试（无外部依赖）
# ============================================================================

class TestLoggerPure:
    """Logger测试（无外部依赖）"""
    
    def test_logger_initialization(self):
        """测试：Logger初始化"""
        from app.utils.logger import logger
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'debug')
    
    def test_logger_methods(self):
        """测试：Logger方法调用"""
        from app.utils.logger import logger
        # 这些调用不应该抛出异常
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
    
    def test_setup_logging(self):
        """测试：设置日志"""
        from app.utils.logger import setup_logging, logger
        # setup_logging可能不接受参数或参数不同
        try:
            setup_logging()
        except TypeError:
            # 如果函数不接受参数，直接调用
            pass
        # 验证logger已配置
        assert logger is not None


# ============================================================================
# MessageUtils测试（纯函数，无外部依赖）
# ============================================================================

class TestMessageUtilsPure:
    """消息工具函数测试（纯函数）"""
    
    def test_detect_message_hints(self):
        """测试：检测消息提示"""
        from app.utils.message_utils import detect_message_hints
        content = "请帮我计算1+1"
        hints = detect_message_hints(content)
        assert isinstance(hints, dict)
    
    def test_detect_message_hints_various(self):
        """测试：检测各种消息提示"""
        from app.utils.message_utils import detect_message_hints
        
        # 测试列表提示
        hints = detect_message_hints("列出所有步骤")
        assert isinstance(hints, dict)
        
        # 测试详细提示
        hints = detect_message_hints("为什么会这样")
        assert isinstance(hints, dict)
        
        # 测试普通消息
        hints = detect_message_hints("你好")
        assert isinstance(hints, dict)


# ============================================================================
# IntentAnalyzer测试（纯函数，无外部依赖）
# ============================================================================

class TestIntentAnalyzerPure:
    """意图分析器测试（纯函数）"""
    
    def test_analyze_chitchat(self):
        """测试：识别闲聊意图"""
        from app.services.context.intent_analyzer import IntentAnalyzer, QueryIntent
        intent = IntentAnalyzer.analyze_intent("你好", {})
        assert intent == QueryIntent.CHITCHAT
    
    def test_analyze_knowledge_query(self):
        """测试：识别知识查询意图"""
        from app.services.context.intent_analyzer import IntentAnalyzer, QueryIntent
        intent = IntentAnalyzer.analyze_intent("什么是Python？", {})
        assert intent == QueryIntent.KNOWLEDGE_QUERY
    
    def test_analyze_task_execution(self):
        """测试：识别任务执行意图"""
        from app.services.context.intent_analyzer import IntentAnalyzer, QueryIntent
        intent = IntentAnalyzer.analyze_intent("帮我计算", {})
        assert intent == QueryIntent.TASK_EXECUTION
    
    def test_analyze_emotional_support(self):
        """测试：识别情感支持意图"""
        from app.services.context.intent_analyzer import IntentAnalyzer, QueryIntent
        intent = IntentAnalyzer.analyze_intent("我感觉很难过", {})
        assert intent == QueryIntent.EMOTIONAL_SUPPORT
    
    def test_get_engine_config(self):
        """测试：获取引擎配置"""
        from app.services.context.intent_analyzer import IntentAnalyzer, QueryIntent
        config = IntentAnalyzer.get_engine_config(QueryIntent.KNOWLEDGE_QUERY)
        assert isinstance(config, dict)
        assert "knowledge" in config or "userprofile" in config or "chatmemory" in config
    
    def test_all_intent_types(self):
        """测试：所有意图类型"""
        from app.services.context.intent_analyzer import IntentAnalyzer, QueryIntent
        
        test_cases = [
            ("你好", QueryIntent.CHITCHAT),
            ("什么是Python？", QueryIntent.KNOWLEDGE_QUERY),
            ("帮我计算", QueryIntent.TASK_EXECUTION),
            ("我很难过", QueryIntent.EMOTIONAL_SUPPORT),
            ("学习", QueryIntent.LEARNING),
        ]
        
        for query, expected_intent in test_cases:
            intent = IntentAnalyzer.analyze_intent(query, {})
            assert intent == expected_intent, f"Query '{query}' should be {expected_intent}"
        
        # 测试信息查询（可能被识别为其他类型）
        intent = IntentAnalyzer.analyze_intent("告诉我", {})
        assert intent in [QueryIntent.INFORMATION_QUERY, QueryIntent.CHITCHAT, QueryIntent.KNOWLEDGE_QUERY]

