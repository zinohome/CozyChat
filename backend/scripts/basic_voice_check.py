#!/usr/bin/env python3
"""测试基础音色（非AI大模型）"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.config.config import settings
from tencent_speech_sdk import credential, speech_synthesizer_ws

print("=" * 60)
print("测试基础音色（VoiceType 0-5）")
print("=" * 60)
print()

class SimpleListener(speech_synthesizer_ws.SpeechSynthesisListener):
    def __init__(self):
        self.success = False
        self.error = None
        self.audio_size = 0
    
    def on_synthesis_start(self, session_id):
        print(f"✅ 开始合成: {session_id}")
    
    def on_synthesis_end(self):
        print(f"✅ 合成结束: 总音频 {self.audio_size} bytes")
        self.success = True
    
    def on_audio_result(self, audio_bytes):
        self.audio_size += len(audio_bytes)
    
    def on_synthesis_fail(self, response):
        self.error = f"Code: {response.get('code')}, Msg: {response.get('message')}"
        print(f"❌ 合成失败: {self.error}")

# 测试基础音色
BASIC_VOICES = [
    (0, "女声"),
    (1, "男声"),
]

for voice_type, voice_name in BASIC_VOICES:
    print(f"\n测试: {voice_name} (VoiceType={voice_type})")
    print("-" * 60)
    
    cred = credential.Credential(settings.tencent_secret_id, settings.tencent_secret_key)
    listener = SimpleListener()
    synthesizer = speech_synthesizer_ws.SpeechSynthesizer(
        settings.tencent_app_id,
        cred,
        listener
    )
    
    synthesizer.set_text("你好，这是基础音色测试。")
    synthesizer.set_voice_type(voice_type)
    synthesizer.set_codec("mp3")
    synthesizer.set_sample_rate(16000)
    
    synthesizer.start()
    synthesizer.wait()
    
    if listener.success:
        print(f"✅✅✅ 基础音色 {voice_name} 成功！")
    else:
        print(f"❌❌❌ 基础音色 {voice_name} 失败: {listener.error}")

print("\n" + "=" * 60)
print("如果基础音色成功，说明是AI大模型音色的配置问题")
print("如果基础音色也失败，说明是更基础的配置问题")
print("=" * 60)

