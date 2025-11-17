"""
STT（语音转文本）引擎模块
"""

from .base import STTEngineBase, STTProvider
from .openai_stt import OpenAISTTEngine
from .tencent_stt import TencentSTTEngine
from .factory import STTEngineFactory

__all__ = [
    "STTEngineBase",
    "STTProvider",
    "OpenAISTTEngine",
    "TencentSTTEngine",
    "STTEngineFactory",
]

