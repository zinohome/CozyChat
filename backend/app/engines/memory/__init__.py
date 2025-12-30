"""记忆管理引擎模块

提供向量数据库记忆存储和检索功能

============================================================================
⚠️ DEPRECATED: 旧版Memory引擎（已废弃）
============================================================================
状态：已废弃，将在 v2.0 移除
创建时间：2024-XX-XX
废弃时间：2024-12-22
移除时间：2025-Q1

替代方案：使用三大人格化引擎系统
  - Knowledge Engine:   backend/app/engines/knowledge/
  - UserProfile Engine: backend/app/engines/userprofile/
  - ChatMemory Engine:  backend/app/engines/chatmemory/

详细信息：docs/reports/三大人格化引擎系统架构重构方案.md
============================================================================
"""

import warnings
warnings.warn(
    "MemoryManager and old memory engine are deprecated and will be removed in v2.0. "
    "Please use the new three-engine system (Knowledge + UserProfile + ChatMemory). "
    "See docs/reports/三大人格化引擎系统架构重构方案.md for migration guide.",
    DeprecationWarning,
    stacklevel=2
)

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

