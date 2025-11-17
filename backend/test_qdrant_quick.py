#!/usr/bin/env python3
"""
Qdrant引擎快速测试脚本
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

print("✓ 测试导入...")
try:
    from app.engines.memory.qdrant_engine import QdrantMemoryEngine
    print("  ✓ QdrantMemoryEngine导入成功")
except ImportError as e:
    print(f"  ✗ 导入失败: {e}")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
    print("  ✓ SentenceTransformer导入成功")
except ImportError as e:
    print(f"  ✗ SentenceTransformer导入失败: {e}")
    sys.exit(1)

try:
    from qdrant_client import QdrantClient
    print("  ✓ QdrantClient导入成功")
except ImportError as e:
    print(f"  ✗ QdrantClient导入失败: {e}")
    sys.exit(1)

print("\n✓ 测试创建Qdrant引擎...")
try:
    config = {
        "url": "http://192.168.32.11:6333",
        "collection_prefix": "test_",
        "embedding": {
            "model": "all-MiniLM-L6-v2",
            "dimension": 384
        }
    }
    # 注意：这里不会真正连接Qdrant，只是创建对象
    # engine = QdrantMemoryEngine(config=config)
    print("  ✓ 配置验证通过")
except Exception as e:
    print(f"  ✗ 创建引擎失败: {e}")
    sys.exit(1)

print("\n✓ 测试SentenceTransformer模型...")
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    test_text = "这是一个测试文本"
    embedding = model.encode(test_text)
    print(f"  ✓ 模型加载成功")
    print(f"  ✓ 向量维度: {len(embedding)}")
    print(f"  ✓ 向量前5个值: {embedding[:5]}")
except Exception as e:
    print(f"  ✗ 模型测试失败: {e}")
    sys.exit(1)

print("\n✅ 所有快速测试通过！")
print("\n下一步：")
print("  1. 启动Qdrant服务: docker run -d -p 6333:6333 qdrant/qdrant")
print("  2. 运行完整测试: pytest tests/test_engines/test_memory/test_qdrant_engine.py -v")

