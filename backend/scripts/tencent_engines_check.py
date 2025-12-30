#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
腾讯语音引擎测试脚本

用于快速验证腾讯ASR和TTS引擎的基本功能
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 导入配置（这会自动加载.env文件）
from app.config.config import settings
from app.engines.voice.stt import STTEngineFactory
from app.engines.voice.tts import TTSEngineFactory
from app.utils.logger import logger


async def test_stt_health_check():
    """测试ASR健康检查"""
    print("\n" + "="*50)
    print("测试 1: 腾讯ASR健康检查")
    print("="*50)
    
    try:
        engine = STTEngineFactory.create_engine("tencent")
        result = await engine.health_check()
        
        if result:
            print("✅ ASR引擎健康检查通过")
        else:
            print("❌ ASR引擎健康检查失败")
        
        return result
    except Exception as e:
        print(f"❌ ASR引擎初始化失败: {e}")
        return False


async def test_tts_health_check():
    """测试TTS健康检查"""
    print("\n" + "="*50)
    print("测试 2: 腾讯TTS健康检查")
    print("="*50)
    
    try:
        engine = TTSEngineFactory.create_engine("tencent")
        result = await engine.health_check()
        
        if result:
            print("✅ TTS引擎健康检查通过")
        else:
            print("❌ TTS引擎健康检查失败")
        
        return result
    except Exception as e:
        print(f"❌ TTS引擎初始化失败: {e}")
        return False


async def test_tts_synthesize():
    """测试TTS合成"""
    print("\n" + "="*50)
    print("测试 3: 腾讯TTS文本合成（AI大模型音色）")
    print("="*50)
    
    try:
        engine = TTSEngineFactory.create_engine("tencent")
        
        text = "你好，这是腾讯AI大模型语音合成测试。"
        print(f"合成文本: {text}")
        print(f"使用音色: ai_female (AI女声)")
        
        audio_data = await engine.synthesize(text, voice="ai_female", speed=1.0)
        
        print(f"✅ 合成成功，音频大小: {len(audio_data)} 字节")
        
        # 保存音频文件
        output_file = "/tmp/tencent_tts_test.mp3"
        with open(output_file, "wb") as f:
            f.write(audio_data)
        print(f"✅ 音频已保存到: {output_file}")
        
        return True
    except Exception as e:
        print(f"❌ TTS合成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tts_stream_synthesize():
    """测试TTS流式合成"""
    print("\n" + "="*50)
    print("测试 4: 腾讯TTS流式合成（AI大模型音色）")
    print("="*50)
    
    try:
        engine = TTSEngineFactory.create_engine("tencent")
        
        text = "这是一段较长的文本，用于测试AI大模型流式合成功能。AI大模型音色更加自然，接近真人发音。"
        print(f"合成文本: {text}")
        print(f"使用音色: ai_male (AI男声)")
        
        chunks = []
        chunk_count = 0
        
        async for audio_chunk in engine.stream_synthesize(text, voice="ai_male", speed=1.0):
            chunk_count += 1
            chunks.append(audio_chunk)
            print(f"收到音频块 {chunk_count}: {len(audio_chunk)} 字节")
        
        total_size = sum(len(chunk) for chunk in chunks)
        print(f"✅ 流式合成完成，共 {chunk_count} 个音频块，总大小: {total_size} 字节")
        
        # 保存音频文件
        output_file = "/tmp/tencent_tts_stream_test.mp3"
        with open(output_file, "wb") as f:
            for chunk in chunks:
                f.write(chunk)
        print(f"✅ 音频已保存到: {output_file}")
        
        return True
    except Exception as e:
        print(f"❌ TTS流式合成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tts_voices():
    """测试TTS音色列表"""
    print("\n" + "="*50)
    print("测试 5: 腾讯TTS音色列表")
    print("="*50)
    
    try:
        engine = TTSEngineFactory.create_engine("tencent")
        voices = engine.get_available_voices()
        
        print(f"✅ 可用音色: {', '.join(voices)}")
        return True
    except Exception as e:
        print(f"❌ 获取音色列表失败: {e}")
        return False


def check_environment():
    """检查环境变量"""
    print("\n" + "="*50)
    print("环境检查")
    print("="*50)
    
    # 从settings对象读取配置
    configs = {
        "TENCENT_APP_ID": settings.tencent_app_id,
        "TENCENT_SECRET_ID": settings.tencent_secret_id,
        "TENCENT_SECRET_KEY": settings.tencent_secret_key
    }
    
    missing_vars = []
    for var_name, value in configs.items():
        if value:
            print(f"✅ {var_name}: {'*' * 10} (已设置)")
        else:
            print(f"❌ {var_name}: 未设置")
            missing_vars.append(var_name)
    
    if missing_vars:
        print(f"\n⚠️  缺少环境变量: {', '.join(missing_vars)}")
        print("\n请在 .env 文件中设置这些变量：")
        for var in missing_vars:
            print(f"  {var}=your_value")
        print(f"\n提示：从 backend 目录运行时，会自动查找父目录的 .env 文件")
        return False
    
    print("\n提示：此测试使用AI大模型音色（需要大模型语音合成资源包）")
    print("购买链接：https://console.cloud.tencent.com/tts")
    
    return True


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("腾讯语音引擎测试")
    print("="*60)
    
    # 检查环境变量
    if not check_environment():
        print("\n❌ 环境检查失败，请配置环境变量后重试")
        return
    
    # 运行测试
    results = []
    
    # 测试ASR健康检查
    results.append(("ASR健康检查", await test_stt_health_check()))
    
    # 测试TTS健康检查
    results.append(("TTS健康检查", await test_tts_health_check()))
    
    # 测试TTS音色列表
    results.append(("TTS音色列表", await test_tts_voices()))
    
    # 测试TTS合成
    results.append(("TTS文本合成", await test_tts_synthesize()))
    
    # 测试TTS流式合成
    results.append(("TTS流式合成", await test_tts_stream_synthesize()))
    
    # 显示测试结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "-"*60)
    print(f"总计: {passed + failed} 个测试，{passed} 个通过，{failed} 个失败")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 所有测试通过！腾讯语音引擎工作正常。")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查配置和日志。")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被中断")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()

