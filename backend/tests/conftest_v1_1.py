"""
v1.1.0 测试配置扩展

为三大人格化引擎提供Mock fixtures
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from typing import List, Dict, Any

# 三大引擎的Mock数据模型
from app.engines.knowledge.models import KnowledgeSearchResult
from app.engines.userprofile.models import UserProfile
from app.engines.chatmemory.models import ConversationMemory


# ============================================================================
# 三大引擎Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_cognee_client():
    """Mock Cognee客户端"""
    mock_client = AsyncMock()
    
    # Mock search方法
    mock_client.search = AsyncMock(return_value={
        "results": [
            {
                "text": "Python是一种高级编程语言",
                "score": 0.95,
                "metadata": {"source": "knowledge_base"}
            },
            {
                "text": "Python由Guido van Rossum创建",
                "score": 0.88,
                "metadata": {"source": "knowledge_base"}
            }
        ]
    })
    
    # Mock add方法
    mock_client.add = AsyncMock(return_value={"id": "test_id"})
    
    # Mock health check
    mock_client.health = AsyncMock(return_value={"status": "ok"})
    
    return mock_client


@pytest.fixture
def mock_memobase_client():
    """Mock Memobase客户端"""
    mock_client = MagicMock()
    
    # Mock get_memory方法
    mock_client.get_memory = Mock(return_value={
        "user_id": "test_user",
        "profile": {
            "interests": ["Python", "AI"],
            "preferences": {"language": "zh-CN"}
        },
        "token_size": 150
    })
    
    # Mock update_memory方法
    mock_client.update_memory = Mock(return_value={"success": True})
    
    # Mock create_user方法
    mock_client.create_user = Mock(return_value={"user_id": "test_user"})
    
    # Mock get_user方法
    mock_client.get_user = Mock(return_value={"user_id": "test_user"})
    
    return mock_client


@pytest.fixture
def mock_mem0_client():
    """Mock Mem0客户端"""
    mock_client = AsyncMock()
    
    # Mock search方法
    mock_client.search = AsyncMock(return_value={
        "memories": [
            {
                "memory": "用户喜欢Python编程",
                "user_id": "test_user",
                "agent_id": "test_session",
                "created_at": "2024-12-22T00:00:00Z"
            }
        ]
    })
    
    # Mock add方法
    mock_client.add = AsyncMock(return_value={"success": True})
    
    # Mock get_memories方法
    mock_client.get_memories = AsyncMock(return_value={
        "memories": []
    })
    
    return mock_client


@pytest_asyncio.fixture
async def mock_knowledge_engine(mock_cognee_client):
    """Mock Knowledge Engine"""
    with patch('app.engines.knowledge.cognee_engine.CogneeClient') as mock:
        mock.return_value = mock_cognee_client
        from app.engines.knowledge.cognee_engine import CogneeKnowledgeEngine
        
        config = {
            "api_url": "http://mock-cognee:8000",
            "api_token": "mock_token"
        }
        engine = CogneeKnowledgeEngine(config)
        engine.client = mock_cognee_client
        engine._initialized = True
        
        yield engine


@pytest_asyncio.fixture
async def mock_userprofile_engine(mock_memobase_client):
    """Mock UserProfile Engine"""
    with patch('app.engines.userprofile.memobase_engine.MemoBaseClient') as mock:
        mock.return_value = mock_memobase_client
        from app.engines.userprofile.memobase_engine import MemobaseUserProfileEngine
        
        config = {
            "project_url": "http://mock-memobase:8019",
            "api_key": "mock_key"
        }
        engine = MemobaseUserProfileEngine(config)
        engine.client = mock_memobase_client
        engine._initialized = True
        
        yield engine


@pytest_asyncio.fixture
async def mock_chatmemory_engine(mock_mem0_client):
    """Mock ChatMemory Engine"""
    with patch('app.engines.chatmemory.mem0_engine.AsyncMemoryClient') as mock:
        mock.return_value = mock_mem0_client
        from app.engines.chatmemory.mem0_engine import Mem0ChatMemoryEngine
        
        config = {
            "api_url": "http://mock-mem0:8888",
            "api_key": "mock_key"
        }
        engine = Mem0ChatMemoryEngine(config)
        engine.client = mock_mem0_client
        engine._initialized = True
        
        yield engine


@pytest_asyncio.fixture
async def mock_context_service(
    db_session,
    mock_knowledge_engine,
    mock_userprofile_engine,
    mock_chatmemory_engine
):
    """Mock ContextService with mocked engines"""
    from app.services.context.context_service_new import ContextServiceNew
    
    service = ContextServiceNew(db_session)
    service.knowledge_engine = mock_knowledge_engine
    service.userprofile_engine = mock_userprofile_engine
    service.chatmemory_engine = mock_chatmemory_engine
    service._initialized = True
    
    yield service


# ============================================================================
# 测试数据Fixtures
# ============================================================================

@pytest.fixture
def sample_knowledge_results():
    """示例知识检索结果"""
    return [
        KnowledgeSearchResult(
            content="Python是一种高级编程语言",
            score=0.95,
            source="knowledge_base",
            metadata={"category": "programming"}
        ),
        KnowledgeSearchResult(
            content="Python支持多种编程范式",
            score=0.88,
            source="knowledge_base",
            metadata={"category": "programming"}
        )
    ]


@pytest.fixture
def sample_user_profile():
    """示例用户画像"""
    return UserProfile(
        user_id="test_user",
        profile_data={
            "interests": ["Python", "AI", "Machine Learning"],
            "skill_level": "intermediate",
            "preferences": {
                "language": "zh-CN",
                "response_style": "detailed"
            }
        },
        token_size=200,
        last_updated="2024-12-22T00:00:00Z"
    )


@pytest.fixture
def sample_conversation_memories():
    """示例会话记忆"""
    return [
        ConversationMemory(
            content="用户喜欢Python编程",
            type="semantic",
            session_id="test_session",
            user_id="test_user",
            timestamp="2024-12-22T00:00:00Z",
            metadata={"importance": "high"}
        ),
        ConversationMemory(
            content="用户最近在学习FastAPI",
            type="episodic",
            session_id="test_session",
            user_id="test_user",
            timestamp="2024-12-22T01:00:00Z",
            metadata={"importance": "medium"}
        )
    ]


@pytest.fixture
def sample_personality_config_v11():
    """示例v1.1人格配置"""
    return {
        "id": "test_personality_v11",
        "name": "Test Personality v1.1",
        "version": "1.1.0",
        "personalization_engines": {
            "intent_analysis": {
                "enabled": True,
                "use_llm": False
            },
            "knowledge": {
                "enabled": True,
                "provider": "cognee",
                "config": {
                    "search_type": "CHUNKS",
                    "top_k": 5
                }
            },
            "userprofile": {
                "enabled": True,
                "provider": "memobase",
                "config": {
                    "max_token_size": 500,
                    "update_on_chat": True
                }
            },
            "chatmemory": {
                "enabled": True,
                "provider": "mem0",
                "config": {
                    "current_session_k": 10,
                    "cross_session_k": 5
                }
            },
            "performance": {
                "parallel_calls": True,
                "timeout_seconds": 5.0,
                "cache_enabled": True
            }
        }
    }


# ============================================================================
# 环境变量Mock
# ============================================================================

@pytest.fixture
def mock_three_engines_env(monkeypatch):
    """Mock三大引擎环境变量"""
    monkeypatch.setenv("KNOWLEDGE_ENGINE_PROVIDER", "cognee")
    monkeypatch.setenv("COGNEE_API_URL", "http://192.168.66.11:8000")
    monkeypatch.setenv("COGNEE_API_TOKEN", "")
    
    monkeypatch.setenv("USERPROFILE_ENGINE_PROVIDER", "memobase")
    monkeypatch.setenv("MEMOBASE_PROJECT_URL", "http://192.168.66.11:8019")
    monkeypatch.setenv("MEMOBASE_API_KEY", "secret")
    
    monkeypatch.setenv("CHATMEMORY_ENGINE_PROVIDER", "mem0")
    monkeypatch.setenv("MEM0_API_URL", "http://192.168.66.11:8888")
    monkeypatch.setenv("MEM0_API_KEY", "")


# ============================================================================
# 性能测试辅助
# ============================================================================

@pytest.fixture
def performance_tracker():
    """性能追踪器"""
    import time
    from collections import defaultdict
    
    class PerformanceTracker:
        def __init__(self):
            self.times = defaultdict(list)
        
        def track(self, operation: str):
            """上下文管理器，追踪操作时间"""
            class Timer:
                def __init__(self, tracker, op):
                    self.tracker = tracker
                    self.operation = op
                    self.start = None
                
                def __enter__(self):
                    self.start = time.time()
                    return self
                
                def __exit__(self, *args):
                    elapsed = time.time() - self.start
                    self.tracker.times[self.operation].append(elapsed)
            
            return Timer(self, operation)
        
        def get_stats(self, operation: str) -> Dict[str, float]:
            """获取操作统计"""
            times = self.times.get(operation, [])
            if not times:
                return {}
            
            return {
                "count": len(times),
                "total": sum(times),
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times)
            }
        
        def print_report(self):
            """打印性能报告"""
            print("\n" + "=" * 60)
            print("性能测试报告")
            print("=" * 60)
            
            for operation in sorted(self.times.keys()):
                stats = self.get_stats(operation)
                print(f"\n{operation}:")
                print(f"  次数: {stats['count']}")
                print(f"  总计: {stats['total']:.3f}s")
                print(f"  平均: {stats['avg']:.3f}s")
                print(f"  最小: {stats['min']:.3f}s")
                print(f"  最大: {stats['max']:.3f}s")
            
            print("\n" + "=" * 60)
    
    return PerformanceTracker()


# ============================================================================
# 测试标记
# ============================================================================

def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "engines: 测试三大引擎"
    )
    config.addinivalue_line(
        "markers", "context: 测试上下文服务"
    )
    config.addinivalue_line(
        "markers", "performance: 性能测试"
    )
    config.addinivalue_line(
        "markers", "regression: 回归测试"
    )
    config.addinivalue_line(
        "markers", "v11: v1.1.0特定测试"
    )

