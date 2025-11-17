"""
重要性评分器测试

测试记忆重要性评分算法
"""

# 标准库
import pytest
from datetime import datetime, timedelta

# 本地库
from app.engines.memory.importance_scorer import ImportanceScorer


class TestImportanceScorer:
    """测试重要性评分器"""
    
    @pytest.fixture
    def scorer(self):
        """创建评分器实例"""
        return ImportanceScorer()
    
    def test_calculate_importance_empty_content(self, scorer):
        """测试：空内容"""
        importance = scorer.calculate_importance("")
        assert importance == 0.0
    
    def test_calculate_importance_short_content(self, scorer):
        """测试：短内容"""
        importance = scorer.calculate_importance("Hello")
        assert 0.0 <= importance <= 1.0
    
    def test_calculate_importance_long_content(self, scorer):
        """测试：长内容"""
        long_content = "A" * 500
        importance = scorer.calculate_importance(long_content)
        assert importance > 0.5  # 长内容应该有较高分数
    
    def test_calculate_importance_with_keywords(self, scorer):
        """测试：包含关键词"""
        content = "我的名字是张三，我喜欢编程"
        importance = scorer.calculate_importance(content)
        assert importance > 0.5  # 包含关键词应该有较高分数
    
    def test_calculate_importance_with_metadata(self, scorer):
        """测试：带元数据"""
        metadata = {"access_count": 5}
        importance = scorer.calculate_importance(
            "Test content",
            metadata=metadata
        )
        assert 0.0 <= importance <= 1.0
    
    def test_calculate_importance_recent(self, scorer):
        """测试：新记忆"""
        recent_date = datetime.utcnow() - timedelta(days=1)
        importance = scorer.calculate_importance(
            "Test content",
            created_at=recent_date
        )
        assert importance > 0.5
    
    def test_calculate_importance_old(self, scorer):
        """测试：旧记忆"""
        old_date = datetime.utcnow() - timedelta(days=200)
        importance = scorer.calculate_importance(
            "Test content",
            created_at=old_date
        )
        assert importance < 0.5  # 旧记忆分数应该较低
    
    def test_calculate_length_score(self, scorer):
        """测试：长度评分"""
        assert scorer._calculate_length_score("") == 0.0
        assert scorer._calculate_length_score("A" * 5) == 0.1
        assert scorer._calculate_length_score("A" * 30) > 0.3
        assert scorer._calculate_length_score("A" * 100) > 0.6
        assert scorer._calculate_length_score("A" * 300) == 0.9
    
    def test_calculate_keyword_score(self, scorer):
        """测试：关键词评分"""
        assert scorer._calculate_keyword_score("Hello") < 0.5
        assert scorer._calculate_keyword_score("我的名字") > 0.3
        assert scorer._calculate_keyword_score("我喜欢编程，我的爱好是阅读") > 0.5
    
    def test_calculate_frequency_score(self, scorer):
        """测试：频率评分"""
        assert scorer._calculate_frequency_score({}) == 0.5
        assert scorer._calculate_frequency_score({"access_count": 1}) == 0.6
        assert scorer._calculate_frequency_score({"access_count": 10}) == 1.0
    
    def test_calculate_recency_score(self, scorer):
        """测试：时间评分"""
        recent = datetime.utcnow() - timedelta(days=1)
        assert scorer._calculate_recency_score(recent) == 1.0
        
        old = datetime.utcnow() - timedelta(days=200)
        assert scorer._calculate_recency_score(old) == 0.2
    
    def test_update_access_frequency(self, scorer):
        """测试：更新访问频率"""
        metadata = {}
        updated = scorer.update_access_frequency(metadata)
        assert updated["access_count"] == 1
        
        updated = scorer.update_access_frequency(updated, increment=2)
        assert updated["access_count"] == 3

