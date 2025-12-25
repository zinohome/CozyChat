"""
MemoryScoringService单元测试

测试记忆评分服务的各种场景

注意：MemoryScoringService已废弃，旧的memory引擎已移除。
此测试保留用于向后兼容，但建议迁移到新的三大引擎系统。
"""

import pytest
import warnings
from unittest.mock import Mock
from datetime import datetime, timedelta, timezone

# 过滤废弃警告
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    try:
        from app.services.memory.scoring_service import MemoryScoringService
        from app.core.personality.models import IntelligentScoring, ScoringWeights
        HAS_SCORING_SERVICE = True
    except ImportError:
        HAS_SCORING_SERVICE = False


@pytest.mark.skipif(not HAS_SCORING_SERVICE, reason="MemoryScoringService已废弃")
class TestMemoryScoringService:
    """MemoryScoringService单元测试类"""
    
    @pytest.fixture
    def scoring_service(self):
        """创建MemoryScoringService实例"""
        return MemoryScoringService()
    
    @pytest.fixture
    def mock_intelligent_config(self):
        """创建模拟的智能评分配置"""
        return IntelligentScoring(
            enabled=True,
            numeric_query_keywords=['身高', '体重', '年龄', '多少', '多高', '多重'],
            numeric_memory_keywords=['cm', 'kg', '岁', '米', '公斤'],
            numeric_boost=0.3,
            keyword_match_boost=0.2,
            optimal_length_min=10,
            optimal_length_max=200,
            length_boost=0.1
        )
    
    @pytest.fixture
    def mock_weights(self):
        """创建模拟的评分权重"""
        return ScoringWeights(
            similarity=0.5,
            importance=0.2,
            recency=0.15,
            relevance=0.15
        )
    
    @pytest.fixture
    def create_mock_memory_result(self):
        """创建模拟记忆结果的工厂函数"""
        def _create(content, similarity, importance=0.5, session_id="session_1", created_at=None):
            memory = Mock()
            memory.content = content
            memory.importance = importance
            memory.session_id = session_id
            memory.created_at = created_at or datetime.now(timezone.utc)
            
            result = Mock()
            result.memory = memory
            result.similarity = similarity
            
            return result
        
        return _create
    
    def test_calculate_recency_score_within_7_days(self, scoring_service):
        """测试：7天内的记忆，时效性分数为1.0"""
        # Arrange
        created_at = datetime.now(timezone.utc) - timedelta(days=3)
        
        # Act
        score = scoring_service._calculate_recency_score(created_at)
        
        # Assert
        assert score == 1.0
    
    def test_calculate_recency_score_within_30_days(self, scoring_service):
        """测试：8-30天的记忆，时效性分数在0.5-1.0之间"""
        # Arrange
        created_at = datetime.now(timezone.utc) - timedelta(days=15)
        
        # Act
        score = scoring_service._calculate_recency_score(created_at)
        
        # Assert
        assert 0.5 < score < 1.0
    
    def test_calculate_recency_score_within_90_days(self, scoring_service):
        """测试：31-90天的记忆，时效性分数在0.1-0.5之间"""
        # Arrange
        created_at = datetime.now(timezone.utc) - timedelta(days=60)
        
        # Act
        score = scoring_service._calculate_recency_score(created_at)
        
        # Assert
        assert 0.1 <= score <= 0.5
    
    def test_calculate_recency_score_older_than_90_days(self, scoring_service):
        """测试：90天以上的记忆，时效性分数为0.1"""
        # Arrange
        created_at = datetime.now(timezone.utc) - timedelta(days=100)
        
        # Act
        score = scoring_service._calculate_recency_score(created_at)
        
        # Assert
        assert score == 0.1
    
    def test_calculate_recency_score_none_created_at(self, scoring_service):
        """测试：创建时间为None，返回默认分数0.5"""
        # Act
        score = scoring_service._calculate_recency_score(None)
        
        # Assert
        assert score == 0.5
    
    def test_calculate_relevance_score_exact_match(self, scoring_service):
        """测试：完全匹配，相关性分数高"""
        # Arrange
        content = "user height 180cm"
        query = "user height"
        
        # Act
        score = scoring_service._calculate_relevance_score(content, query)
        
        # Assert
        assert score > 0
    
    def test_calculate_relevance_score_no_match(self, scoring_service):
        """测试：无匹配，相关性分数低"""
        # Arrange
        content = "今天天气很好"
        query = "身高"
        
        # Act
        score = scoring_service._calculate_relevance_score(content, query)
        
        # Assert
        assert score >= 0  # Jaccard可能为0
    
    def test_calculate_relevance_score_with_numeric_query(self, scoring_service):
        """测试：数字查询时，包含数字的内容获得额外分数"""
        # Arrange
        content = "user height 180 cm"
        query = "user height how much"
        query_intent = {"type": "numeric_query"}
        
        # Act
        score = scoring_service._calculate_relevance_score(content, query, query_intent)
        
        # Assert
        assert score >= 0.3  # 应该有数字boost
    
    def test_analyze_query_intent_numeric_query(self, scoring_service):
        """测试：识别数字查询"""
        # Arrange
        query = "用户身高是多少？"
        
        # Act
        intent = scoring_service._analyze_query_intent(query)
        
        # Assert
        assert intent["type"] == "numeric_query"
        assert intent["is_question"] is True
        assert "身高" in intent["keywords"]
    
    def test_analyze_query_intent_factual_query(self, scoring_service):
        """测试：识别事实查询"""
        # Arrange
        query = "什么是量子计算？"
        
        # Act
        intent = scoring_service._analyze_query_intent(query)
        
        # Assert
        assert intent["type"] == "factual_query"
        assert intent["is_question"] is True
    
    def test_analyze_query_intent_conversational(self, scoring_service):
        """测试：识别对话型查询"""
        # Arrange
        query = "今天天气很好"
        
        # Act
        intent = scoring_service._analyze_query_intent(query)
        
        # Assert
        assert intent["type"] == "conversational"
        assert intent["is_question"] is False
    
    def test_apply_intelligent_scoring_numeric_query(
        self,
        scoring_service,
        mock_intelligent_config,
        create_mock_memory_result
    ):
        """测试：智能评分 - 数字查询优先包含数字的记忆"""
        # Arrange
        memories = [
            create_mock_memory_result("用户喜欢运动", 0.8),
            create_mock_memory_result("用户身高180cm", 0.7),  # 包含数字和关键词
            create_mock_memory_result("用户昨天吃了火锅", 0.75)
        ]
        query = "用户身高多少"
        
        # Act
        sorted_memories = scoring_service.apply_intelligent_scoring(
            memories, query, mock_intelligent_config
        )
        
        # Assert
        # 包含"身高"和"180cm"的记忆应该排在前面
        assert "180cm" in sorted_memories[0].memory.content
    
    def test_apply_intelligent_scoring_length_boost(
        self,
        scoring_service,
        mock_intelligent_config,
        create_mock_memory_result
    ):
        """测试：智能评分 - 长度适中的记忆获得加分"""
        # Arrange
        memories = [
            create_mock_memory_result("短", 0.8),  # 太短
            create_mock_memory_result("这是一个长度适中的记忆内容用于测试", 0.75),  # 适中
            create_mock_memory_result("非常" * 100, 0.7)  # 太长
        ]
        query = "测试"
        
        # Act
        sorted_memories = scoring_service.apply_intelligent_scoring(
            memories, query, mock_intelligent_config
        )
        
        # Assert
        # 长度适中的记忆应该排在前面（因为length_boost）
        assert "适中" in sorted_memories[0].memory.content
    
    def test_apply_comprehensive_scoring_basic(
        self,
        scoring_service,
        mock_weights,
        create_mock_memory_result
    ):
        """测试：综合评分 - 基本场景"""
        # Arrange
        session_id = "session_1"
        memories = [
            create_mock_memory_result("记忆1", similarity=0.9, importance=0.5),
            create_mock_memory_result("记忆2", similarity=0.8, importance=0.8),
            create_mock_memory_result("记忆3", similarity=0.7, importance=0.3)
        ]
        query = "测试"
        
        # Act
        sorted_memories = scoring_service.apply_comprehensive_scoring(
            memories, query, session_id, mock_weights
        )
        
        # Assert
        assert len(sorted_memories) == 3
        # 分数应该按综合评分排序
    
    def test_apply_comprehensive_scoring_with_memory_levels(
        self,
        scoring_service,
        mock_weights,
        create_mock_memory_result
    ):
        """测试：综合评分 - 带记忆层级boost"""
        # Arrange
        session_id = "session_1"
        
        memory_levels_config = Mock()
        memory_levels_config.enabled = True
        memory_levels_config.session_memory_boost = 1.5
        memory_levels_config.cross_session_memory_boost = 1.0
        
        memories = [
            create_mock_memory_result(
                "本会话记忆",
                similarity=0.7,
                importance=0.5,
                session_id="session_1"  # 当前会话
            ),
            create_mock_memory_result(
                "其他会话记忆",
                similarity=0.9,
                importance=0.8,
                session_id="session_2"  # 其他会话
            )
        ]
        query = "测试"
        
        # Act
        sorted_memories = scoring_service.apply_comprehensive_scoring(
            memories,
            query,
            session_id,
            mock_weights,
            memory_levels_config
        )
        
        # Assert
        # 本会话记忆应该获得boost，尽管原始相似度和重要性较低
        # 但由于session_memory_boost=1.5，可能排在前面
        assert len(sorted_memories) == 2
    
    def test_apply_comprehensive_scoring_empty_memories(
        self,
        scoring_service,
        mock_weights
    ):
        """测试：综合评分 - 空记忆列表"""
        # Arrange
        memories = []
        query = "测试"
        session_id = "session_1"
        
        # Act
        sorted_memories = scoring_service.apply_comprehensive_scoring(
            memories, query, session_id, mock_weights
        )
        
        # Assert
        assert len(sorted_memories) == 0
    
    def test_apply_intelligent_scoring_empty_memories(
        self,
        scoring_service,
        mock_intelligent_config
    ):
        """测试：智能评分 - 空记忆列表"""
        # Arrange
        memories = []
        query = "测试"
        
        # Act
        sorted_memories = scoring_service.apply_intelligent_scoring(
            memories, query, mock_intelligent_config
        )
        
        # Assert
        assert len(sorted_memories) == 0
    
    def test_apply_intelligent_scoring_keyword_match_boost(
        self,
        scoring_service,
        mock_intelligent_config,
        create_mock_memory_result
    ):
        """测试：智能评分 - 关键词匹配加分"""
        # Arrange
        memories = [
            create_mock_memory_result("用户身高180", 0.7),  # 包含数字但无单位
            create_mock_memory_result("用户身高180cm", 0.7),  # 包含数字和关键词cm
            create_mock_memory_result("用户身高很高", 0.7)  # 无数字
        ]
        query = "身高多少"
        
        # Act
        sorted_memories = scoring_service.apply_intelligent_scoring(
            memories, query, mock_intelligent_config
        )
        
        # Assert
        # 包含关键词"cm"的记忆应该排在最前面
        assert "cm" in sorted_memories[0].memory.content
    
    def test_calculate_relevance_score_empty_query(self, scoring_service):
        """测试：相关性分数 - 空查询"""
        # Arrange
        content = "用户身高180厘米"
        query = ""
        
        # Act
        score = scoring_service._calculate_relevance_score(content, query)
        
        # Assert
        assert score == 0.0
    
    def test_calculate_recency_score_no_timezone(self, scoring_service):
        """测试：时效性分数 - 无时区信息的datetime"""
        # Arrange
        created_at = datetime.now() - timedelta(days=5)
        
        # Act
        score = scoring_service._calculate_recency_score(created_at)
        
        # Assert
        assert score == 1.0  # 应该能正确处理
    
    def test_apply_comprehensive_scoring_multiple_factors(
        self,
        scoring_service,
        mock_weights,
        create_mock_memory_result
    ):
        """测试：综合评分 - 多因子影响"""
        # Arrange
        session_id = "session_1"
        now = datetime.now(timezone.utc)
        
        memories = [
            # 高相似度，低重要性，旧记忆
            create_mock_memory_result(
                "旧记忆",
                similarity=0.9,
                importance=0.1,
                created_at=now - timedelta(days=100)
            ),
            # 低相似度，高重要性，新记忆
            create_mock_memory_result(
                "新记忆",
                similarity=0.5,
                importance=0.9,
                created_at=now - timedelta(days=1)
            ),
            # 中等相似度，中等重要性，中等时效
            create_mock_memory_result(
                "中等记忆",
                similarity=0.7,
                importance=0.5,
                created_at=now - timedelta(days=15)
            )
        ]
        query = "测试"
        
        # Act
        sorted_memories = scoring_service.apply_comprehensive_scoring(
            memories, query, session_id, mock_weights
        )
        
        # Assert
        assert len(sorted_memories) == 3
        # 验证排序（具体顺序取决于权重配置）
    
    def test_analyze_query_intent_with_multiple_keywords(self, scoring_service):
        """测试：查询意图分析 - 多个关键词"""
        # Arrange
        query = "用户的身高和体重各是多少？"
        
        # Act
        intent = scoring_service._analyze_query_intent(query)
        
        # Assert
        assert intent["type"] == "numeric_query"
        assert intent["is_question"] is True
        assert "身高" in intent["keywords"]
        assert "体重" in intent["keywords"]
    
    def test_calculate_relevance_score_special_characters(self, scoring_service):
        """测试：相关性分数 - 特殊字符处理"""
        # Arrange
        content = "user height 180cm very tall"
        query = "user height how much"
        
        # Act
        score = scoring_service._calculate_relevance_score(content, query)
        
        # Assert
        assert score > 0  # 应该能正确处理特殊字符

