#!/usr/bin/env python3
"""
直接使用腾讯SDK原生代码测试AI大模型音色
排除封装层的影响
"""
import sys
import os
from pathlib import Path

# 添加项目路径
backend_dir = Path(__file__).parent.parent  # backend/
project_root = backend_dir.parent  # CozyChat/
sys.path.insert(0, str(backend_dir))  # 添加 backend/ 到 sys.path
os.chdir(str(backend_dir))  # 切换到 backend/ 目录

# 加载环境变量
from app.config.config import settings

# 导入腾讯SDK
from tencent_speech_sdk import credential, speech_synthesizer_ws

print("=" * 60)
print("腾讯SDK原生代码测试 - AI大模型音色")
print("=" * 60)
print()

# 配置信息
APPID = settings.tencent_app_id
SECRET_ID = settings.tencent_secret_id
SECRET_KEY = settings.tencent_secret_key

print(f"配置信息：")
print(f"  APPID: {APPID}")
print(f"  SECRET_ID: {SECRET_ID[:10]}...")
print(f"  SECRET_KEY: {SECRET_KEY[:10]}...")
print()

# 测试文本
TEST_TEXT = "你好，这是腾讯AI大模型语音合成测试。"

# AI大模型音色配置
VOICE_CONFIGS = [
    (101001, "", "AI女声 (ai_female)"),
    (101002, "", "AI男声 (ai_male)"),
    (101003, "", "AI旁白 (ai_narrator)"),
]

print(f"测试文本: {TEST_TEXT}")
print()


class SimpleListener(speech_synthesizer_ws.SpeechSynthesisListener):
    """简单的监听器"""
    
    def __init__(self, voice_name):
        self.voice_name = voice_name
        self.audio_chunks = []
        self.error = None
        self.success = False
    
    def on_synthesis_start(self, session_id):
        print(f"  [开始] session_id={session_id}")
    
    def on_synthesis_end(self):
        print(f"  [结束] 总音频大小: {sum(len(c) for c in self.audio_chunks)} bytes")
        self.success = True
    
    def on_audio_result(self, audio_bytes):
        self.audio_chunks.append(audio_bytes)
        print(f"  [音频] 收到 {len(audio_bytes)} bytes")
    
    def on_text_result(self, response):
        pass
    
    def on_synthesis_fail(self, response):
        code = response.get("code", "unknown")
        message = response.get("message", "Unknown error")
        self.error = f"Code: {code}, Message: {message}"
        print(f"  [失败] {self.error}")


def test_voice(voice_type, fast_voice_type, voice_name):
    """测试单个音色"""
    print("-" * 60)
    print(f"测试音色: {voice_name}")
    print(f"  VoiceType: {voice_type}")
    print(f"  FastVoiceType: '{fast_voice_type}'")
    print()
    
    # 创建凭证
    cred = credential.Credential(SECRET_ID, SECRET_KEY)
    
    # 创建监听器
    listener = SimpleListener(voice_name)
    
    # 创建合成器
    synthesizer = speech_synthesizer_ws.SpeechSynthesizer(
        APPID,
        cred,
        listener
    )
    
    # 配置参数
    synthesizer.set_text(TEST_TEXT)
    synthesizer.set_voice_type(voice_type)
    synthesizer.set_fast_voice_type(fast_voice_type)
    synthesizer.set_codec("mp3")
    synthesizer.set_sample_rate(16000)
    synthesizer.set_speed(0)  # 腾讯SDK使用-2到2的范围
    synthesizer.set_volume(0)
    synthesizer.set_enable_subtitle(False)
    
    # 开始合成
    try:
        synthesizer.start()
        synthesizer.wait()
        
        if listener.success:
            total_size = sum(len(c) for c in listener.audio_chunks)
            print(f"✅ 合成成功！总音频大小: {total_size} bytes")
            
            # 保存音频
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / f"tencent_raw_sdk_{voice_type}.mp3"
            with open(output_file, "wb") as f:
                for chunk in listener.audio_chunks:
                    f.write(chunk)
            print(f"✅ 音频已保存: {output_file}")
            return True
        elif listener.error:
            print(f"❌ 合成失败: {listener.error}")
            return False
        else:
            print(f"❌ 合成失败: 未知错误（没有成功也没有错误回调）")
            return False
    
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("开始测试")
    print("=" * 60)
    print()
    
    results = []
    
    for voice_type, fast_voice_type, voice_name in VOICE_CONFIGS:
        success = test_voice(voice_type, fast_voice_type, voice_name)
        results.append((voice_name, success))
        print()
    
    print("=" * 60)
    print("测试汇总")
    print("=" * 60)
    for voice_name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{status} - {voice_name}")
    
    success_count = sum(1 for _, s in results if s)
    total_count = len(results)
    print()
    print(f"总计: {success_count}/{total_count} 测试通过")
    
    if success_count < total_count:
        print()
        print("💡 提示：如果测试失败，可能的原因：")
        print("  1. 资源包未生效（等待15分钟后重试）")
        print("  2. 资源包未绑定到当前AppID")
        print("  3. AI大模型语音合成服务未开通")
        print("  4. 需要在控制台进行额外配置")
        print()
        print("  建议：对比控制台的调用参数和本脚本的参数")
        print("  控制台地址：https://console.cloud.tencent.com/tts")


if __name__ == "__main__":
    main()

