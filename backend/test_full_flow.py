#!/usr/bin/env python3
"""
完整流程测试：从配置加载到memory检索
"""
import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.personality.manager import PersonalityManager
from app.engines.memory.manager import MemoryManager

async def test_full_flow():
    """测试完整流程"""
    
    print("=" * 60)
    print("完整流程测试：从配置加载到memory检索")
    print("=" * 60)
    
    # 1. 创建PersonalityManager（模拟chat.py中的调用）
    print("\n1. 创建PersonalityManager（模拟chat.py）...")
    personality_manager = PersonalityManager()
    
    # 2. 获取personality（模拟chat.py中的调用）
    print("\n2. 获取health_assistant personality...")
    personality = personality_manager.get_personality("health_assistant")
    
    if not personality:
        print("❌ Personality not found!")
        return
    
    print(f"✅ Personality loaded: {personality.name}")
    print(f"   personality.memory.retrieval.similarity_threshold: {personality.memory.retrieval.similarity_threshold}")
    
    # 3. 创建MemoryManager（模拟chat.py中的调用）
    print("\n3. 创建MemoryManager（模拟chat.py）...")
    memory_manager = MemoryManager()
    
    # 4. 模拟chat.py中的调用
    print("\n4. 模拟chat.py中的调用...")
    memory_config = personality.memory
    similarity_threshold = memory_config.retrieval.similarity_threshold
    
    print(f"   memory_config.retrieval.similarity_threshold: {similarity_threshold}")
    print(f"   similarity_threshold type: {type(similarity_threshold)}")
    print(f"   similarity_threshold value: {similarity_threshold}")
    
    if similarity_threshold != 0.3:
        print(f"\n❌ 问题：similarity_threshold不是0.3！实际值: {similarity_threshold}")
        print(f"   personality.memory.retrieval: {personality.memory.retrieval}")
        print(f"   personality.memory.retrieval type: {type(personality.memory.retrieval)}")
        return
    else:
        print(f"\n✅ similarity_threshold正确：{similarity_threshold}")
    
    # 5. 模拟调用retrieve_memories（不实际调用，只检查参数）
    print("\n5. 模拟调用retrieve_memories（检查参数）...")
    print(f"   将传递的similarity_threshold: {similarity_threshold}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_full_flow())

