"""
人格系统模块

提供人格配置、管理和编排功能
"""

from .models import Personality, PersonalityTraits, AIConfig, MemoryConfig, ToolConfig, VoiceConfig
from .loader import PersonalityLoader
from .manager import PersonalityManager
from .orchestrator import Orchestrator

__all__ = [
    "Personality",
    "PersonalityTraits",
    "AIConfig",
    "MemoryConfig",
    "ToolConfig",
    "VoiceConfig",
    "PersonalityLoader",
    "PersonalityManager",
    "Orchestrator",
]

