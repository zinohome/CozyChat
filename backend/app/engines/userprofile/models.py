"""
用户画像引擎数据模型
"""

# 标准库
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class UserProfile:
    """用户画像
    
    Attributes:
        user_id: 用户ID
        profile_text: 画像文本
        token_size: token数量
        profile_data: 结构化画像数据（可选）
    """
    user_id: str
    profile_text: str
    token_size: int
    profile_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict: 字典格式的画像
        """
        return {
            "user_id": self.user_id,
            "profile_text": self.profile_text,
            "token_size": self.token_size,
            "profile_data": self.profile_data or {}
        }


@dataclass
class ProfileUpdateRequest:
    """画像更新请求
    
    Attributes:
        user_id: 用户ID
        messages: 会话消息列表
    """
    user_id: str
    messages: list
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict: 字典格式的请求
        """
        return {
            "user_id": self.user_id,
            "messages": self.messages
        }

