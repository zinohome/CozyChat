"""
Cognee知识引擎单元测试

测试Cognee知识引擎的所有方法，包括：
- 引擎初始化
- 健康检查
- 知识搜索（CHUNKS和GRAPH_COMPLETION模式）
- 搜索结果解析
- 知识添加
- 引擎关闭
- 错误处理和边界条件

覆盖率要求：≥85%
"""

# 标准库
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

# 第三方库
import pytest
from cognee_sdk import SearchType

# 本地库
from app.engines.knowledge.cognee_engine import CogneeKnowledgeEngine


class TestCogneeKnowledgeEngine:
    """Cognee知识引擎测试类"""
    
    @pytest.fixture
    def engine_config(self):
        """引擎配置"""
        return {
            "api_url": "http://localhost:8000",
            "api_token": "test_token"
        }
    
    @pytest.fixture
    def engine_config_no_token(self):
        """引擎配置（无token）"""
        return {
            "api_url": "http://localhost:8000"
        }
    
    @pytest.fixture
    def engine_config_default(self):
        """引擎配置（默认值）"""
        return {}
    
    @pytest.fixture
    def mock_cognee_client(self):
        """Mock Cognee客户端"""
        mock_client = AsyncMock()
        
        # Mock health_check方法
        mock_health = MagicMock()
        mock_health.status = "ok"
        mock_client.health_check = AsyncMock(return_value=mock_health)
        
        # Mock search方法
        mock_client.search = AsyncMock()
        
        # Mock add方法
        mock_add_result = MagicMock()
        mock_add_result.data_id = "test_data_id_123"
        mock_client.add = AsyncMock(return_value=mock_add_result)
        
        return mock_client
    
    @pytest.fixture
    def mock_search_result_chunks(self):
        """Mock CHUNKS模式搜索结果"""
        mock_result1 = MagicMock()
        mock_result1.text = "这是第一个搜索结果"
        mock_result1.score = 0.95
        
        mock_result2 = MagicMock()
        mock_result2.text = "这是第二个搜索结果"
        mock_result2.score = 0.88
        
        return [mock_result1, mock_result2]
    
    @pytest.fixture
    def mock_search_result_graph(self):
        """Mock GRAPH_COMPLETION模式搜索结果（字符串列表）"""
        return [
            "这是第一个搜索结果",
            "这是第二个搜索结果",
            "这是第三个搜索结果"
        ]
    
    # ========== 引擎初始化测试 ==========
    
    def test_engine_initialization_with_config(self, engine_config):
        """测试：使用配置初始化引擎"""
        engine = CogneeKnowledgeEngine(engine_config)
        
        assert engine.engine_name == "cognee"
        assert engine.api_url == engine_config["api_url"]
        assert engine.api_token == engine_config["api_token"]
        assert engine.client is None
        assert engine._initialized is False
    
    def test_engine_initialization_without_token(self, engine_config_no_token):
        """测试：无token初始化引擎"""
        engine = CogneeKnowledgeEngine(engine_config_no_token)
        
        assert engine.api_url == engine_config_no_token["api_url"]
        assert engine.api_token is None
    
    def test_engine_initialization_with_defaults(self, engine_config_default):
        """测试：使用默认值初始化引擎"""
        engine = CogneeKnowledgeEngine(engine_config_default)
        
        assert engine.api_url == "http://localhost:8000"
        assert engine.api_token is None
    
    @pytest.mark.asyncio
    async def test_initialize_success(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：初始化成功"""
        with patch('app.engines.knowledge.cognee_engine.CogneeClient') as mock_client_class:
            mock_client_class.return_value = mock_cognee_client
            
            engine = CogneeKnowledgeEngine(engine_config)
            result = await engine.initialize()
            
            assert result is True
            assert engine._initialized is True
            assert engine.client is not None
            mock_client_class.assert_called_once_with(
                api_url=engine_config["api_url"],
                api_token=engine_config["api_token"]
            )
            mock_cognee_client.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_already_initialized(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：重复初始化（已初始化）"""
        with patch('app.engines.knowledge.cognee_engine.CogneeClient') as mock_client_class:
            mock_client_class.return_value = mock_cognee_client
            
            engine = CogneeKnowledgeEngine(engine_config)
            engine._initialized = True
            engine.client = mock_cognee_client
            
            result = await engine.initialize()
            
            assert result is True
            # 不应该再次创建客户端
            mock_client_class.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_initialize_health_check_failed(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：初始化时健康检查失败"""
        # Mock健康检查返回False
        mock_cognee_client.health_check = AsyncMock(return_value=None)
        
        with patch('app.engines.knowledge.cognee_engine.CogneeClient') as mock_client_class:
            mock_client_class.return_value = mock_cognee_client
            
            engine = CogneeKnowledgeEngine(engine_config)
            result = await engine.initialize()
            
            assert result is False
            assert engine._initialized is False
    
    @pytest.mark.asyncio
    async def test_initialize_exception(
        self,
        engine_config
    ):
        """测试：初始化时发生异常"""
        with patch('app.engines.knowledge.cognee_engine.CogneeClient') as mock_client_class:
            mock_client_class.side_effect = Exception("Connection error")
            
            engine = CogneeKnowledgeEngine(engine_config)
            result = await engine.initialize()
            
            assert result is False
            assert engine._initialized is False
    
    # ========== 健康检查测试 ==========
    
    @pytest.mark.asyncio
    async def test_health_check_success_ok(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：健康检查成功（status=ok）"""
        mock_health = MagicMock()
        mock_health.status = "ok"
        mock_cognee_client.health_check = AsyncMock(return_value=mock_health)
        
        engine = CogneeKnowledgeEngine(engine_config)
        engine.client = mock_cognee_client
        
        result = await engine.health_check()
        
        assert result is True
        mock_cognee_client.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_success_ready(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：健康检查成功（status=ready）"""
        mock_health = MagicMock()
        mock_health.status = "ready"
        mock_cognee_client.health_check = AsyncMock(return_value=mock_health)
        
        engine = CogneeKnowledgeEngine(engine_config)
        engine.client = mock_cognee_client
        
        result = await engine.health_check()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failed_status(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：健康检查失败（status不为ok或ready）"""
        mock_health = MagicMock()
        mock_health.status = "error"
        mock_cognee_client.health_check = AsyncMock(return_value=mock_health)
        
        engine = CogneeKnowledgeEngine(engine_config)
        engine.client = mock_cognee_client
        
        result = await engine.health_check()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_no_client(
        self,
        engine_config
    ):
        """测试：健康检查失败（客户端未初始化）"""
        engine = CogneeKnowledgeEngine(engine_config)
        engine.client = None
        
        result = await engine.health_check()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_exception(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：健康检查异常"""
        mock_cognee_client.health_check = AsyncMock(side_effect=Exception("Network error"))
        
        engine = CogneeKnowledgeEngine(engine_config)
        engine.client = mock_cognee_client
        
        result = await engine.health_check()
        
        assert result is False
    
    # ========== 知识搜索测试 ==========
    
    @pytest.mark.asyncio
    async def test_search_knowledge_chunks_success(
        self,
        engine_config,
        mock_cognee_client,
        mock_search_result_chunks
    ):
        """测试：搜索知识成功（CHUNKS模式）"""
        mock_cognee_client.search = AsyncMock(return_value=mock_search_result_chunks)
        
        with patch('app.engines.knowledge.cognee_engine.CogneeClient') as mock_client_class:
            mock_client_class.return_value = mock_cognee_client
            
            engine = CogneeKnowledgeEngine(engine_config)
            engine.client = mock_cognee_client
            engine._initialized = True
            
            results = await engine.search_knowledge(
                query="Python编程",
                dataset_names=["test_dataset"],
                top_k=5
            )
            
            assert len(results) == 2
            assert results[0]["content"] == "这是第一个搜索结果"
            assert results[0]["score"] == 0.95
            assert results[0]["source"] == "test_dataset"
            assert results[1]["content"] == "这是第二个搜索结果"
            assert results[1]["score"] == 0.88
            
            # 验证调用了CHUNKS模式
            mock_cognee_client.search.assert_called_once_with(
                query="Python编程",
                datasets=["test_dataset"],
                search_type=SearchType.CHUNKS,
                top_k=5
            )
    
    @pytest.mark.asyncio
    async def test_search_knowledge_chunks_empty_fallback(
        self,
        engine_config,
        mock_cognee_client,
        mock_search_result_graph
    ):
        """测试：CHUNKS模式返回空，降级到GRAPH_COMPLETION"""
        # 第一次调用返回空列表
        # 第二次调用返回GRAPH_COMPLETION结果
        mock_cognee_client.search = AsyncMock(side_effect=[
            [],  # CHUNKS模式返回空
            mock_search_result_graph  # GRAPH_COMPLETION模式返回结果
        ])
        
        with patch('app.engines.knowledge.cognee_engine.CogneeClient') as mock_client_class:
            mock_client_class.return_value = mock_cognee_client
            
            engine = CogneeKnowledgeEngine(engine_config)
            engine.client = mock_cognee_client
            engine._initialized = True
            
            results = await engine.search_knowledge(
                query="Python编程",
                dataset_names=["test_dataset"],
                top_k=5
            )
            
            assert len(results) == 3
            # 验证调用了两次search（CHUNKS和GRAPH_COMPLETION）
            assert mock_cognee_client.search.call_count == 2
    
    @pytest.mark.asyncio
    async def test_search_knowledge_chunks_exception_fallback(
        self,
        engine_config,
        mock_cognee_client,
        mock_search_result_graph
    ):
        """测试：CHUNKS模式异常，降级到GRAPH_COMPLETION"""
        # 第一次调用抛出异常
        # 第二次调用返回GRAPH_COMPLETION结果
        mock_cognee_client.search = AsyncMock(side_effect=[
            Exception("CHUNKS mode error"),  # CHUNKS模式异常
            mock_search_result_graph  # GRAPH_COMPLETION模式返回结果
        ])
        
        with patch('app.engines.knowledge.cognee_engine.CogneeClient') as mock_client_class:
            mock_client_class.return_value = mock_cognee_client
            
            engine = CogneeKnowledgeEngine(engine_config)
            engine.client = mock_cognee_client
            engine._initialized = True
            
            results = await engine.search_knowledge(
                query="Python编程",
                dataset_names=["test_dataset"],
                top_k=5
            )
            
            assert len(results) == 3
            # 验证调用了两次search
            assert mock_cognee_client.search.call_count == 2
    
    @pytest.mark.asyncio
    async def test_search_knowledge_graph_completion_success(
        self,
        engine_config,
        mock_cognee_client,
        mock_search_result_graph
    ):
        """测试：搜索知识成功（直接使用GRAPH_COMPLETION模式）"""
        # 模拟CHUNKS模式返回空，直接使用GRAPH_COMPLETION
        mock_cognee_client.search = AsyncMock(side_effect=[
            [],  # CHUNKS模式返回空
            mock_search_result_graph  # GRAPH_COMPLETION模式返回结果
        ])
        
        with patch('app.engines.knowledge.cognee_engine.CogneeClient') as mock_client_class:
            mock_client_class.return_value = mock_cognee_client
            
            engine = CogneeKnowledgeEngine(engine_config)
            engine.client = mock_cognee_client
            engine._initialized = True
            
            results = await engine.search_knowledge(
                query="Python编程",
                dataset_names=["test_dataset"],
                top_k=5
            )
            
            assert len(results) == 3
            assert results[0]["content"] == "这是第一个搜索结果"
            assert results[0]["score"] == 1.0  # 默认分数
            assert results[1]["score"] == 0.9  # 递减分数
            assert results[2]["score"] == 0.8
    
    @pytest.mark.asyncio
    async def test_search_knowledge_no_datasets(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：搜索知识失败（未提供数据集）"""
        with patch('app.engines.knowledge.cognee_engine.CogneeClient') as mock_client_class:
            mock_client_class.return_value = mock_cognee_client
            
            engine = CogneeKnowledgeEngine(engine_config)
            engine.client = mock_cognee_client
            engine._initialized = True
            
            results = await engine.search_knowledge(
                query="Python编程",
                dataset_names=None
            )
            
            assert results == []
            # 不应该调用search
            mock_cognee_client.search.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_search_knowledge_empty_datasets(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：搜索知识失败（空数据集列表）"""
        with patch('app.engines.knowledge.cognee_engine.CogneeClient') as mock_client_class:
            mock_client_class.return_value = mock_cognee_client
            
            engine = CogneeKnowledgeEngine(engine_config)
            engine.client = mock_cognee_client
            engine._initialized = True
            
            results = await engine.search_knowledge(
                query="Python编程",
                dataset_names=[]
            )
            
            assert results == []
            mock_cognee_client.search.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_search_knowledge_dataset_not_found(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：搜索知识失败（数据集不存在）"""
        mock_cognee_client.search = AsyncMock(side_effect=Exception("DatasetNotFoundError: Dataset not found"))
        
        with patch('app.engines.knowledge.cognee_engine.CogneeClient') as mock_client_class:
            mock_client_class.return_value = mock_cognee_client
            
            engine = CogneeKnowledgeEngine(engine_config)
            engine.client = mock_cognee_client
            engine._initialized = True
            
            results = await engine.search_knowledge(
                query="Python编程",
                dataset_names=["nonexistent_dataset"],
                top_k=5
            )
            
            assert results == []
    
    @pytest.mark.asyncio
    async def test_search_knowledge_general_exception(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：搜索知识失败（一般异常）"""
        mock_cognee_client.search = AsyncMock(side_effect=Exception("General error"))
        
        with patch('app.engines.knowledge.cognee_engine.CogneeClient') as mock_client_class:
            mock_client_class.return_value = mock_cognee_client
            
            engine = CogneeKnowledgeEngine(engine_config)
            engine.client = mock_cognee_client
            engine._initialized = True
            
            results = await engine.search_knowledge(
                query="Python编程",
                dataset_names=["test_dataset"],
                top_k=5
            )
            
            assert results == []
    
    @pytest.mark.asyncio
    async def test_search_knowledge_auto_initialize(
        self,
        engine_config,
        mock_cognee_client,
        mock_search_result_chunks
    ):
        """测试：搜索知识时自动初始化"""
        mock_cognee_client.search = AsyncMock(return_value=mock_search_result_chunks)
        
        with patch('app.engines.knowledge.cognee_engine.CogneeClient') as mock_client_class:
            mock_client_class.return_value = mock_cognee_client
            
            engine = CogneeKnowledgeEngine(engine_config)
            # 不手动初始化
            
            results = await engine.search_knowledge(
                query="Python编程",
                dataset_names=["test_dataset"],
                top_k=5
            )
            
            assert len(results) == 2
            # 验证自动初始化被调用
            assert engine._initialized is True
            assert engine.client is not None
    
    @pytest.mark.asyncio
    async def test_search_knowledge_multiple_datasets(
        self,
        engine_config,
        mock_cognee_client,
        mock_search_result_chunks
    ):
        """测试：搜索知识（多个数据集）"""
        mock_cognee_client.search = AsyncMock(return_value=mock_search_result_chunks)
        
        engine = CogneeKnowledgeEngine(engine_config)
        engine.client = mock_cognee_client
        engine._initialized = True
        
        results = await engine.search_knowledge(
            query="Python编程",
            dataset_names=["dataset1", "dataset2"],
            top_k=10
        )
        
        assert len(results) == 2
        # 验证传递了多个数据集
        call_args = mock_cognee_client.search.call_args
        assert call_args[1]["datasets"] == ["dataset1", "dataset2"]
        assert call_args[1]["top_k"] == 10
    
    # ========== 搜索结果解析测试 ==========
    
    def test_parse_search_results_string_format(
        self,
        engine_config
    ):
        """测试：解析搜索结果（字符串格式）"""
        engine = CogneeKnowledgeEngine(engine_config)
        
        results = ["结果1", "结果2", "结果3"]
        dataset_names = ["test_dataset"]
        
        parsed = engine._parse_search_results(results, dataset_names)
        
        assert len(parsed) == 3
        assert parsed[0]["content"] == "结果1"
        assert parsed[0]["score"] == 1.0
        assert parsed[1]["score"] == 0.9
        assert parsed[2]["score"] == 0.8
        assert all(r["source"] == "test_dataset" for r in parsed)
    
    def test_parse_search_results_object_with_text(
        self,
        engine_config
    ):
        """测试：解析搜索结果（对象格式，有text属性）"""
        engine = CogneeKnowledgeEngine(engine_config)
        
        mock_result1 = MagicMock()
        mock_result1.text = "结果1"
        mock_result1.score = 0.95
        
        mock_result2 = MagicMock()
        mock_result2.text = "结果2"
        mock_result2.score = 0.88
        
        results = [mock_result1, mock_result2]
        dataset_names = ["test_dataset"]
        
        parsed = engine._parse_search_results(results, dataset_names)
        
        assert len(parsed) == 2
        assert parsed[0]["content"] == "结果1"
        assert parsed[0]["score"] == 0.95
        assert parsed[1]["content"] == "结果2"
        assert parsed[1]["score"] == 0.88
    
    def test_parse_search_results_object_with_content(
        self,
        engine_config
    ):
        """测试：解析搜索结果（对象格式，有content属性）"""
        engine = CogneeKnowledgeEngine(engine_config)
        
        mock_result1 = MagicMock()
        mock_result1.content = "结果1"
        mock_result1.score = 0.90
        
        results = [mock_result1]
        dataset_names = ["test_dataset"]
        
        parsed = engine._parse_search_results(results, dataset_names)
        
        assert len(parsed) == 1
        assert parsed[0]["content"] == "结果1"
        assert parsed[0]["score"] == 0.90
    
    def test_parse_search_results_dict_format(
        self,
        engine_config
    ):
        """测试：解析搜索结果（字典格式）"""
        engine = CogneeKnowledgeEngine(engine_config)
        
        results = [
            {"text": "结果1", "score": 0.95},
            {"content": "结果2", "score": 0.88},
            {"other": "结果3"}  # 无text或content，使用str(result)
        ]
        dataset_names = ["test_dataset"]
        
        parsed = engine._parse_search_results(results, dataset_names)
        
        assert len(parsed) == 3
        assert parsed[0]["content"] == "结果1"
        assert parsed[0]["score"] == 0.95
        assert parsed[1]["content"] == "结果2"
        assert parsed[1]["score"] == 0.88
        assert "结果3" in parsed[2]["content"]  # str(result)包含结果
    
    def test_parse_search_results_mixed_format(
        self,
        engine_config
    ):
        """测试：解析搜索结果（混合格式）"""
        engine = CogneeKnowledgeEngine(engine_config)
        
        mock_result = MagicMock()
        mock_result.text = "对象结果"
        mock_result.score = 0.85
        
        results = [
            "字符串结果1",
            mock_result,
            {"text": "字典结果", "score": 0.75}
        ]
        dataset_names = ["test_dataset"]
        
        parsed = engine._parse_search_results(results, dataset_names)
        
        assert len(parsed) == 3
        assert parsed[0]["content"] == "字符串结果1"
        assert parsed[1]["content"] == "对象结果"
        assert parsed[1]["score"] == 0.85
        assert parsed[2]["content"] == "字典结果"
        assert parsed[2]["score"] == 0.75
    
    def test_parse_search_results_unparseable(
        self,
        engine_config
    ):
        """测试：解析搜索结果（无法解析的结果）"""
        engine = CogneeKnowledgeEngine(engine_config)
        
        # 创建一个无法解析的对象
        class UnparseableResult:
            pass
        
        results = [UnparseableResult()]
        dataset_names = ["test_dataset"]
        
        parsed = engine._parse_search_results(results, dataset_names)
        
        # 无法解析的结果应该被跳过
        assert len(parsed) == 0
    
    def test_parse_search_results_empty(
        self,
        engine_config
    ):
        """测试：解析搜索结果（空列表）"""
        engine = CogneeKnowledgeEngine(engine_config)
        
        results = []
        dataset_names = ["test_dataset"]
        
        parsed = engine._parse_search_results(results, dataset_names)
        
        assert len(parsed) == 0
    
    def test_parse_search_results_no_dataset(
        self,
        engine_config
    ):
        """测试：解析搜索结果（无数据集名称）"""
        engine = CogneeKnowledgeEngine(engine_config)
        
        results = ["结果1", "结果2"]
        dataset_names = []
        
        parsed = engine._parse_search_results(results, dataset_names)
        
        assert len(parsed) == 2
        assert all(r["source"] == "unknown" for r in parsed)
    
    # ========== 知识添加测试 ==========
    
    @pytest.mark.asyncio
    async def test_add_knowledge_success(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：添加知识成功"""
        mock_add_result = MagicMock()
        mock_add_result.data_id = "test_data_id_456"
        mock_cognee_client.add = AsyncMock(return_value=mock_add_result)
        
        with patch('app.engines.knowledge.cognee_engine.CogneeClient') as mock_client_class:
            mock_client_class.return_value = mock_cognee_client
            
            engine = CogneeKnowledgeEngine(engine_config)
            engine.client = mock_cognee_client
            engine._initialized = True
            
            result_id = await engine.add_knowledge(
                content="Python是一种编程语言",
                dataset_name="test_dataset",
                metadata={"category": "programming"}
            )
            
            assert result_id == "test_data_id_456"
            mock_cognee_client.add.assert_called_once_with(
                data="Python是一种编程语言",
                dataset_name="test_dataset",
                metadata={"category": "programming"}
            )
    
    @pytest.mark.asyncio
    async def test_add_knowledge_no_metadata(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：添加知识（无元数据）"""
        mock_add_result = MagicMock()
        mock_add_result.data_id = "test_data_id_789"
        mock_cognee_client.add = AsyncMock(return_value=mock_add_result)
        
        engine = CogneeKnowledgeEngine(engine_config)
        engine.client = mock_cognee_client
        engine._initialized = True
        
        result_id = await engine.add_knowledge(
            content="Python是一种编程语言",
            dataset_name="test_dataset"
        )
        
        assert result_id == "test_data_id_789"
        mock_cognee_client.add.assert_called_once_with(
            data="Python是一种编程语言",
            dataset_name="test_dataset",
            metadata=None
        )
    
    @pytest.mark.asyncio
    async def test_add_knowledge_with_kwargs(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：添加知识（带额外参数）"""
        mock_add_result = MagicMock()
        mock_add_result.data_id = "test_data_id_999"
        mock_cognee_client.add = AsyncMock(return_value=mock_add_result)
        
        engine = CogneeKnowledgeEngine(engine_config)
        engine.client = mock_cognee_client
        engine._initialized = True
        
        result_id = await engine.add_knowledge(
            content="Python是一种编程语言",
            dataset_name="test_dataset",
            metadata={"category": "programming"},
            chunk_size=100,
            overlap=20
        )
        
        assert result_id == "test_data_id_999"
        call_args = mock_cognee_client.add.call_args
        assert call_args[1]["chunk_size"] == 100
        assert call_args[1]["overlap"] == 20
    
    @pytest.mark.asyncio
    async def test_add_knowledge_exception(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：添加知识失败（异常）"""
        mock_cognee_client.add = AsyncMock(side_effect=Exception("Add knowledge error"))
        
        engine = CogneeKnowledgeEngine(engine_config)
        engine.client = mock_cognee_client
        engine._initialized = True
        
        with pytest.raises(Exception) as exc_info:
            await engine.add_knowledge(
                content="Python是一种编程语言",
                dataset_name="test_dataset"
            )
        
        assert "Add knowledge error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_add_knowledge_auto_initialize(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：添加知识时自动初始化"""
        mock_add_result = MagicMock()
        mock_add_result.data_id = "test_data_id_auto"
        mock_cognee_client.add = AsyncMock(return_value=mock_add_result)
        
        with patch('app.engines.knowledge.cognee_engine.CogneeClient') as mock_client_class:
            mock_client_class.return_value = mock_cognee_client
            
            engine = CogneeKnowledgeEngine(engine_config)
            # 不手动初始化
            
            result_id = await engine.add_knowledge(
                content="Python是一种编程语言",
                dataset_name="test_dataset"
            )
            
            assert result_id == "test_data_id_auto"
            # 验证自动初始化被调用
            assert engine._initialized is True
            assert engine.client is not None
    
    # ========== 引擎关闭测试 ==========
    
    @pytest.mark.asyncio
    async def test_shutdown_with_client(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：关闭引擎（有客户端）"""
        engine = CogneeKnowledgeEngine(engine_config)
        engine.client = mock_cognee_client
        engine._initialized = True
        
        await engine.shutdown()
        
        assert engine.client is None
    
    @pytest.mark.asyncio
    async def test_shutdown_without_client(
        self,
        engine_config
    ):
        """测试：关闭引擎（无客户端）"""
        engine = CogneeKnowledgeEngine(engine_config)
        engine.client = None
        
        await engine.shutdown()
        
        assert engine.client is None
    
    # ========== 指标更新测试 ==========
    
    @pytest.mark.asyncio
    async def test_metrics_update_on_success(
        self,
        engine_config,
        mock_cognee_client,
        mock_search_result_chunks
    ):
        """测试：成功操作更新指标"""
        mock_cognee_client.search = AsyncMock(return_value=mock_search_result_chunks)
        
        engine = CogneeKnowledgeEngine(engine_config)
        engine.client = mock_cognee_client
        engine._initialized = True
        
        initial_metrics = engine.get_metrics()
        initial_total = initial_metrics["total_requests"]
        initial_success = initial_metrics["successful_requests"]
        
        await engine.search_knowledge(
            query="test",
            dataset_names=["test_dataset"],
            top_k=5
        )
        
        updated_metrics = engine.get_metrics()
        assert updated_metrics["total_requests"] == initial_total + 1
        assert updated_metrics["successful_requests"] == initial_success + 1
        assert updated_metrics["failed_requests"] == initial_metrics["failed_requests"]
        assert updated_metrics["average_processing_time"] > 0
    
    @pytest.mark.asyncio
    async def test_metrics_update_on_failure(
        self,
        engine_config,
        mock_cognee_client
    ):
        """测试：失败操作更新指标"""
        mock_cognee_client.search = AsyncMock(side_effect=Exception("Error"))
        
        engine = CogneeKnowledgeEngine(engine_config)
        engine.client = mock_cognee_client
        engine._initialized = True
        
        initial_metrics = engine.get_metrics()
        initial_total = initial_metrics["total_requests"]
        initial_failed = initial_metrics["failed_requests"]
        
        await engine.search_knowledge(
            query="test",
            dataset_names=["test_dataset"],
            top_k=5
        )
        
        updated_metrics = engine.get_metrics()
        assert updated_metrics["total_requests"] == initial_total + 1
        assert updated_metrics["failed_requests"] == initial_failed + 1
        assert updated_metrics["successful_requests"] == initial_metrics["successful_requests"]
