"""
三大人格化引擎集成测试

测试Knowledge、UserProfile、ChatMemory三大引擎的功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# 设置环境变量（在导入app模块之前）
import os
os.environ["KNOWLEDGE_ENGINE_PROVIDER"] = "cognee"
os.environ["COGNEE_API_URL"] = "http://192.168.66.11:8000"
os.environ["COGNEE_API_TOKEN"] = ""

os.environ["USERPROFILE_ENGINE_PROVIDER"] = "memobase"
os.environ["MEMOBASE_PROJECT_URL"] = "http://192.168.66.11:8019"
os.environ["MEMOBASE_API_KEY"] = "secret"

os.environ["CHATMEMORY_ENGINE_PROVIDER"] = "mem0"
os.environ["MEM0_API_URL"] = "http://192.168.66.11:8888"
os.environ["MEM0_API_KEY"] = ""


async def test_knowledge_engine():
    """测试Knowledge Engine (Cognee)"""
    print("\n" + "="*60)
    print("测试 1: Knowledge Engine (Cognee)")
    print("="*60)
    
    try:
        from app.engines.knowledge.factory import KnowledgeEngineFactory
        
        # 创建引擎
        engine = KnowledgeEngineFactory.create_engine(
            provider="cognee",
            config={
                "api_url": "http://192.168.66.11:8000",
                "api_token": None
            }
        )
        
        # 初始化
        print("⏳ 正在初始化Knowledge Engine...")
        init_result = await engine.initialize()
        if init_result:
            print("✅ Knowledge Engine 初始化成功")
        else:
            print("❌ Knowledge Engine 初始化失败")
            return False
        
        # 健康检查
        print("⏳ 执行健康检查...")
        health = await engine.health_check()
        if health:
            print("✅ Knowledge Engine 健康检查通过")
        else:
            print("❌ Knowledge Engine 健康检查失败")
            return False
        
        # 搜索知识
        print("⏳ 测试知识搜索...")
        results = await engine.search_knowledge(
            query="什么是AI",
            dataset_names=["default"],
            top_k=3
        )
        print(f"✅ 搜索到 {len(results)} 条知识")
        for i, result in enumerate(results[:3], 1):
            print(f"  {i}. {result.get('content', '')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Knowledge Engine 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_userprofile_engine():
    """测试UserProfile Engine (Memobase)"""
    print("\n" + "="*60)
    print("测试 2: UserProfile Engine (Memobase)")
    print("="*60)
    
    try:
        from app.engines.userprofile.factory import UserProfileEngineFactory
        
        # 创建引擎
        engine = UserProfileEngineFactory.create_engine(
            provider="memobase",
            config={
                "project_url": "http://192.168.66.11:8019",
                "api_key": "secret"
            }
        )
        
        # 初始化
        print("⏳ 正在初始化UserProfile Engine...")
        init_result = await engine.initialize()
        if init_result:
            print("✅ UserProfile Engine 初始化成功")
        else:
            print("❌ UserProfile Engine 初始化失败")
            return False
        
        # 健康检查
        print("⏳ 执行健康检查...")
        health = await engine.health_check()
        if health:
            print("✅ UserProfile Engine 健康检查通过")
        else:
            print("❌ UserProfile Engine 健康检查失败")
            return False
        
        # 获取用户画像
        test_user_id = "test_user_001"
        print(f"⏳ 获取用户画像 (user_id: {test_user_id})...")
        profile = await engine.get_profile(
            user_id=test_user_id,
            max_token_size=300
        )
        print(f"✅ 用户画像获取成功")
        print(f"  - user_id: {profile.get('user_id')}")
        print(f"  - token_size: {profile.get('token_size')}")
        print(f"  - profile: {profile.get('profile_text', '')[:100]}...")
        
        # 更新用户画像
        print(f"⏳ 更新用户画像...")
        test_messages = [
            {"role": "user", "content": "我喜欢编程"},
            {"role": "assistant", "content": "很好！编程是一项很有价值的技能。"}
        ]
        update_result = await engine.update_profile(
            user_id=test_user_id,
            messages=test_messages
        )
        if update_result:
            print("✅ 用户画像更新成功")
        else:
            print("⚠️ 用户画像更新失败（可能是新用户）")
        
        return True
        
    except Exception as e:
        print(f"❌ UserProfile Engine 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_chatmemory_engine():
    """测试ChatMemory Engine (Mem0)"""
    print("\n" + "="*60)
    print("测试 3: ChatMemory Engine (Mem0)")
    print("="*60)
    
    try:
        from app.engines.chatmemory.factory import ChatMemoryEngineFactory
        
        # 创建引擎
        engine = ChatMemoryEngineFactory.create_engine(
            provider="mem0",
            config={
                "api_url": "http://192.168.66.11:8888",
                "api_key": None
            }
        )
        
        # 初始化
        print("⏳ 正在初始化ChatMemory Engine...")
        init_result = await engine.initialize()
        if init_result:
            print("✅ ChatMemory Engine 初始化成功")
        else:
            print("❌ ChatMemory Engine 初始化失败")
            return False
        
        # 健康检查
        print("⏳ 执行健康检查...")
        health = await engine.health_check()
        if health:
            print("✅ ChatMemory Engine 健康检查通过")
        else:
            print("❌ ChatMemory Engine 健康检查失败")
            return False
        
        # 添加记忆
        test_user_id = "test_user_001"
        test_session_id = "test_session_001"
        print(f"⏳ 添加会话记忆...")
        test_messages = [
            {"role": "user", "content": "今天天气很好"},
            {"role": "assistant", "content": "是的，适合出去走走。"}
        ]
        try:
            memory_id = await engine.add_memory(
                user_id=test_user_id,
                session_id=test_session_id,
                messages=test_messages
            )
            print(f"✅ 记忆添加成功 (id: {memory_id})")
        except Exception as e:
            print(f"⚠️ 记忆添加失败: {e}")
        
        # 搜索记忆
        print(f"⏳ 搜索会话记忆...")
        memories = await engine.search_memories(
            query="天气",
            user_id=test_user_id,
            session_id=test_session_id,
            top_k=5
        )
        print(f"✅ 搜索到 {len(memories)} 条记忆")
        for i, memory in enumerate(memories[:3], 1):
            print(f"  {i}. {memory.get('memory', '')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ ChatMemory Engine 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_context_service():
    """测试ContextService集成"""
    print("\n" + "="*60)
    print("测试 4: ContextService 集成测试")
    print("="*60)
    
    try:
        from app.services.context.context_service_new import ContextServiceNew
        
        # 获取ContextService实例
        print("⏳ 创建ContextService实例...")
        context_service = ContextServiceNew.get_instance()
        
        # 初始化
        print("⏳ 初始化ContextService...")
        init_result = await context_service.initialize()
        if init_result:
            print("✅ ContextService 初始化成功")
        else:
            print("❌ ContextService 初始化失败")
            return False
        
        # 健康检查
        print("⏳ 执行健康检查...")
        health_status = await context_service.health_check()
        print(f"✅ 健康检查结果:")
        print(f"  - Knowledge: {'✅' if health_status.get('knowledge') else '❌'}")
        print(f"  - UserProfile: {'✅' if health_status.get('userprofile') else '❌'}")
        print(f"  - ChatMemory: {'✅' if health_status.get('chatmemory') else '❌'}")
        print(f"  - Overall: {'✅' if health_status.get('overall') else '❌'}")
        
        # 构建个性化上下文
        test_user_id = "test_user_001"
        test_session_id = "test_session_001"
        test_query = "给我讲讲人工智能"
        
        print(f"\n⏳ 构建个性化上下文...")
        print(f"  - user_id: {test_user_id}")
        print(f"  - session_id: {test_session_id}")
        print(f"  - query: {test_query}")
        
        context = await context_service.build_personalized_context(
            user_id=test_user_id,
            session_id=test_session_id,
            query=test_query,
            dataset_names=["default"]
        )
        
        print(f"✅ 上下文构建成功:")
        print(f"  - 意图: {context.get('intent')}")
        print(f"  - 知识数量: {len(context.get('knowledge', []))}")
        print(f"  - 画像: {bool(context.get('profile', {}).get('profile_text'))}")
        print(f"  - 记忆数量: {len(context.get('memories', []))}")
        
        # 更新用户数据
        print(f"\n⏳ 更新用户数据...")
        update_messages = [
            {"role": "user", "content": test_query},
            {"role": "assistant", "content": "人工智能是一个广泛的领域..."}
        ]
        update_result = await context_service.update_user_data(
            user_id=test_user_id,
            session_id=test_session_id,
            messages=update_messages
        )
        print(f"✅ 用户数据更新结果:")
        print(f"  - UserProfile: {'✅' if update_result.get('userprofile_updated') else '❌'}")
        print(f"  - ChatMemory: {'✅' if update_result.get('chatmemory_updated') else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ ContextService 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n")
    print("="*60)
    print("🚀 三大人格化引擎集成测试")
    print("="*60)
    print(f"服务器地址: 192.168.66.11")
    print(f"  - Cognee (Knowledge): :8000")
    print(f"  - Memobase (UserProfile): :8019")
    print(f"  - Mem0 (ChatMemory): :8888")
    print("="*60)
    
    results = {
        "knowledge": False,
        "userprofile": False,
        "chatmemory": False,
        "context_service": False
    }
    
    # 测试各个引擎
    results["knowledge"] = await test_knowledge_engine()
    results["userprofile"] = await test_userprofile_engine()
    results["chatmemory"] = await test_chatmemory_engine()
    results["context_service"] = await test_context_service()
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name.ljust(20)}: {status}")
    
    print("-"*60)
    print(f"总计: {success_count}/{total_count} 测试通过")
    
    if success_count == total_count:
        print("\n🎉 所有测试通过！三大引擎集成成功！")
        return 0
    else:
        print(f"\n⚠️ {total_count - success_count} 个测试失败，请检查配置和服务状态")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

