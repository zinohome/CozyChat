"""
CozyChat Backend Application
"""

# 标准库
import os

# 禁用 ChromaDB 遥测（必须在导入任何 ChromaDB 模块之前）
# 设置环境变量和配置
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# 导入 chromadb 并配置（如果已安装）
try:
    import chromadb
    chromadb.configure(anonymized_telemetry=False)
except ImportError:
    # ChromaDB 未安装时忽略
    pass

__version__ = "0.1.0"


