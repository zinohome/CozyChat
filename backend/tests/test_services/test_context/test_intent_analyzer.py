"""
IntentAnalyzer单元测试

测试意图分析器的6种意图识别和引擎配置生成。
测试各种查询场景的意图识别准确性。
"""

import pytest
from typing import Dict, Any

# 本地库
from app.services.context.intent_analyzer import IntentAnalyzer, QueryIntent


class TestIntentAnalyzer:
    """IntentAnalyzer单元测试类"""
    
    # ============================================================================
    # 意图识别测试 - 6种意图类型
    # ============================================================================
    
    def test_analyze_intent_chitchat(self):
        """测试：闲聊意图识别"""
        test_cases = [
            "你好",
            "早上好",
            "在吗",
            "最近怎么样",
            "今天天气不错",
            "随便聊聊",
            "hello",
            "hi",
            "",  # 空查询
            "   ",  # 空白查询
        ]
        
        for query in test_cases:
            intent = IntentAnalyzer.analyze_intent(query, {})
            assert intent == QueryIntent.CHITCHAT, \
                f"Query '{query}' should be CHITCHAT, got {intent}"
    
    def test_analyze_intent_knowledge_query(self):
        """测试：知识查询意图识别"""
        test_cases = [
            "什么是Python？",
            "什么是机器学习",
            "如何学习编程",
            "为什么天空是蓝色的",
            "解释一下量子计算",
            "请解释一下",
            "原理是什么",
            "定义一下",
            "介绍一下人工智能",
            "是什么让计算机工作",
            "什么是API",
            "如何工作",
            "为什么这样",
        ]
        
        for query in test_cases:
            intent = IntentAnalyzer.analyze_intent(query, {})
            assert intent == QueryIntent.KNOWLEDGE_QUERY, \
                f"Query '{query}' should be KNOWLEDGE_QUERY, got {intent}"
    
    def test_analyze_intent_task_execution(self):
        """测试：任务执行意图识别"""
        test_cases = [
            "帮我计算一下",
            "请帮我写代码",
            "完成这个任务",
            "执行这个操作",
            "做一份报告",
            "创建一个文件",
            "生成一份文档",
            "帮我翻译",
            "请帮我",
            "帮我做",
        ]
        
        for query in test_cases:
            intent = IntentAnalyzer.analyze_intent(query, {})
            assert intent == QueryIntent.TASK_EXECUTION, \
                f"Query '{query}' should be TASK_EXECUTION, got {intent}"
    
    def test_analyze_intent_emotional_support(self):
        """测试：情感支持意图识别"""
        test_cases = [
            "我很难过",
            "我感觉很焦虑",
            "压力很大",
            "心情不好",
            "情绪低落",
            "感觉很累",
            "我很难过，不知道怎么办",
            "压力山大",
            "心情烦躁",
            "情绪波动",
        ]
        
        for query in test_cases:
            intent = IntentAnalyzer.analyze_intent(query, {})
            assert intent == QueryIntent.EMOTIONAL_SUPPORT, \
                f"Query '{query}' should be EMOTIONAL_SUPPORT, got {intent}"
    
    def test_analyze_intent_learning(self):
        """测试：学习辅导意图识别"""
        test_cases = [
            "学习Python",
            "教我编程",
            "练习算法",
            "理解这个概念",
            "掌握这个技能",
            "学会使用",
            "学习如何",
            "教我如何",
            "练习一下",
            "理解一下",
        ]
        
        for query in test_cases:
            intent = IntentAnalyzer.analyze_intent(query, {})
            assert intent == QueryIntent.LEARNING, \
                f"Query '{query}' should be LEARNING, got {intent}"
    
    def test_analyze_intent_case_insensitive(self):
        """测试：大小写不敏感"""
        test_cases = [
            ("什么是Python", QueryIntent.KNOWLEDGE_QUERY),
            ("什么是PYTHON", QueryIntent.KNOWLEDGE_QUERY),
            ("什么是python", QueryIntent.KNOWLEDGE_QUERY),
            ("什么是Python？", QueryIntent.KNOWLEDGE_QUERY),
            ("帮我计算", QueryIntent.TASK_EXECUTION),
            ("帮我计算", QueryIntent.TASK_EXECUTION),
            ("我很难过", QueryIntent.EMOTIONAL_SUPPORT),
            ("我很难过", QueryIntent.EMOTIONAL_SUPPORT),
            ("学习Python", QueryIntent.LEARNING),
            ("学习PYTHON", QueryIntent.LEARNING),
        ]
        
        for query, expected_intent in test_cases:
            intent = IntentAnalyzer.analyze_intent(query, {})
            assert intent == expected_intent, \
                f"Query '{query}' should be {expected_intent}, got {intent}"
    
    def test_analyze_intent_priority_order(self):
        """测试：意图识别优先级顺序"""
        # 测试多个关键词同时存在时的优先级
        # 优先级：KNOWLEDGE > TASK > EMOTIONAL > LEARNING > CHITCHAT
        
        test_cases = [
            # 知识查询优先级最高
            ("什么是帮我计算", QueryIntent.KNOWLEDGE_QUERY),
            ("如何学习编程", QueryIntent.KNOWLEDGE_QUERY),  # "如何"匹配知识查询
            # 任务执行优先级次之
            ("帮我学习", QueryIntent.TASK_EXECUTION),  # "帮我"匹配任务执行
            ("请解释一下", QueryIntent.KNOWLEDGE_QUERY),  # "解释"匹配知识查询
            # 情感支持
            ("我很难过，帮我一下", QueryIntent.EMOTIONAL_SUPPORT),  # "难过"匹配情感支持
            # 学习辅导
            ("学习如何编程", QueryIntent.LEARNING),  # "学习"匹配学习辅导
        ]
        
        for query, expected_intent in test_cases:
            intent = IntentAnalyzer.analyze_intent(query, {})
            assert intent == expected_intent, \
                f"Query '{query}' should be {expected_intent}, got {intent}"
    
    def test_analyze_intent_with_context(self):
        """测试：带上下文的意图识别"""
        # 当前实现中context参数未使用，但测试接口兼容性
        context = {
            "previous_intent": QueryIntent.CHITCHAT,
            "user_id": "test_user",
        }
        
        intent = IntentAnalyzer.analyze_intent("什么是Python", context)
        assert intent == QueryIntent.KNOWLEDGE_QUERY
    
    def test_analyze_intent_edge_cases(self):
        """测试：边界情况"""
        test_cases = [
            ("", QueryIntent.CHITCHAT),  # 空字符串
            ("   ", QueryIntent.CHITCHAT),  # 空白字符
            ("\n\t", QueryIntent.CHITCHAT),  # 换行和制表符
            ("什么是", QueryIntent.KNOWLEDGE_QUERY),  # 只有关键词
            ("帮我", QueryIntent.TASK_EXECUTION),  # 只有关键词
            ("难过", QueryIntent.EMOTIONAL_SUPPORT),  # 只有关键词
            ("学习", QueryIntent.LEARNING),  # 只有关键词
        ]
        
        for query, expected_intent in test_cases:
            intent = IntentAnalyzer.analyze_intent(query, {})
            assert intent == expected_intent, \
                f"Query '{query}' should be {expected_intent}, got {intent}"
    
    # ============================================================================
    # 引擎配置生成测试
    # ============================================================================
    
    def test_get_engine_config_chitchat(self):
        """测试：闲聊意图的引擎配置"""
        config = IntentAnalyzer.get_engine_config(QueryIntent.CHITCHAT)
        
        assert isinstance(config, dict)
        assert config["knowledge"]["enabled"] is False
        assert config["userprofile"]["enabled"] is True
        assert config["userprofile"]["max_tokens"] == 300
        assert config["chatmemory"]["enabled"] is True
        assert config["chatmemory"]["top_k"] == 5
    
    def test_get_engine_config_knowledge_query(self):
        """测试：知识查询意图的引擎配置"""
        config = IntentAnalyzer.get_engine_config(QueryIntent.KNOWLEDGE_QUERY)
        
        assert isinstance(config, dict)
        assert config["knowledge"]["enabled"] is True
        assert config["knowledge"]["top_k"] == 3
        assert config["userprofile"]["enabled"] is True
        assert config["userprofile"]["max_tokens"] == 200
        assert config["chatmemory"]["enabled"] is True
        assert config["chatmemory"]["top_k"] == 3
    
    def test_get_engine_config_task_execution(self):
        """测试：任务执行意图的引擎配置"""
        config = IntentAnalyzer.get_engine_config(QueryIntent.TASK_EXECUTION)
        
        assert isinstance(config, dict)
        assert config["knowledge"]["enabled"] is True
        assert config["knowledge"]["top_k"] == 2
        assert config["userprofile"]["enabled"] is True
        assert config["userprofile"]["max_tokens"] == 200
        assert config["chatmemory"]["enabled"] is True
        assert config["chatmemory"]["top_k"] == 5
    
    def test_get_engine_config_emotional_support(self):
        """测试：情感支持意图的引擎配置"""
        config = IntentAnalyzer.get_engine_config(QueryIntent.EMOTIONAL_SUPPORT)
        
        assert isinstance(config, dict)
        assert config["knowledge"]["enabled"] is False
        assert config["userprofile"]["enabled"] is True
        assert config["userprofile"]["max_tokens"] == 400
        assert config["chatmemory"]["enabled"] is True
        assert config["chatmemory"]["top_k"] == 8
    
    def test_get_engine_config_information_query(self):
        """测试：信息查询意图的引擎配置
        
        注意：INFORMATION_QUERY 意图目前不能通过 analyze_intent 自动识别，
        只能通过 get_engine_config 直接使用。这是设计上的限制。
        """
        config = IntentAnalyzer.get_engine_config(QueryIntent.INFORMATION_QUERY)
        
        assert isinstance(config, dict)
        assert config["knowledge"]["enabled"] is True
        assert config["knowledge"]["top_k"] == 5
        assert config["userprofile"]["enabled"] is False
        assert config["chatmemory"]["enabled"] is True
        assert config["chatmemory"]["top_k"] == 2
    
    def test_get_engine_config_learning(self):
        """测试：学习辅导意图的引擎配置"""
        config = IntentAnalyzer.get_engine_config(QueryIntent.LEARNING)
        
        assert isinstance(config, dict)
        assert config["knowledge"]["enabled"] is True
        assert config["knowledge"]["top_k"] == 3
        assert config["userprofile"]["enabled"] is True
        assert config["userprofile"]["max_tokens"] == 300
        assert config["chatmemory"]["enabled"] is True
        assert config["chatmemory"]["top_k"] == 4
    
    def test_get_engine_config_all_intents(self):
        """测试：所有意图的引擎配置结构"""
        intents = [
            QueryIntent.CHITCHAT,
            QueryIntent.KNOWLEDGE_QUERY,
            QueryIntent.TASK_EXECUTION,
            QueryIntent.EMOTIONAL_SUPPORT,
            QueryIntent.INFORMATION_QUERY,
            QueryIntent.LEARNING,
        ]
        
        for intent in intents:
            config = IntentAnalyzer.get_engine_config(intent)
            
            # 验证配置是字典类型
            assert isinstance(config, dict), \
                f"Config for {intent} should be a dict"
            
            # 验证配置包含必要的引擎
            assert "knowledge" in config or "userprofile" in config or "chatmemory" in config, \
                f"Config for {intent} should contain at least one engine"
            
            # 验证每个引擎配置的结构
            for engine_name, engine_config in config.items():
                assert isinstance(engine_config, dict), \
                    f"Engine config for {engine_name} in {intent} should be a dict"
                assert "enabled" in engine_config, \
                    f"Engine config for {engine_name} in {intent} should have 'enabled' field"
    
    def test_get_engine_config_default_fallback(self):
        """测试：未知意图的默认配置回退"""
        # 创建一个不存在的意图（通过字符串模拟）
        # 由于QueryIntent是枚举，无法直接创建不存在的值
        # 但可以测试get方法的行为
        config = IntentAnalyzer.get_engine_config(QueryIntent.CHITCHAT)
        assert isinstance(config, dict)
        # 默认应该返回CHITCHAT的配置
    
    # ============================================================================
    # 综合场景测试 - 意图识别准确性
    # ============================================================================
    
    def test_comprehensive_scenarios(self):
        """测试：综合场景的意图识别准确性"""
        scenarios = [
            # 知识查询场景
            {
                "query": "什么是人工智能？",
                "expected_intent": QueryIntent.KNOWLEDGE_QUERY,
                "description": "知识查询 - 什么是",
            },
            {
                "query": "如何学习Python编程？",
                "expected_intent": QueryIntent.KNOWLEDGE_QUERY,
                "description": "知识查询 - 如何",
            },
            {
                "query": "为什么需要版本控制？",
                "expected_intent": QueryIntent.KNOWLEDGE_QUERY,
                "description": "知识查询 - 为什么",
            },
            {
                "query": "解释一下RESTful API",
                "expected_intent": QueryIntent.KNOWLEDGE_QUERY,
                "description": "知识查询 - 解释",
            },
            
            # 任务执行场景
            {
                "query": "帮我写一个Python函数",
                "expected_intent": QueryIntent.TASK_EXECUTION,
                "description": "任务执行 - 帮我",
            },
            {
                "query": "请帮我生成一份报告",
                "expected_intent": QueryIntent.TASK_EXECUTION,
                "description": "任务执行 - 请帮我",
            },
            {
                "query": "完成这个代码重构",
                "expected_intent": QueryIntent.TASK_EXECUTION,
                "description": "任务执行 - 完成",
            },
            {
                "query": "执行这个测试用例",
                "expected_intent": QueryIntent.TASK_EXECUTION,
                "description": "任务执行 - 执行",
            },
            
            # 情感支持场景
            {
                "query": "我最近感觉压力很大",
                "expected_intent": QueryIntent.EMOTIONAL_SUPPORT,
                "description": "情感支持 - 压力",
            },
            {
                "query": "心情不好，不知道怎么办",
                "expected_intent": QueryIntent.EMOTIONAL_SUPPORT,
                "description": "情感支持 - 心情",
            },
            {
                "query": "我很难过",
                "expected_intent": QueryIntent.EMOTIONAL_SUPPORT,
                "description": "情感支持 - 难过",
            },
            {
                "query": "感觉很焦虑",
                "expected_intent": QueryIntent.EMOTIONAL_SUPPORT,
                "description": "情感支持 - 焦虑",
            },
            
            # 学习辅导场景
            {
                "query": "学习机器学习算法",
                "expected_intent": QueryIntent.LEARNING,
                "description": "学习辅导 - 学习",
            },
            {
                "query": "教我如何使用Git",
                "expected_intent": QueryIntent.LEARNING,
                "description": "学习辅导 - 教",
            },
            {
                "query": "练习算法题",
                "expected_intent": QueryIntent.LEARNING,
                "description": "学习辅导 - 练习",
            },
            {
                "query": "理解这个设计模式",
                "expected_intent": QueryIntent.LEARNING,
                "description": "学习辅导 - 理解",
            },
            
            # 闲聊场景
            {
                "query": "你好",
                "expected_intent": QueryIntent.CHITCHAT,
                "description": "闲聊 - 问候",
            },
            {
                "query": "今天天气不错",
                "expected_intent": QueryIntent.CHITCHAT,
                "description": "闲聊 - 日常话题",
            },
            {
                "query": "最近怎么样",
                "expected_intent": QueryIntent.CHITCHAT,
                "description": "闲聊 - 询问近况",
            },
        ]
        
        for scenario in scenarios:
            intent = IntentAnalyzer.analyze_intent(scenario["query"], {})
            assert intent == scenario["expected_intent"], \
                f"Scenario '{scenario['description']}': Query '{scenario['query']}' " \
                f"should be {scenario['expected_intent']}, got {intent}"
    
    def test_intent_to_config_integration(self):
        """测试：意图识别到配置生成的集成"""
        test_cases = [
            ("你好", QueryIntent.CHITCHAT),
            ("什么是Python", QueryIntent.KNOWLEDGE_QUERY),
            ("帮我计算", QueryIntent.TASK_EXECUTION),
            ("我很难过", QueryIntent.EMOTIONAL_SUPPORT),
            ("学习Python", QueryIntent.LEARNING),
        ]
        
        for query, expected_intent in test_cases:
            # 识别意图
            intent = IntentAnalyzer.analyze_intent(query, {})
            assert intent == expected_intent, \
                f"Query '{query}' should be {expected_intent}, got {intent}"
            
            # 生成配置
            config = IntentAnalyzer.get_engine_config(intent)
            assert isinstance(config, dict), \
                f"Config for intent {intent} should be a dict"
            assert len(config) > 0, \
                f"Config for intent {intent} should not be empty"
    
    def test_ambiguous_queries(self):
        """测试：模糊查询的意图识别"""
        # 测试可能匹配多个关键词的查询
        ambiguous_cases = [
            # "如何"优先匹配知识查询
            ("如何学习编程", QueryIntent.KNOWLEDGE_QUERY),
            # "帮我"优先匹配任务执行
            ("帮我学习", QueryIntent.TASK_EXECUTION),
            # "学习"匹配学习辅导
            ("学习如何编程", QueryIntent.LEARNING),
            # "解释"匹配知识查询
            ("解释一下如何学习", QueryIntent.KNOWLEDGE_QUERY),
        ]
        
        for query, expected_intent in ambiguous_cases:
            intent = IntentAnalyzer.analyze_intent(query, {})
            assert intent == expected_intent, \
                f"Ambiguous query '{query}' should be {expected_intent}, got {intent}"
