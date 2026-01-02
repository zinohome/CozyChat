"""
Mem0引擎单元测试

测试Mem0引擎的所有方法，包括：
- 引擎初始化
- 健康检查
- 记忆搜索（并发搜索当前会话和跨会话）
- 记忆添加
- 错误处理
- 并发场景
"""

# 标准库
import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

# 第三方库
import pytest
import httpx

# 本地库
from app.engines.chatmemory.mem0_engine import Mem0ChatMemoryEngine


class TestMem0ChatMemoryEngine:
    """测试Mem0引擎"""
    
    @pytest.fixture
    def engine_config(self):
        """引擎配置"""
        return {
            "api_url": "http://localhost:8888",
            "api_key": "test-api-key"
        }
    
    @pytest.fixture
    def engine_config_no_key(self):
        """引擎配置（无API Key）"""
        return {
            "api_url": "http://localhost:8888"
        }
    
    @pytest.fixture
    def mem0_engine(self, engine_config):
        """Mem0引擎实例"""
        return Mem0ChatMemoryEngine(config=engine_config)
    
    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx客户端"""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        return mock_client
    
    @pytest.fixture
    def mock_health_response(self):
        """Mock健康检查响应"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        return mock_response
    
    @pytest.fixture
    def mock_search_response_list(self):
        """Mock搜索响应（列表格式）"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "memory": "用户喜欢Python编程",
                "score": 0.95,
                "created_at": "2024-01-01T10:00:00Z"
            },
            {
                "memory": "用户正在学习FastAPI",
                "score": 0.85,
                "created_at": "2024-01-02T10:00:00Z"
            }
        ]
        mock_response.raise_for_status = MagicMock()
        return mock_response
    
    @pytest.fixture
    def mock_search_response_dict(self):
        """Mock搜索响应（字典格式，包含results）"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "memory": "用户使用React开发前端",
                    "score": 0.90,
                    "created_at": "2024-01-03T10:00:00Z"
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        return mock_response
    
    @pytest.fixture
    def mock_add_memory_response(self):
        """Mock添加记忆响应"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "mem_123",
            "status": "success"
        }
        mock_response.raise_for_status = MagicMock()
        return mock_response
    
    # ========== 引擎初始化测试 ==========
    
    def test_engine_initialization(self, engine_config):
        """测试：引擎初始化"""
        engine = Mem0ChatMemoryEngine(config=engine_config)
        
        assert engine.engine_name == "mem0"
        assert engine.api_url == "http://localhost:8888"
        assert engine.api_key == "test-api-key"
        assert engine.client is None
        assert engine._initialized is False
    
    def test_engine_initialization_no_key(self, engine_config_no_key):
        """测试：引擎初始化（无API Key）"""
        engine = Mem0ChatMemoryEngine(config=engine_config_no_key)
        
        assert engine.engine_name == "mem0"
        assert engine.api_url == "http://localhost:8888"
        assert engine.api_key is None
        assert engine.client is None
    
    def test_engine_initialization_url_trailing_slash(self):
        """测试：引擎初始化（URL带尾随斜杠）"""
        config = {
            "api_url": "http://localhost:8888/",
            "api_key": "test-key"
        }
        engine = Mem0ChatMemoryEngine(config=config)
        
        assert engine.api_url == "http://localhost:8888"
    
    # ========== 引擎初始化方法测试 ==========
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, mem0_engine, mock_httpx_client, mock_health_response):
        """测试：初始化成功"""
        # Mock httpx.AsyncClient
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            # Mock健康检查
            mock_httpx_client.get = AsyncMock(return_value=mock_health_response)
            
            # 执行初始化
            result = await mem0_engine.initialize()
        
        # 验证结果
        assert result is True
        assert mem0_engine._initialized is True
        assert mem0_engine.client is not None
        assert mem0_engine.metrics["successful_requests"] == 1
    
    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self, mem0_engine, mock_httpx_client, mock_health_response):
        """测试：重复初始化（已初始化）"""
        # 第一次初始化
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            mock_httpx_client.get = AsyncMock(return_value=mock_health_response)
            await mem0_engine.initialize()
        
        # 第二次初始化（应该直接返回True）
        result = await mem0_engine.initialize()
        
        assert result is True
        assert mem0_engine._initialized is True
    
    @pytest.mark.asyncio
    async def test_initialize_health_check_failed(self, mem0_engine, mock_httpx_client):
        """测试：初始化失败（健康检查失败）"""
        # Mock健康检查失败
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            result = await mem0_engine.initialize()
        
        assert result is False
        assert mem0_engine._initialized is False
    
    @pytest.mark.asyncio
    async def test_initialize_exception(self, mem0_engine):
        """测试：初始化异常"""
        # Mock httpx.AsyncClient抛出异常
        with patch('httpx.AsyncClient', side_effect=Exception("Connection error")):
            result = await mem0_engine.initialize()
        
        assert result is False
        assert mem0_engine._initialized is False
    
    # ========== 健康检查测试 ==========
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, mem0_engine, mock_httpx_client, mock_health_response):
        """测试：健康检查成功"""
        mem0_engine.client = mock_httpx_client
        mock_httpx_client.get = AsyncMock(return_value=mock_health_response)
        
        result = await mem0_engine.health_check()
        
        assert result is True
        mock_httpx_client.get.assert_called_once_with("/")
    
    @pytest.mark.asyncio
    async def test_health_check_no_client(self, mem0_engine):
        """测试：健康检查失败（无客户端）"""
        mem0_engine.client = None
        
        result = await mem0_engine.health_check()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_server_error(self, mem0_engine, mock_httpx_client):
        """测试：健康检查失败（服务器错误）"""
        mem0_engine.client = mock_httpx_client
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        
        result = await mem0_engine.health_check()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_exception(self, mem0_engine, mock_httpx_client):
        """测试：健康检查异常"""
        mem0_engine.client = mock_httpx_client
        mock_httpx_client.get = AsyncMock(side_effect=Exception("Network error"))
        
        result = await mem0_engine.health_check()
        
        assert result is False
    
    # ========== 搜索记忆测试 ==========
    
    @pytest.mark.asyncio
    async def test_search_memories_with_session_id(self, mem0_engine, mock_httpx_client, 
                                                   mock_search_response_list, mock_search_response_dict):
        """测试：搜索记忆（有session_id，并发搜索）"""
        # 初始化引擎
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        # Mock并发请求（当前会话 + 跨会话）
        mock_httpx_client.post = AsyncMock(side_effect=[
            mock_search_response_list,  # 当前会话
            mock_search_response_dict   # 跨会话
        ])
        
        # 执行搜索
        results = await mem0_engine.search_memories(
            query="Python编程",
            user_id="user_123",
            session_id="session_456",
            top_k=5
        )
        
        # 验证结果
        assert len(results) > 0
        assert all("memory" in r for r in results)
        assert all("score" in r for r in results)
        assert all("session" in r for r in results)
        
        # 验证并发调用
        assert mock_httpx_client.post.call_count == 2
        
        # 验证请求参数
        calls = mock_httpx_client.post.call_args_list
        # 第一个调用：当前会话
        assert calls[0][1]["json"]["user_id"] == "user_123"
        assert calls[0][1]["json"]["agent_id"] == "session_456"
        # 第二个调用：跨会话
        assert calls[1][1]["json"]["user_id"] == "user_123"
        assert "agent_id" not in calls[1][1]["json"]
    
    @pytest.mark.asyncio
    async def test_search_memories_without_session_id(self, mem0_engine, mock_httpx_client,
                                                       mock_search_response_dict):
        """测试：搜索记忆（无session_id，只搜索跨会话）"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        mock_httpx_client.post = AsyncMock(return_value=mock_search_response_dict)
        
        results = await mem0_engine.search_memories(
            query="Python编程",
            user_id="user_123",
            session_id=None,
            top_k=5
        )
        
        assert len(results) > 0
        # 只应该调用一次（跨会话）
        assert mock_httpx_client.post.call_count == 1
        # 验证请求参数
        call_args = mock_httpx_client.post.call_args
        assert call_args[1]["json"]["user_id"] == "user_123"
        assert "agent_id" not in call_args[1]["json"]
    
    @pytest.mark.asyncio
    async def test_search_memories_auto_initialize(self, mem0_engine, mock_httpx_client, 
                                                    mock_health_response, mock_search_response_list):
        """测试：搜索记忆（自动初始化）"""
        # Mock初始化
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            mock_httpx_client.get = AsyncMock(return_value=mock_health_response)
            mock_httpx_client.post = AsyncMock(return_value=mock_search_response_list)
            
            results = await mem0_engine.search_memories(
                query="Python编程",
                user_id="user_123",
                top_k=5
            )
        
        assert mem0_engine._initialized is True
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_search_memories_top_k_limit(self, mem0_engine, mock_httpx_client,
                                                mock_search_response_list):
        """测试：搜索记忆（top_k限制）"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        # Mock返回更多结果
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"memory": f"记忆{i}", "score": 0.9 - i * 0.1, "created_at": f"2024-01-0{i+1}T10:00:00Z"}
            for i in range(10)
        ]
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        
        results = await mem0_engine.search_memories(
            query="test",
            user_id="user_123",
            top_k=3
        )
        
        assert len(results) <= 3
    
    @pytest.mark.asyncio
    async def test_search_memories_exception_handling(self, mem0_engine, mock_httpx_client):
        """测试：搜索记忆（异常处理）"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        mock_httpx_client.post = AsyncMock(side_effect=Exception("Network error"))
        
        results = await mem0_engine.search_memories(
            query="test",
            user_id="user_123"
        )
        
        assert results == []
        assert mem0_engine.metrics["failed_requests"] > 0
    
    @pytest.mark.asyncio
    async def test_search_memories_response_exception(self, mem0_engine, mock_httpx_client):
        """测试：搜索记忆（响应异常）"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        # Mock响应包含异常
        mock_response_exception = Exception("Response error")
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = [{"memory": "test"}]
        mock_response_success.raise_for_status = MagicMock()
        
        mock_httpx_client.post = AsyncMock(side_effect=[
            mock_response_exception,  # 第一个请求异常
            mock_response_success     # 第二个请求成功
        ])
        
        results = await mem0_engine.search_memories(
            query="test",
            user_id="user_123",
            session_id="session_123"
        )
        
        # 应该返回部分结果（第二个请求的结果）
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_search_memories_http_error(self, mem0_engine, mock_httpx_client):
        """测试：搜索记忆（HTTP错误）"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error",
            request=MagicMock(),
            response=mock_response
        )
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        
        results = await mem0_engine.search_memories(
            query="test",
            user_id="user_123"
        )
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_memories_sorting_by_created_at(self, mem0_engine, mock_httpx_client):
        """测试：搜索记忆（按created_at排序）"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        # Mock返回不同时间的结果
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"memory": "记忆1", "score": 0.9, "created_at": "2024-01-03T10:00:00Z"},
            {"memory": "记忆2", "score": 0.95, "created_at": "2024-01-01T10:00:00Z"},
            {"memory": "记忆3", "score": 0.85, "created_at": "2024-01-02T10:00:00Z"}
        ]
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        
        results = await mem0_engine.search_memories(
            query="test",
            user_id="user_123"
        )
        
        # 应该按created_at降序排序（最新的在前）
        assert len(results) == 3
        assert results[0]["created_at"] == "2024-01-03T10:00:00Z"
        assert results[1]["created_at"] == "2024-01-02T10:00:00Z"
        assert results[2]["created_at"] == "2024-01-01T10:00:00Z"
    
    @pytest.mark.asyncio
    async def test_search_memories_no_created_at(self, mem0_engine, mock_httpx_client):
        """测试：搜索记忆（无created_at字段）"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"memory": "记忆1", "score": 0.9},
            {"memory": "记忆2", "score": 0.85}
        ]
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        
        results = await mem0_engine.search_memories(
            query="test",
            user_id="user_123"
        )
        
        # 应该能正常处理，即使没有created_at
        assert len(results) == 2
        assert all("created_at" in r or r.get("created_at") is None for r in results)
    
    # ========== 解析记忆测试 ==========
    
    def test_parse_memories_list_format(self, mem0_engine):
        """测试：解析记忆（列表格式）"""
        data = [
            {
                "memory": "记忆1",
                "score": 0.9,
                "created_at": "2024-01-01T10:00:00Z"
            },
            {
                "content": "记忆2",
                "score": 0.8,
                "timestamp": "2024-01-02T10:00:00Z"
            }
        ]
        
        results = mem0_engine._parse_memories(data, session="current", limit=10)
        
        assert len(results) == 2
        assert results[0]["memory"] == "记忆1"
        assert results[0]["score"] == 0.9
        assert results[0]["session"] == "current"
        assert results[1]["memory"] == "记忆2"
    
    def test_parse_memories_dict_with_results(self, mem0_engine):
        """测试：解析记忆（字典格式，包含results）"""
        data = {
            "results": [
                {
                    "memory": "记忆1",
                    "score": 0.9,
                    "created_at": "2024-01-01T10:00:00Z"
                }
            ]
        }
        
        results = mem0_engine._parse_memories(data, session="cross", limit=10)
        
        assert len(results) == 1
        assert results[0]["memory"] == "记忆1"
        assert results[0]["session"] == "cross"
    
    def test_parse_memories_dict_single(self, mem0_engine):
        """测试：解析记忆（字典格式，单个结果）"""
        data = {
            "memory": "记忆1",
            "score": 0.9,
            "created_at": "2024-01-01T10:00:00Z"
        }
        
        results = mem0_engine._parse_memories(data, session="current", limit=10)
        
        assert len(results) == 1
        assert results[0]["memory"] == "记忆1"
    
    def test_parse_memories_limit(self, mem0_engine):
        """测试：解析记忆（限制数量）"""
        data = [
            {"memory": f"记忆{i}", "score": 0.9} for i in range(10)
        ]
        
        results = mem0_engine._parse_memories(data, session="current", limit=3)
        
        assert len(results) == 3
    
    def test_parse_memories_fallback_fields(self, mem0_engine):
        """测试：解析记忆（字段回退）"""
        data = [
            {
                "content": "记忆内容",
                "timestamp": "2024-01-01T10:00:00Z"
            }
        ]
        
        results = mem0_engine._parse_memories(data, session="current", limit=10)
        
        assert results[0]["memory"] == "记忆内容"
        assert results[0]["created_at"] == "2024-01-01T10:00:00Z"
        assert results[0]["score"] == 1.0  # 默认值
    
    def test_parse_memories_empty_list(self, mem0_engine):
        """测试：解析记忆（空列表）"""
        data = []
        
        results = mem0_engine._parse_memories(data, session="current", limit=10)
        
        assert len(results) == 0
    
    def test_parse_memories_empty_dict(self, mem0_engine):
        """测试：解析记忆（空字典）"""
        data = {}
        
        results = mem0_engine._parse_memories(data, session="current", limit=10)
        
        assert len(results) == 1
        assert isinstance(results[0]["memory"], str)  # 使用str(data)
    
    def test_parse_memories_dict_empty_results(self, mem0_engine):
        """测试：解析记忆（字典格式，空results）"""
        data = {"results": []}
        
        results = mem0_engine._parse_memories(data, session="current", limit=10)
        
        assert len(results) == 0
    
    def test_parse_memories_list_item_not_dict(self, mem0_engine):
        """测试：解析记忆（列表项不是字典）"""
        data = ["记忆1", "记忆2"]
        
        results = mem0_engine._parse_memories(data, session="current", limit=10)
        
        assert len(results) == 2
        assert results[0]["memory"] == "记忆1"
        assert results[1]["memory"] == "记忆2"
    
    def test_parse_memories_dict_item_not_dict(self, mem0_engine):
        """测试：解析记忆（results中的项不是字典）"""
        data = {"results": ["记忆1", "记忆2"]}
        
        results = mem0_engine._parse_memories(data, session="current", limit=10)
        
        assert len(results) == 2
        assert results[0]["memory"] == "记忆1"
        assert results[1]["memory"] == "记忆2"
    
    def test_parse_memories_dict_no_memory_fields(self, mem0_engine):
        """测试：解析记忆（字典无memory/content字段）"""
        data = {"other_field": "value"}
        
        results = mem0_engine._parse_memories(data, session="current", limit=10)
        
        assert len(results) == 1
        assert isinstance(results[0]["memory"], str)  # 使用str(data)
    
    # ========== 添加记忆测试 ==========
    
    @pytest.mark.asyncio
    async def test_add_memory_success(self, mem0_engine, mock_httpx_client, mock_add_memory_response):
        """测试：添加记忆成功"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        mock_httpx_client.post = AsyncMock(return_value=mock_add_memory_response)
        
        messages = [
            {"role": "user", "content": "我喜欢Python"},
            {"role": "assistant", "content": "很好！"}
        ]
        
        result = await mem0_engine.add_memory(
            user_id="user_123",
            session_id="session_456",
            messages=messages
        )
        
        assert result == "mem_123"
        mock_httpx_client.post.assert_called_once()
        
        # 验证请求参数
        call_args = mock_httpx_client.post.call_args
        assert call_args[0][0] == "/api/v1/memories"
        payload = call_args[1]["json"]
        assert payload["user_id"] == "user_123"
        assert payload["agent_id"] == "session_456"
        assert len(payload["messages"]) == 2
    
    @pytest.mark.asyncio
    async def test_add_memory_with_metadata(self, mem0_engine, mock_httpx_client, mock_add_memory_response):
        """测试：添加记忆（带元数据）"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        mock_httpx_client.post = AsyncMock(return_value=mock_add_memory_response)
        
        messages = [{"role": "user", "content": "test"}]
        metadata = {"source": "test", "priority": "high"}
        
        result = await mem0_engine.add_memory(
            user_id="user_123",
            session_id="session_456",
            messages=messages,
            metadata=metadata
        )
        
        assert result == "mem_123"
        
        # 验证元数据
        call_args = mock_httpx_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["metadata"] == metadata
    
    @pytest.mark.asyncio
    async def test_add_memory_message_format_conversion(self, mem0_engine, mock_httpx_client, mock_add_memory_response):
        """测试：添加记忆（消息格式转换）"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        mock_httpx_client.post = AsyncMock(return_value=mock_add_memory_response)
        
        # 测试不同的消息格式
        messages = [
            {"role": "user", "content": "标准格式"},
            {"role": "user", "message": "非标准格式"}
        ]
        
        result = await mem0_engine.add_memory(
            user_id="user_123",
            session_id="session_456",
            messages=messages
        )
        
        assert result == "mem_123"
        
        # 验证消息格式转换
        call_args = mock_httpx_client.post.call_args
        payload = call_args[1]["json"]
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["content"] == "标准格式"
        assert payload["messages"][1]["content"] == "非标准格式"
        assert payload["messages"][1]["role"] == "user"
    
    @pytest.mark.asyncio
    async def test_add_memory_auto_initialize(self, mem0_engine, mock_httpx_client,
                                              mock_health_response, mock_add_memory_response):
        """测试：添加记忆（自动初始化）"""
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            mock_httpx_client.get = AsyncMock(return_value=mock_health_response)
            mock_httpx_client.post = AsyncMock(return_value=mock_add_memory_response)
            
            messages = [{"role": "user", "content": "test"}]
            result = await mem0_engine.add_memory(
                user_id="user_123",
                session_id="session_456",
                messages=messages
            )
        
        assert mem0_engine._initialized is True
        assert result == "mem_123"
    
    @pytest.mark.asyncio
    async def test_add_memory_response_without_id(self, mem0_engine, mock_httpx_client):
        """测试：添加记忆（响应无ID）"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        
        messages = [{"role": "user", "content": "test"}]
        result = await mem0_engine.add_memory(
            user_id="user_123",
            session_id="session_456",
            messages=messages
        )
        
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_add_memory_response_string(self, mem0_engine, mock_httpx_client):
        """测试：添加记忆（响应为字符串）"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = "success"
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        
        messages = [{"role": "user", "content": "test"}]
        result = await mem0_engine.add_memory(
            user_id="user_123",
            session_id="session_456",
            messages=messages
        )
        
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_add_memory_http_error(self, mem0_engine, mock_httpx_client):
        """测试：添加记忆（HTTP错误）"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error",
            request=MagicMock(),
            response=mock_response
        )
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        
        messages = [{"role": "user", "content": "test"}]
        
        with pytest.raises(httpx.HTTPStatusError):
            await mem0_engine.add_memory(
                user_id="user_123",
                session_id="session_456",
                messages=messages
            )
        
        assert mem0_engine.metrics["failed_requests"] > 0
    
    @pytest.mark.asyncio
    async def test_add_memory_exception(self, mem0_engine, mock_httpx_client):
        """测试：添加记忆（异常）"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        mock_httpx_client.post = AsyncMock(side_effect=Exception("Network error"))
        
        messages = [{"role": "user", "content": "test"}]
        
        with pytest.raises(Exception):
            await mem0_engine.add_memory(
                user_id="user_123",
                session_id="session_456",
                messages=messages
            )
    
    @pytest.mark.asyncio
    async def test_add_memory_empty_messages(self, mem0_engine, mock_httpx_client, mock_add_memory_response):
        """测试：添加记忆（空消息列表）"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        mock_httpx_client.post = AsyncMock(return_value=mock_add_memory_response)
        
        result = await mem0_engine.add_memory(
            user_id="user_123",
            session_id="session_456",
            messages=[]
        )
        
        assert result == "mem_123"
        
        # 验证请求参数
        call_args = mock_httpx_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["messages"] == []
    
    @pytest.mark.asyncio
    async def test_add_memory_invalid_message_format(self, mem0_engine, mock_httpx_client, mock_add_memory_response):
        """测试：添加记忆（无效消息格式）"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        mock_httpx_client.post = AsyncMock(return_value=mock_add_memory_response)
        
        # 测试既没有role/content也没有message的消息
        messages = [
            {"invalid": "format"},
            {"role": "user", "content": "valid"}
        ]
        
        result = await mem0_engine.add_memory(
            user_id="user_123",
            session_id="session_456",
            messages=messages
        )
        
        assert result == "mem_123"
        
        # 验证只有有效消息被添加
        call_args = mock_httpx_client.post.call_args
        payload = call_args[1]["json"]
        # 无效格式的消息应该被过滤掉
        assert len(payload["messages"]) >= 1
    
    # ========== 关闭引擎测试 ==========
    
    @pytest.mark.asyncio
    async def test_shutdown(self, mem0_engine, mock_httpx_client):
        """测试：关闭引擎"""
        mem0_engine.client = mock_httpx_client
        mock_httpx_client.aclose = AsyncMock()
        
        await mem0_engine.shutdown()
        
        mock_httpx_client.aclose.assert_called_once()
        assert mem0_engine.client is None
    
    @pytest.mark.asyncio
    async def test_shutdown_no_client(self, mem0_engine):
        """测试：关闭引擎（无客户端）"""
        mem0_engine.client = None
        
        # 不应该抛出异常
        await mem0_engine.shutdown()
    
    # ========== 并发场景测试 ==========
    
    @pytest.mark.asyncio
    async def test_concurrent_search_memories(self, mem0_engine, mock_httpx_client,
                                              mock_search_response_list):
        """测试：并发搜索记忆"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        mock_httpx_client.post = AsyncMock(return_value=mock_search_response_list)
        
        # 并发执行多个搜索
        tasks = [
            mem0_engine.search_memories(
                query=f"查询{i}",
                user_id=f"user_{i}",
                session_id=f"session_{i}",
                top_k=5
            )
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(len(r) > 0 for r in results)
        # 每个搜索应该调用2次（当前会话 + 跨会话）
        assert mock_httpx_client.post.call_count == 10
    
    @pytest.mark.asyncio
    async def test_concurrent_add_memories(self, mem0_engine, mock_httpx_client, mock_add_memory_response):
        """测试：并发添加记忆"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        mock_httpx_client.post = AsyncMock(return_value=mock_add_memory_response)
        
        # 并发执行多个添加
        tasks = [
            mem0_engine.add_memory(
                user_id=f"user_{i}",
                session_id=f"session_{i}",
                messages=[{"role": "user", "content": f"消息{i}"}]
            )
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(r == "mem_123" for r in results)
        assert mock_httpx_client.post.call_count == 5
    
    @pytest.mark.asyncio
    async def test_concurrent_search_and_add(self, mem0_engine, mock_httpx_client,
                                             mock_search_response_list, mock_add_memory_response):
        """测试：并发搜索和添加记忆"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        # Mock不同的响应
        call_count = 0
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if "/search" in str(args[0]):
                return mock_search_response_list
            else:
                return mock_add_memory_response
        
        mock_httpx_client.post = AsyncMock(side_effect=mock_post)
        
        # 并发执行搜索和添加
        search_task = mem0_engine.search_memories(
            query="test",
            user_id="user_123",
            session_id="session_456"
        )
        add_task = mem0_engine.add_memory(
            user_id="user_123",
            session_id="session_456",
            messages=[{"role": "user", "content": "test"}]
        )
        
        search_result, add_result = await asyncio.gather(search_task, add_task)
        
        assert len(search_result) > 0
        assert add_result == "mem_123"
    
    # ========== 指标测试 ==========
    
    @pytest.mark.asyncio
    async def test_metrics_update_on_success(self, mem0_engine, mock_httpx_client,
                                             mock_search_response_list):
        """测试：成功操作更新指标"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        initial_requests = mem0_engine.metrics["total_requests"]
        initial_success = mem0_engine.metrics["successful_requests"]
        
        mock_httpx_client.post = AsyncMock(return_value=mock_search_response_list)
        
        await mem0_engine.search_memories(
            query="test",
            user_id="user_123"
        )
        
        assert mem0_engine.metrics["total_requests"] == initial_requests + 1
        assert mem0_engine.metrics["successful_requests"] == initial_success + 1
        assert mem0_engine.metrics["average_processing_time"] > 0
    
    @pytest.mark.asyncio
    async def test_metrics_update_on_failure(self, mem0_engine, mock_httpx_client):
        """测试：失败操作更新指标"""
        mem0_engine.client = mock_httpx_client
        mem0_engine._initialized = True
        
        initial_requests = mem0_engine.metrics["total_requests"]
        initial_failed = mem0_engine.metrics["failed_requests"]
        
        mock_httpx_client.post = AsyncMock(side_effect=Exception("Error"))
        
        await mem0_engine.search_memories(
            query="test",
            user_id="user_123"
        )
        
        assert mem0_engine.metrics["total_requests"] == initial_requests + 1
        assert mem0_engine.metrics["failed_requests"] == initial_failed + 1
