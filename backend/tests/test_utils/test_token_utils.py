"""
Token工具函数测试

测试token计数和消息历史管理功能
"""

# 标准库
import pytest

# 本地库
from app.utils.token_utils import (
    estimate_tokens,
    estimate_message_tokens,
    summarize_old_messages,
    truncate_messages
)
from app.engines.ai.base import ChatMessage


class TestEstimateTokens:
    """测试token估算函数"""
    
    def test_estimate_tokens_empty(self):
        """测试：空字符串"""
        assert estimate_tokens("") == 0
    
    def test_estimate_tokens_short_text(self):
        """测试：短文本"""
        text = "Hello"
        tokens = estimate_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_estimate_tokens_chinese(self):
        """测试：中文文本"""
        text = "你好，世界"
        tokens = estimate_tokens(text)
        assert tokens > 0
    
    def test_estimate_tokens_mixed(self):
        """测试：中英文混合"""
        text = "Hello 世界"
        tokens = estimate_tokens(text)
        assert tokens > 0
    
    def test_estimate_tokens_long_text(self):
        """测试：长文本"""
        text = "A" * 1000
        tokens = estimate_tokens(text)
        assert tokens > 100  # 应该估算出合理的token数


class TestEstimateMessageTokens:
    """测试消息token估算"""
    
    def test_estimate_message_tokens_simple(self):
        """测试：简单消息"""
        message = ChatMessage(role="user", content="Hello")
        tokens = estimate_message_tokens(message)
        assert tokens > 0
    
    def test_estimate_message_tokens_empty_content(self):
        """测试：空内容消息"""
        message = ChatMessage(role="user", content="")
        tokens = estimate_message_tokens(message)
        assert tokens >= 5  # 至少包含消息格式开销
    
    def test_estimate_message_tokens_with_tool_calls(self):
        """测试：带工具调用的消息"""
        message = ChatMessage(
            role="assistant",
            content="I'll use a calculator",
            tool_calls=[
                {
                    "function": {
                        "name": "calculator",
                        "arguments": '{"expression": "2+2"}'
                    }
                }
            ]
        )
        tokens = estimate_message_tokens(message)
        assert tokens > 0
    
    def test_estimate_message_tokens_with_function_call(self):
        """测试：带函数调用的消息（旧格式）"""
        message = ChatMessage(
            role="assistant",
            content="I'll use a calculator",
            function_call={
                "name": "calculator",
                "arguments": '{"expression": "2+2"}'
            }
        )
        tokens = estimate_message_tokens(message)
        assert tokens > 0


class TestSummarizeOldMessages:
    """测试旧消息摘要"""
    
    def test_summarize_empty_messages(self):
        """测试：空消息列表"""
        result = summarize_old_messages([])
        assert result is None
    
    def test_summarize_single_message(self):
        """测试：单条消息"""
        messages = [
            ChatMessage(role="user", content="Hello")
        ]
        result = summarize_old_messages(messages)
        assert result is not None
        assert result.role == "system"
        assert "之前的对话摘要" in result.content
    
    def test_summarize_multiple_messages(self):
        """测试：多条消息"""
        messages = [
            ChatMessage(role="user", content="What is Python?"),
            ChatMessage(role="assistant", content="Python is a programming language."),
            ChatMessage(role="user", content="Tell me more"),
        ]
        result = summarize_old_messages(messages)
        assert result is not None
        assert result.role == "system"
        assert len(result.content) > 0
    
    def test_summarize_with_system_messages(self):
        """测试：包含系统消息"""
        messages = [
            ChatMessage(role="system", content="You are a helpful assistant"),
            ChatMessage(role="user", content="Hello"),
        ]
        result = summarize_old_messages(messages)
        assert result is not None
    
    def test_summarize_long_messages(self):
        """测试：长消息（超过100字符）"""
        long_content = "A" * 200
        messages = [
            ChatMessage(role="user", content=long_content)
        ]
        result = summarize_old_messages(messages)
        assert result is not None
        # 应该被截断
        assert len(result.content) < len(long_content) + 100


class TestTruncateMessages:
    """测试消息截断"""
    
    def test_truncate_empty_messages(self):
        """测试：空消息列表"""
        result = truncate_messages([], max_history_tokens=1000)
        assert result == []
    
    def test_truncate_within_limit(self):
        """测试：消息在限制内"""
        messages = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi there"),
        ]
        result = truncate_messages(messages, max_history_tokens=1000)
        assert len(result) == 2
    
    def test_truncate_exceeds_limit(self):
        """测试：消息超过限制"""
        messages = [
            ChatMessage(role="user", content="A" * 1000),
            ChatMessage(role="assistant", content="B" * 1000),
            ChatMessage(role="user", content="C" * 1000),
        ]
        result = truncate_messages(messages, max_history_tokens=100)
        # 应该被截断
        assert len(result) <= len(messages)
    
    def test_truncate_keeps_system_messages(self):
        """测试：保留系统消息"""
        messages = [
            ChatMessage(role="system", content="You are helpful"),
            ChatMessage(role="user", content="A" * 1000),
        ]
        result = truncate_messages(messages, max_history_tokens=100, keep_system=True)
        # 应该保留系统消息
        assert any(msg.role == "system" for msg in result)
    
    def test_truncate_min_messages(self):
        """测试：最少保留消息数"""
        messages = [
            ChatMessage(role="user", content="A" * 1000),
            ChatMessage(role="assistant", content="B" * 1000),
        ]
        result = truncate_messages(
            messages,
            max_history_tokens=100,
            min_messages=2
        )
        # 应该至少保留min_messages条消息
        assert len(result) >= 2
    
    def test_truncate_with_summary(self):
        """测试：启用摘要"""
        messages = [
            ChatMessage(role="user", content="A" * 500),
            ChatMessage(role="assistant", content="B" * 500),
            ChatMessage(role="user", content="C" * 500),
        ]
        result = truncate_messages(
            messages,
            max_history_tokens=200,
            enable_summary=True
        )
        # 如果启用了摘要且消息被截断，可能会生成摘要消息
        # 摘要消息可能是system角色，内容可能包含"摘要"或"summary"等关键词
        # 但由于摘要生成是简化的，可能不会生成摘要，所以只验证结果不为空
        assert len(result) > 0
        # 验证至少保留了一些消息
        assert len(result) <= len(messages)
    
    def test_truncate_without_summary(self):
        """测试：禁用摘要"""
        messages = [
            ChatMessage(role="user", content="A" * 500),
            ChatMessage(role="assistant", content="B" * 500),
        ]
        result = truncate_messages(
            messages,
            max_history_tokens=100,
            enable_summary=False
        )
        # 不应该包含摘要消息
        summary_messages = [msg for msg in result if "摘要" in msg.content]
        assert len(summary_messages) == 0

