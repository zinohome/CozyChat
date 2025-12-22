"""记忆管理引擎模块

提供向量数据库记忆存储和检索功能
"""

from .base import MemoryEngineBase
# ChromaDB 已注释（默认使用 qdrant），使用条件导入
try:
    from .chromadb_engine import ChromaDBMemoryEngine
except ImportError:
    ChromaDBMemoryEngine = None  # type: ignore
from .qdrant_engine import QdrantMemoryEngine
# Cognee 引擎（条件导入，使用 SDK）
try:
    from .cognee_engine import CogneeMemoryEngine
    COGNEE_AVAILABLE = True
except ImportError:
    CogneeMemoryEngine = None  # type: ignore
    COGNEE_AVAILABLE = False
from .manager import MemoryManager, get_memory_manager
from .models import Memory, MemoryType

__all__ = [
    "MemoryEngineBase",
    "QdrantMemoryEngine",
    "MemoryManager",
    "get_memory_manager",
    "Memory",
    "MemoryType",
]
# 如果 ChromaDB 可用，添加到 __all__
if ChromaDBMemoryEngine is not None:
    __all__.append("ChromaDBMemoryEngine")
# 如果 Cognee 可用，添加到 __all__
if COGNEE_AVAILABLE and CogneeMemoryEngine is not None:
    __all__.append("CogneeMemoryEngine")

