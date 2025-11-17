# 只使用官方语音SDK方案分析

## 1. 重要发现

**可以只使用 `tencentcloud-speech-sdk-python`！**

官方语音SDK实际上提供了**完整的解决方案**，既支持一句话识别，也支持实时识别和TTS。

## 2. 官方语音SDK功能清单

### 2.1 ASR（语音识别）

#### 2.1.1 FlashRecognizer - 一句话识别（HTTP）

**位置**: `example/tencentcloud-speech-sdk-python/asr/flash_recognizer.py`

**特点**:
- ✅ HTTP POST请求
- ✅ 一句话识别（非实时）
- ✅ 同步API，转换简单
- ✅ 适合短音频识别

**使用示例**:
```python
from common import credential
from asr import flash_recognizer

cred = credential.Credential(SECRET_ID, SECRET_KEY)
recognizer = flash_recognizer.FlashRecognizer(APPID, cred)

req = flash_recognizer.FlashRecognitionRequest("16k_zh")
req.set_voice_format("wav")
req.set_filter_modal(1)
req.set_filter_punc(1)

# 读取音频文件
with open("audio.wav", 'rb') as f:
    data = f.read()
    # 执行识别（同步，返回结果）
    result = recognizer.recognize(req, data)
    resp = json.loads(result)
    print(resp["flash_result"][0]["text"])
```

#### 2.1.2 SpeechRecognizer - 实时识别（WebSocket）

**位置**: `example/tencentcloud-speech-sdk-python/asr/speech_recognizer.py`

**特点**:
- ✅ WebSocket实时识别
- ✅ 支持长音频
- ✅ 流式识别
- ❌ 同步API，转换复杂

**使用示例**:
```python
from common import credential
from asr import speech_recognizer

cred = credential.Credential(SECRET_ID, SECRET_KEY)
recognizer = speech_recognizer.SpeechRecognizer(
    APPID, cred, "16k_zh", listener
)
recognizer.start()
recognizer.write(audio_chunk)
recognizer.stop()
```

### 2.2 TTS（语音合成）

#### 2.2.1 SpeechSynthesizer - HTTP流式合成

**位置**: `example/tencentcloud-speech-sdk-python/tts/speech_synthesizer.py`

**特点**:
- ✅ HTTP POST流式合成
- ✅ 同步API，转换简单
- ✅ 适合一次性合成

**使用示例**:
```python
from common import credential
from tts import speech_synthesizer

cred = credential.Credential(SECRET_ID, SECRET_KEY)
synthesizer = speech_synthesizer.SpeechSynthesizer(
    APPID, cred, voice_type, listener
)
synthesizer.set_codec("mp3")
synthesizer.set_sample_rate(16000)
synthesizer.synthesis(text)  # 同步调用
```

#### 2.2.2 SpeechSynthesizer (WebSocket) - WebSocket流式合成

**位置**: `example/tencentcloud-speech-sdk-python/tts/speech_synthesizer_ws.py`

**特点**:
- ✅ WebSocket流式合成
- ✅ 支持实时合成
- ❌ 同步API，转换复杂

#### 2.2.3 FlowingSpeechSynthesizer - 流式文本合成

**位置**: `example/tencentcloud-speech-sdk-python/tts/flowing_speech_synthesizer.py`

**特点**:
- ✅ 支持分块输入文本
- ✅ 流式合成
- ❌ 同步API，转换复杂

## 3. 方案对比

### 3.1 使用通用SDK（tencentcloud-sdk-python）

**需要安装**: `pip install tencentcloud-sdk-python`

**功能**:
- ✅ 一句话识别（HTTP）
- ❌ 不支持实时识别
- ❌ 不支持流式TTS

### 3.2 只使用官方语音SDK（tencentcloud-speech-sdk-python）

**需要安装**: 手动集成（GitHub下载）

**功能**:
- ✅ 一句话识别（FlashRecognizer，HTTP）
- ✅ 实时识别（SpeechRecognizer，WebSocket）
- ✅ HTTP流式TTS（SpeechSynthesizer）
- ✅ WebSocket流式TTS（SpeechSynthesizer WS）
- ✅ 流式文本TTS（FlowingSpeechSynthesizer）

## 4. 推荐方案：只使用官方语音SDK

### 4.1 优势

1. **功能完整**
   - ✅ 一句话识别（FlashRecognizer）
   - ✅ 实时识别（SpeechRecognizer）
   - ✅ 各种TTS方式

2. **统一SDK**
   - ✅ 只需要维护一个SDK
   - ✅ 统一的认证方式
   - ✅ 统一的配置管理

3. **官方维护**
   - ✅ 腾讯官方GitHub仓库
   - ✅ 官方推荐的语音SDK

4. **减少依赖**
   - ✅ 不需要安装通用SDK
   - ✅ 减少依赖冲突风险

### 4.2 实现策略

**根据场景选择不同的识别器**：

1. **短音频/一句话识别** → 使用 `FlashRecognizer`
   ```python
   # 简单、快速、HTTP请求
   result = recognizer.recognize(req, audio_data)
   ```

2. **长音频/实时识别** → 使用 `SpeechRecognizer`
   ```python
   # 复杂但支持实时，WebSocket
   recognizer.start()
   recognizer.write(audio_chunk)
   ```

## 5. 实现方案

### 5.1 ASR引擎实现

```python
class TencentSTTEngine(STTEngineBase):
    """腾讯ASR引擎 - 只使用官方语音SDK"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 读取配置
        api_config = config.get("api", {})
        self.app_id = api_config.get("app_id")
        self.secret_id = api_config.get("secret_id")
        self.secret_key = api_config.get("secret_key")
        
        # 创建凭证
        cred = credential.Credential(self.secret_id, self.secret_key)
        self.credential = cred
        
        # 识别模式：flash（一句话）或 realtime（实时）
        self.recognition_mode = config.get("recognition_mode", "flash")
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """语音转文本"""
        
        # 根据音频长度或配置选择识别器
        use_realtime = kwargs.get("realtime", False) or len(audio_data) > 1024 * 1024  # 1MB
        
        if use_realtime:
            # 使用实时识别（WebSocket）
            return await self._transcribe_realtime(audio_data, language)
        else:
            # 使用一句话识别（HTTP）
            return await self._transcribe_flash(audio_data, language)
    
    async def _transcribe_flash(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> str:
        """使用FlashRecognizer进行一句话识别"""
        from asr import flash_recognizer
        
        # 创建识别器
        recognizer = flash_recognizer.FlashRecognizer(
            self.app_id,
            self.credential
        )
        
        # 创建请求
        req = flash_recognizer.FlashRecognitionRequest(
            self._get_engine_type(language)
        )
        req.set_voice_format(self._detect_format(audio_data))
        req.set_filter_modal(self.config.get("filter_modal", 1))
        req.set_filter_punc(self.config.get("filter_punc", 1))
        req.set_filter_dirty(self.config.get("filter_dirty", 1))
        
        # 在线程中运行同步调用
        loop = asyncio.get_event_loop()
        result_json = await loop.run_in_executor(
            self._executor,
            recognizer.recognize,
            req,
            audio_data
        )
        
        # 解析结果
        resp = json.loads(result_json)
        if resp.get("code") != 0:
            raise Exception(f"Recognition failed: {resp.get('message')}")
        
        # 提取文本
        flash_result = resp.get("flash_result", [])
        if flash_result:
            return flash_result[0].get("text", "")
        return ""
    
    async def _transcribe_realtime(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> str:
        """使用SpeechRecognizer进行实时识别"""
        from asr import speech_recognizer
        
        # 创建结果收集器
        collector = ResultCollector()
        
        # 创建识别器
        recognizer = speech_recognizer.SpeechRecognizer(
            self.app_id,
            self.credential,
            self._get_engine_type(language),
            collector
        )
        
        # 配置参数
        recognizer.set_filter_modal(self.config.get("filter_modal", 1))
        recognizer.set_filter_punc(self.config.get("filter_punc", 1))
        recognizer.set_filter_dirty(self.config.get("filter_dirty", 1))
        recognizer.set_need_vad(self.config.get("need_vad", 1))
        recognizer.set_voice_format(self._get_format_code(audio_data))
        
        # 在线程中运行识别
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor,
            self._realtime_recognize_sync,
            recognizer,
            audio_data,
            collector
        )
        
        # 等待识别完成
        if collector.completed.wait(timeout=30):
            if collector.error:
                raise Exception(collector.error)
            return collector.final_text
        else:
            raise TimeoutError("Recognition timeout")
```

### 5.2 TTS引擎实现

```python
class TencentTTSEngine(TTSEngineBase):
    """腾讯TTS引擎 - 只使用官方语音SDK"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 读取配置
        api_config = config.get("api", {})
        self.app_id = api_config.get("app_id")
        self.secret_id = api_config.get("secret_id")
        self.secret_key = api_config.get("secret_key")
        
        # 创建凭证
        cred = credential.Credential(self.secret_id, self.secret_key)
        self.credential = cred
        
        # TTS模式：http 或 websocket
        self.tts_mode = config.get("tts_mode", "http")
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        **kwargs: Any
    ) -> bytes:
        """文本转语音"""
        
        if self.tts_mode == "websocket":
            # 使用WebSocket合成（复杂）
            return await self._synthesize_websocket(text, voice, speed)
        else:
            # 使用HTTP合成（简单）
            return await self._synthesize_http(text, voice, speed)
    
    async def _synthesize_http(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None
    ) -> bytes:
        """使用HTTP流式合成"""
        from tts import speech_synthesizer
        
        # 创建音频收集器
        collector = AudioCollector()
        
        # 创建合成器
        synthesizer = speech_synthesizer.SpeechSynthesizer(
            self.app_id,
            self.credential,
            self._get_voice_type(voice),
            collector
        )
        synthesizer.set_codec(self.config.get("codec", "mp3"))
        synthesizer.set_sample_rate(self.config.get("sample_rate", 16000))
        synthesizer.set_speed(self._convert_speed(speed))
        synthesizer.set_volume(self.config.get("volume", 0))
        
        # 在线程中运行同步调用
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor,
            synthesizer.synthesis,
            text
        )
        
        # 等待合成完成
        if collector.completed.wait(timeout=30):
            if collector.error:
                raise Exception(collector.error)
            return collector.audio_data
        else:
            raise TimeoutError("Synthesis timeout")
```

## 6. 依赖管理

### 6.1 移除通用SDK

```txt
# backend/requirements/base.txt

# 移除这行
# tencentcloud-sdk-python==3.0.1489
```

### 6.2 添加语音SDK依赖

```txt
# backend/requirements/base.txt

# 腾讯语音SDK依赖
websocket-client==0.48  # WebSocket客户端（必须0.48版本）
requests>=2.28.0        # HTTP请求
```

### 6.3 SDK集成

**方案A：直接使用example目录（推荐）**

```python
import sys
sys.path.append("example/tencentcloud-speech-sdk-python")

from common import credential
from asr import flash_recognizer, speech_recognizer
from tts import speech_synthesizer, speech_synthesizer_ws
```

**方案B：复制到项目目录**

```bash
# 将SDK复制到backend/app/engines/voice/tencent_sdk/
cp -r example/tencentcloud-speech-sdk-python backend/app/engines/voice/tencent_sdk/
```

## 7. 配置更新

### 7.1 STT配置

```yaml
# backend/config/voice/stt.yaml

engines:
  stt:
    tencent:
      provider: "tencent"
      # 识别模式：flash（一句话）或 realtime（实时）
      recognition_mode: "flash"  # 默认使用一句话识别
      model: "16k_zh"
      language: "zh-CN"
      # ASR参数
      filter_modal: 1
      filter_punc: 1
      filter_dirty: 1
      need_vad: 1
      voice_format: "wav"
      # API配置
      api:
        app_id: null  # 从环境变量获取
        secret_id: null
        secret_key: null
        timeout: 30
        max_retries: 2
        retry_delay: 1.0
```

### 7.2 TTS配置

```yaml
# backend/config/voice/tts.yaml

engines:
  tts:
    tencent:
      provider: "tencent"
      # TTS模式：http 或 websocket
      tts_mode: "http"  # 默认使用HTTP
      voice_type: 0
      codec: "mp3"
      sample_rate: 16000
      speed: 0
      volume: 0
      # API配置
      api:
        app_id: null
        secret_id: null
        secret_key: null
        timeout: 30
        max_retries: 2
        retry_delay: 1.0
```

## 8. 总结

### 8.1 优势

✅ **功能完整**：一句话识别 + 实时识别 + 各种TTS  
✅ **统一SDK**：只需要维护一个SDK  
✅ **减少依赖**：不需要安装通用SDK  
✅ **官方维护**：腾讯官方推荐的语音SDK  

### 8.2 实现要点

1. **根据场景选择识别器**：
   - 短音频 → FlashRecognizer（HTTP，简单）
   - 长音频/实时 → SpeechRecognizer（WebSocket，复杂）

2. **异步转换**：
   - FlashRecognizer：简单（HTTP请求）
   - SpeechRecognizer：复杂（WebSocket + 线程同步）

3. **配置灵活**：
   - 支持自动选择识别模式
   - 支持手动指定模式

### 8.3 推荐

**只使用官方语音SDK（tencentcloud-speech-sdk-python）**：
- ✅ 功能完整
- ✅ 统一维护
- ✅ 减少依赖
- ✅ 官方推荐

---

**文档版本**: v1.0  
**创建日期**: 2024-12-19

