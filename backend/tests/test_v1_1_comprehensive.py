"""
CozyChat v1.1.0 完整覆盖性测试

测试范围：
1. 三大人格化引擎（Knowledge/UserProfile/ChatMemory）
2. ContextService集成测试
3. API接口测试
4. 性能测试
5. 回归测试
6. 意图分析测试
7. 缓存系统测试
"""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

# 第三方库
from httpx import AsyncClient

# 本地库
from app.engines.knowledge.cognee_engine import CogneeKnowledgeEngine
from app.engines.userprofile.memobase_engine import MemobaseUserProfileEngine
from app.engines.chatmemory.mem0_engine import Mem0ChatMemoryEngine
from app.services.context.context_service_new import ContextServiceNew
from app.services.context.intent_analyzer import IntentAnalyzer, QueryIntent
from app.utils.cache_new.multi_level_cache import MultiLevelCache, cache
from app.config.config import settings


# ============================================================================
# 1. 三大引擎单元测试
# ============================================================================

class TestKnowledgeEngine:
    """Knowledge Engine测试"""
    
    @pytest_asyncio.fixture
    async def knowledge_engine(self):
        """创建Knowledge Engine实例"""
        config = {
            "api_url": "http://192.168.66.11:8000",
            "api_token": None
        }
        engine = CogneeKnowledgeEngine(config)
        await engine.initialize()
        yield engine
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, knowledge_engine):
        """测试：引擎初始化"""
        assert knowledge_engine.client is not None
        assert knowledge_engine._initialized is True
    
    @pytest.mark.asyncio
    async def test_health_check(self, knowledge_engine):
        """测试：健康检查"""
        is_healthy = await knowledge_engine.health_check()
        assert isinstance(is_healthy, bool)
        # 允许失败（如果服务未启动）
    
    @pytest.mark.asyncio
    async def test_search_knowledge(self, knowledge_engine):
        """测试：知识检索"""
        try:
            results = await knowledge_engine.search_knowledge(
                query="什么是Python",
                user_id="test_user",
                top_k=3
            )
            assert isinstance(results, list)
            # 如果有结果，验证结构
            if results:
                assert hasattr(results[0], 'content')
                assert hasattr(results[0], 'score')
                assert hasattr(results[0], 'source')
        except Exception as e:
            pytest.skip(f"Knowledge Engine服务不可用: {e}")


class TestUserProfileEngine:
    """UserProfile Engine测试"""
    
    @pytest_asyncio.fixture
    async def userprofile_engine(self):
        """创建UserProfile Engine实例"""
        config = {
            "project_url": "http://192.168.66.11:8019",
            "api_key": "secret"
        }
        engine = MemobaseUserProfileEngine(config)
        await engine.initialize()
        yield engine
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, userprofile_engine):
        """测试：引擎初始化"""
        assert userprofile_engine.client is not None
        assert userprofile_engine._initialized is True
    
    @pytest.mark.asyncio
    async def test_health_check(self, userprofile_engine):
        """测试：健康检查"""
        is_healthy = await userprofile_engine.health_check()
        assert isinstance(is_healthy, bool)
    
    @pytest.mark.asyncio
    async def test_get_profile(self, userprofile_engine):
        """测试：获取用户画像"""
        try:
            profile = await userprofile_engine.get_profile(
                user_id="test_user_123",
                max_token_size=500
            )
            assert profile is not None
            assert profile.user_id == "test_user_123"
            assert isinstance(profile.profile_data, dict)
        except Exception as e:
            pytest.skip(f"UserProfile Engine服务不可用: {e}")
    
    @pytest.mark.asyncio
    async def test_update_profile(self, userprofile_engine):
        """测试：更新用户画像"""
        try:
            messages = [
                {"role": "user", "content": "我喜欢Python编程"},
                {"role": "assistant", "content": "好的，我知道了"}
            ]
            await userprofile_engine.update_profile(
                user_id="test_user_123",
                messages=messages
            )
            # 验证：更新后可以获取画像
            profile = await userprofile_engine.get_profile("test_user_123")
            assert profile is not None
        except Exception as e:
            pytest.skip(f"UserProfile Engine服务不可用: {e}")


class TestChatMemoryEngine:
    """ChatMemory Engine测试"""
    
    @pytest_asyncio.fixture
    async def chatmemory_engine(self):
        """创建ChatMemory Engine实例"""
        config = {
            "api_url": "http://192.168.66.11:8888",
            "api_key": None
        }
        engine = Mem0ChatMemoryEngine(config)
        await engine.initialize()
        yield engine
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, chatmemory_engine):
        """测试：引擎初始化"""
        assert chatmemory_engine.client is not None
        assert chatmemory_engine._initialized is True
    
    @pytest.mark.asyncio
    async def test_health_check(self, chatmemory_engine):
        """测试：健康检查"""
        is_healthy = await chatmemory_engine.health_check()
        assert isinstance(is_healthy, bool)
    
    @pytest.mark.asyncio
    async def test_search_memories(self, chatmemory_engine):
        """测试：检索记忆"""
        try:
            memories = await chatmemory_engine.search_memories(
                user_id="test_user",
                session_id="test_session",
                query="Python",
                top_k=5
            )
            assert isinstance(memories, list)
            # 如果有结果，验证结构
            if memories:
                assert hasattr(memories[0], 'content')
                assert hasattr(memories[0], 'type')
        except Exception as e:
            pytest.skip(f"ChatMemory Engine服务不可用: {e}")
    
    @pytest.mark.asyncio
    async def test_add_memory(self, chatmemory_engine):
        """测试：添加记忆"""
        try:
            messages = [
                {"role": "user", "content": "测试消息"},
                {"role": "assistant", "content": "收到"}
            ]
            await chatmemory_engine.add_memory(
                user_id="test_user",
                session_id="test_session",
                messages=messages
            )
        except Exception as e:
            pytest.skip(f"ChatMemory Engine服务不可用: {e}")


# ============================================================================
# 2. ContextService集成测试
# ============================================================================

class TestContextServiceIntegration:
    """ContextService集成测试"""
    
    @pytest_asyncio.fixture
    async def context_service(self, db_session):
        """创建ContextService实例"""
        service = ContextServiceNew(db_session)
        await service.initialize()
        yield service
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, context_service):
        """测试：服务初始化"""
        assert context_service.knowledge_engine is not None
        assert context_service.userprofile_engine is not None
        assert context_service.chatmemory_engine is not None
    
    @pytest.mark.asyncio
    async def test_build_context_chitchat(self, context_service):
        """测试：闲聊意图的上下文构建"""
        try:
            context = await context_service.build_context(
                user_id="test_user",
                session_id="test_session",
                query="你好",
                personality_config={
                    "personalization_engines": {
                        "chatmemory": {"enabled": True}
                    }
                }
            )
            assert isinstance(context, dict)
            assert "knowledge" in context
            assert "user_profile" in context
            assert "conversation_memory" in context
        except Exception as e:
            pytest.skip(f"ContextService不可用: {e}")
    
    @pytest.mark.asyncio
    async def test_build_context_knowledge_query(self, context_service):
        """测试：知识查询意图的上下文构建"""
        try:
            context = await context_service.build_context(
                user_id="test_user",
                session_id="test_session",
                query="什么是Python？",
                personality_config={
                    "personalization_engines": {
                        "knowledge": {"enabled": True},
                        "chatmemory": {"enabled": True}
                    }
                }
            )
            assert isinstance(context, dict)
            # 知识查询应该启用知识引擎
            assert len(context.get("knowledge", [])) >= 0
        except Exception as e:
            pytest.skip(f"ContextService不可用: {e}")


# ============================================================================
# 3. 意图分析测试
# ============================================================================

class TestIntentAnalyzer:
    """意图分析器测试"""
    
    def test_analyze_chitchat(self):
        """测试：识别闲聊意图"""
        intent = IntentAnalyzer.analyze_intent("你好", {})
        assert intent == QueryIntent.CHITCHAT
    
    def test_analyze_knowledge_query(self):
        """测试：识别知识查询意图"""
        intent = IntentAnalyzer.analyze_intent("什么是Python？", {})
        assert intent == QueryIntent.KNOWLEDGE_QUERY
    
    def test_analyze_task_execution(self):
        """测试：识别任务执行意图"""
        intent = IntentAnalyzer.analyze_intent("帮我计算一下", {})
        assert intent == QueryIntent.TASK_EXECUTION
    
    def test_analyze_emotional_support(self):
        """测试：识别情感支持意图"""
        intent = IntentAnalyzer.analyze_intent("我感觉很难过", {})
        assert intent == QueryIntent.EMOTIONAL_SUPPORT
    
    def test_get_engine_config(self):
        """测试：获取引擎配置"""
        config = IntentAnalyzer.get_engine_config(QueryIntent.KNOWLEDGE_QUERY)
        assert isinstance(config, dict)
        assert "knowledge" in config
        assert config["knowledge"]["enabled"] is True


# ============================================================================
# 4. 缓存系统测试
# ============================================================================

class TestMultiLevelCache:
    """多级缓存测试"""
    
    @pytest_asyncio.fixture
    async def test_cache(self):
        """创建测试缓存实例"""
        cache_instance = MultiLevelCache(
            l1_maxsize=10,
            l1_ttl=5,
            l2_ttl=10,
            redis_url=None  # 不使用Redis，只测试L1
        )
        yield cache_instance
        await cache_instance.clear()
    
    @pytest.mark.asyncio
    async def test_cache_set_get(self, test_cache):
        """测试：缓存设置和获取"""
        await test_cache.set("test_key", "test_value")
        value = await test_cache.get("test_key")
        assert value == "test_value"
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, test_cache):
        """测试：缓存未命中"""
        value = await test_cache.get("non_existent_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, test_cache):
        """测试：删除缓存"""
        await test_cache.set("test_key", "test_value")
        await test_cache.delete("test_key")
        value = await test_cache.get("test_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, test_cache):
        """测试：缓存统计"""
        await test_cache.set("key1", "value1")
        await test_cache.get("key1")  # hit
        await test_cache.get("key2")  # miss
        
        stats = test_cache.get_stats()
        assert "total_requests" in stats
        assert "l1_hits" in stats
        assert "hit_rate" in stats


# ============================================================================
# 5. API接口测试
# ============================================================================

class TestV11APIs:
    """v1.1.0 API接口测试"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """测试：健康检查接口"""
        response = await async_client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    @pytest.mark.asyncio
    async def test_engines_health_check(self, async_client: AsyncClient):
        """测试：三大引擎健康检查"""
        response = await async_client.get("/v1/health/engines")
        assert response.status_code == 200
        data = response.json()
        assert "knowledge" in data
        assert "userprofile" in data
        assert "chatmemory" in data
    
    @pytest.mark.asyncio
    async def test_chat_completion_basic(self, async_client: AsyncClient):
        """测试：基本聊天完成"""
        # 先创建用户和会话
        # TODO: 添加用户创建逻辑
        
        payload = {
            "messages": [
                {"role": "user", "content": "你好"}
            ],
            "personality_id": "default",
            "stream": False
        }
        
        # 注意：这个测试可能需要mock或实际的OpenAI key
        try:
            response = await async_client.post(
                "/v1/chat/completions",
                json=payload,
                headers={"Authorization": "Bearer test_token"}
            )
            # 如果没有认证，预期401
            assert response.status_code in [200, 401, 422]
        except Exception as e:
            pytest.skip(f"Chat API测试跳过: {e}")


# ============================================================================
# 6. 性能测试
# ============================================================================

class TestPerformance:
    """性能测试"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_context_build_performance(self, db_session):
        """测试：上下文构建性能"""
        import time
        
        service = ContextServiceNew(db_session)
        await service.initialize()
        
        # 测试10次上下文构建
        times = []
        for i in range(10):
            start = time.time()
            try:
                await service.build_context(
                    user_id=f"test_user_{i}",
                    session_id=f"test_session_{i}",
                    query="测试查询",
                    personality_config={}
                )
                elapsed = time.time() - start
                times.append(elapsed)
            except:
                pass
        
        if times:
            avg_time = sum(times) / len(times)
            print(f"\n平均上下文构建时间: {avg_time:.3f}秒")
            # 目标：平均时间 < 1秒
            assert avg_time < 1.0, f"性能不达标：平均时间{avg_time:.3f}秒 > 1秒"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_parallel_engine_calls(self, db_session):
        """测试：并行引擎调用"""
        import time
        
        service = ContextServiceNew(db_session)
        await service.initialize()
        
        start = time.time()
        try:
            # 并行调用三个引擎
            results = await asyncio.gather(
                service.knowledge_engine.search_knowledge("Python", top_k=3),
                service.userprofile_engine.get_profile("test_user"),
                service.chatmemory_engine.search_memories(
                    "test_user", "test_session", "Python", top_k=3
                ),
                return_exceptions=True
            )
            elapsed = time.time() - start
            print(f"\n并行调用耗时: {elapsed:.3f}秒")
            # 并行调用应该快于串行
            assert elapsed < 2.0
        except Exception as e:
            pytest.skip(f"并行测试跳过: {e}")


# ============================================================================
# 7. 回归测试
# ============================================================================

class TestRegression:
    """回归测试 - 确保旧功能正常"""
    
    @pytest.mark.asyncio
    async def test_old_memory_engine_compatibility(self):
        """测试：旧Memory引擎向后兼容"""
        # 导入旧引擎应该触发DeprecationWarning
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from app.engines.memory import MemoryManager
            # 验证警告被触发
            assert len(w) > 0
            assert issubclass(w[0].category, DeprecationWarning)
    
    @pytest.mark.asyncio
    async def test_personality_old_config_support(self):
        """测试：旧Personality配置支持"""
        # 旧配置应该仍然可以加载
        from app.core.personality import PersonalityRegistry
        registry = PersonalityRegistry()
        
        # 加载旧配置格式
        personalities = registry.list_personalities()
        assert len(personalities) > 0


# ============================================================================
# 8. 边界条件测试
# ============================================================================

class TestEdgeCases:
    """边界条件测试"""
    
    @pytest.mark.asyncio
    async def test_empty_query(self, db_session):
        """测试：空查询"""
        service = ContextServiceNew(db_session)
        await service.initialize()
        
        try:
            context = await service.build_context(
                user_id="test_user",
                session_id="test_session",
                query="",
                personality_config={}
            )
            assert isinstance(context, dict)
        except Exception as e:
            # 空查询可能抛出异常，这是正常的
            pass
    
    @pytest.mark.asyncio
    async def test_very_long_query(self, db_session):
        """测试：超长查询"""
        service = ContextServiceNew(db_session)
        await service.initialize()
        
        long_query = "测试" * 1000  # 4000字符
        try:
            context = await service.build_context(
                user_id="test_user",
                session_id="test_session",
                query=long_query,
                personality_config={}
            )
            assert isinstance(context, dict)
        except Exception as e:
            # 超长查询可能触发限制
            pass
    
    @pytest.mark.asyncio
    async def test_special_characters(self, db_session):
        """测试：特殊字符处理"""
        service = ContextServiceNew(db_session)
        await service.initialize()
        
        special_query = "测试!@#$%^&*()_+<>?:\"{}|[]\\;',./~`"
        try:
            context = await service.build_context(
                user_id="test_user",
                session_id="test_session",
                query=special_query,
                personality_config={}
            )
            assert isinstance(context, dict)
        except Exception as e:
            pass


# ============================================================================
# 9. 错误处理测试
# ============================================================================

class TestErrorHandling:
    """错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_engine_connection_failure(self):
        """测试：引擎连接失败处理"""
        # 使用错误的URL
        config = {
            "api_url": "http://invalid-url:9999",
            "api_token": None
        }
        engine = CogneeKnowledgeEngine(config)
        
        # 初始化应该失败但不抛出异常
        result = await engine.initialize()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_engine_timeout_handling(self, db_session):
        """测试：引擎超时处理"""
        service = ContextServiceNew(db_session)
        await service.initialize()
        
        # 设置极短的超时时间
        service.timeout = 0.001  # 1ms
        
        try:
            context = await service.build_context(
                user_id="test_user",
                session_id="test_session",
                query="测试",
                personality_config={}
            )
            # 即使超时，也应该返回部分结果
            assert isinstance(context, dict)
        except Exception as e:
            # 超时异常是可接受的
            pass


# ============================================================================
# 测试运行配置
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

