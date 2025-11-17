#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
腾讯AI大模型音色测试脚本

测试大模型语音合成功能（需要购买大模型语音合成资源包）
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 导入配置（这会自动加载.env文件）
from app.config.config import settings
from app.engines.voice.tts import TTSEngineFactory
from app.utils.logger import logger


async def test_ai_voice_synthesis():
    """测试AI大模型音色合成"""
    print("\n" + "="*60)
    print("测试 腾讯AI大模型音色合成")
    print("="*60)
    
    try:
        engine = TTSEngineFactory.create_engine("tencent")
        
        # 测试文本
        text = "你好，我是腾讯云AI大模型音色，这是一段语音合成测试。"
        
        # AI音色列表
        ai_voices = [
            ("ai_female", "AI女声1号"),
            ("ai_male", "AI男声1号"),
            ("ai_narrator", "AI播音员"),
            ("ai_warm_female", "AI温暖女声"),
            ("ai_energetic", "AI活力女声"),
        ]
        
        print(f"\n合成文本: {text}\n")
        
        for voice_id, voice_name in ai_voices:
            print(f"\n{'='*50}")
            print(f"测试音色: {voice_name} ({voice_id})")
            print('='*50)
            
            try:
                # 使用流式合成（AI音色自动切换到WebSocket模式）
                chunks = []
                chunk_count = 0
                
                async for audio_chunk in engine.stream_synthesize(
                    text, 
                    voice=voice_id, 
                    speed=1.0
                ):
                    chunk_count += 1
                    chunks.append(audio_chunk)
                    print(f"  收到音频块 {chunk_count}: {len(audio_chunk)} 字节")
                
                # 合并音频
                audio_data = b"".join(chunks)
                
                # 保存音频文件
                output_file = f"/tmp/tencent_ai_{voice_id}.mp3"
                with open(output_file, "wb") as f:
                    f.write(audio_data)
                
                print(f"✅ {voice_name} 合成成功")
                print(f"   共 {chunk_count} 个音频块，总大小: {len(audio_data)} 字节")
                print(f"   音频已保存到: {output_file}")
                
            except Exception as e:
                print(f"❌ {voice_name} 合成失败: {e}")
                if "PkgExhausted" in str(e):
                    print("   提示：请确保您已购买大模型语音合成资源包")
                    print("   购买链接：https://console.cloud.tencent.com/tts")
        
        print("\n" + "="*60)
        print("测试完成")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_voice_type_direct():
    """直接使用VoiceType编号测试"""
    print("\n" + "="*60)
    print("测试 直接使用VoiceType编号")
    print("="*60)
    
    try:
        engine = TTSEngineFactory.create_engine("tencent")
        
        text = "测试使用VoiceType编号直接调用。"
        voice_type = 101001  # AI女声1号
        
        print(f"\n合成文本: {text}")
        print(f"VoiceType: {voice_type}\n")
        
        # 使用编号作为字符串
        audio_data = []
        async for chunk in engine.stream_synthesize(text, voice=str(voice_type)):
            audio_data.append(chunk)
        
        audio_data = b"".join(audio_data)
        
        output_file = f"/tmp/tencent_voice_{voice_type}.mp3"
        with open(output_file, "wb") as f:
            f.write(audio_data)
        
        print(f"✅ 合成成功，音频大小: {len(audio_data)} 字节")
        print(f"   音频已保存到: {output_file}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        if "PkgExhausted" in str(e):
            print("   提示：请确保您已购买大模型语音合成资源包")


def check_environment():
    """检查环境变量"""
    print("\n" + "="*60)
    print("环境检查")
    print("="*60)
    
    configs = {
        "TENCENT_APP_ID": settings.tencent_app_id,
        "TENCENT_SECRET_ID": settings.tencent_secret_id,
        "TENCENT_SECRET_KEY": settings.tencent_secret_key
    }
    
    all_set = True
    for var_name, value in configs.items():
        if value:
            print(f"✅ {var_name}: {'*' * 10} (已设置)")
        else:
            print(f"❌ {var_name}: 未设置")
            all_set = False
    
    if not all_set:
        print("\n❌ 环境检查失败，请配置环境变量后重试")
        return False
    
    print("\n提示：此测试需要购买【大模型语音合成】资源包")
    print("购买链接：https://console.cloud.tencent.com/tts")
    print("预付费包价格：100万字符 = 650元")
    
    return True


async def main():
    """主函数"""
    print("\n" + "="*70)
    print("腾讯云AI大模型音色测试")
    print("="*70)
    
    # 检查环境变量
    if not check_environment():
        return
    
    # 测试AI音色
    await test_ai_voice_synthesis()
    
    # 测试直接使用VoiceType编号
    await test_voice_type_direct()
    
    print("\n" + "="*70)
    print("所有测试完成")
    print("="*70)
    print("\n说明：")
    print("1. 基础音色(0-5)使用【基础语音合成】资源包")
    print("2. AI大模型音色(101xxx)使用【大模型语音合成】资源包")
    print("3. AI大模型音色自动使用WebSocket模式")
    print("4. 两种资源包是独立的，需要分别购买")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被中断")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()

