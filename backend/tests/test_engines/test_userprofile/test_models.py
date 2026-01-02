"""
UserProfile引擎模型单元测试

测试UserProfile和ProfileUpdateRequest模型
"""

# 标准库
from typing import Dict, Any

# 第三方库
import pytest

# 本地库
from app.engines.userprofile.models import UserProfile, ProfileUpdateRequest


class TestUserProfile:
    """UserProfile模型测试类"""
    
    def test_user_profile_creation(self):
        """测试：创建UserProfile实例"""
        profile = UserProfile(
            user_id="test-user-123",
            profile_text="User profile text",
            token_size=3
        )
        
        assert profile.user_id == "test-user-123"
        assert profile.profile_text == "User profile text"
        assert profile.token_size == 3
        assert profile.profile_data is None
    
    def test_user_profile_with_profile_data(self):
        """测试：创建UserProfile实例（包含profile_data）"""
        profile_data = {
            "interests": ["Python", "AI"],
            "age": 30
        }
        
        profile = UserProfile(
            user_id="test-user-123",
            profile_text="User profile text",
            token_size=3,
            profile_data=profile_data
        )
        
        assert profile.profile_data == profile_data
    
    def test_user_profile_to_dict(self):
        """测试：UserProfile转换为字典"""
        profile = UserProfile(
            user_id="test-user-123",
            profile_text="User profile text",
            token_size=3
        )
        
        result = profile.to_dict()
        
        assert isinstance(result, dict)
        assert result["user_id"] == "test-user-123"
        assert result["profile_text"] == "User profile text"
        assert result["token_size"] == 3
        assert result["profile_data"] == {}
    
    def test_user_profile_to_dict_with_profile_data(self):
        """测试：UserProfile转换为字典（包含profile_data）"""
        profile_data = {
            "interests": ["Python", "AI"],
            "age": 30
        }
        
        profile = UserProfile(
            user_id="test-user-123",
            profile_text="User profile text",
            token_size=3,
            profile_data=profile_data
        )
        
        result = profile.to_dict()
        
        assert result["profile_data"] == profile_data
    
    def test_user_profile_empty_profile_data(self):
        """测试：UserProfile（空profile_data）"""
        profile = UserProfile(
            user_id="test-user-123",
            profile_text="",
            token_size=0,
            profile_data=None
        )
        
        result = profile.to_dict()
        
        assert result["profile_data"] == {}


class TestProfileUpdateRequest:
    """ProfileUpdateRequest模型测试类"""
    
    def test_profile_update_request_creation(self):
        """测试：创建ProfileUpdateRequest实例"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        
        request = ProfileUpdateRequest(
            user_id="test-user-123",
            messages=messages
        )
        
        assert request.user_id == "test-user-123"
        assert request.messages == messages
    
    def test_profile_update_request_to_dict(self):
        """测试：ProfileUpdateRequest转换为字典"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        
        request = ProfileUpdateRequest(
            user_id="test-user-123",
            messages=messages
        )
        
        result = request.to_dict()
        
        assert isinstance(result, dict)
        assert result["user_id"] == "test-user-123"
        assert result["messages"] == messages
    
    def test_profile_update_request_empty_messages(self):
        """测试：ProfileUpdateRequest（空消息列表）"""
        request = ProfileUpdateRequest(
            user_id="test-user-123",
            messages=[]
        )
        
        assert request.messages == []
        result = request.to_dict()
        assert result["messages"] == []
