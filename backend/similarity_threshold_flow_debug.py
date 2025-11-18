#!/usr/bin/env python3
"""
测试similarity_threshold的完整流程
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.personality.manager import PersonalityManager
from app.core.personality.models import Personality

def test_similarity_threshold_flow():
    """测试similarity_threshold从配置到使用的完整流程"""
    
    print("=" * 60)
    print("测试 similarity_threshold 完整流程")
    print("=" * 60)
    
    # 1. 创建PersonalityManager
    print("\n1. 创建PersonalityManager...")
    manager = PersonalityManager()
    
    # 2. 获取personality
    print("\n2. 获取health_assistant personality...")
    personality = manager.get_personality("health_assistant")
    
    if not personality:
        print("❌ Personality not found!")
        return
    
    print(f"✅ Personality loaded: {personality.name}")
    
    # 3. 检查memory配置
    print("\n3. 检查memory配置...")
    print(f"   memory.enabled: {personality.memory.enabled}")
    print(f"   memory.retrieval: {personality.memory.retrieval}")
    print(f"   memory.retrieval.similarity_threshold: {personality.memory.retrieval.similarity_threshold}")
    print(f"   memory.retrieval.similarity_threshold type: {type(personality.memory.retrieval.similarity_threshold)}")
    
    # 4. 检查MemoryRetrieval对象
    print("\n4. 检查MemoryRetrieval对象...")
    retrieval = personality.memory.retrieval
    print(f"   retrieval object: {retrieval}")
    print(f"   retrieval type: {type(retrieval)}")
    print(f"   retrieval.similarity_threshold: {retrieval.similarity_threshold}")
    print(f"   retrieval.similarity_threshold type: {type(retrieval.similarity_threshold)}")
    
    # 5. 检查是否有默认值问题
    print("\n5. 检查MemoryRetrieval默认值...")
    from app.core.personality.models import MemoryRetrieval
    default_retrieval = MemoryRetrieval()
    print(f"   MemoryRetrieval默认值: {default_retrieval.similarity_threshold}")
    
    # 6. 模拟orchestrator中的使用
    print("\n6. 模拟orchestrator中的使用...")
    memory_config = personality.memory
    similarity_threshold = memory_config.retrieval.similarity_threshold
    print(f"   memory_config.retrieval.similarity_threshold: {similarity_threshold}")
    print(f"   similarity_threshold type: {type(similarity_threshold)}")
    
    # 7. 检查是否有dataclass的问题
    print("\n7. 检查dataclass字段...")
    import dataclasses
    fields = dataclasses.fields(retrieval)
    for field in fields:
        print(f"   {field.name}: {getattr(retrieval, field.name)} (type: {type(getattr(retrieval, field.name))})")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_similarity_threshold_flow()

