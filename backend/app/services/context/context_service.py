"""
上下文服务（转发到新实现）

这个文件用于向后兼容，将导入转发到新的ContextServiceNew
"""

# ============================================================================
# 导入转发：context_service → context_service_new
# ============================================================================
# 新代码应直接导入：from app.services.context.context_service_new import ContextServiceNew
# 旧代码兼容：from app.services.context.context_service import ContextService
# ============================================================================

import warnings

# 发出废弃警告
warnings.warn(
    "Importing from context_service.py is deprecated. "
    "Please use 'from app.services.context.context_service_new import ContextServiceNew' instead.",
    DeprecationWarning,
    stacklevel=2
)

# 转发到新实现
from app.services.context.context_service_new import ContextServiceNew as ContextService

__all__ = ["ContextService"]

