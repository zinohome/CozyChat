# 腾讯语音SDK接入和实现方案

## 1. 方案概述

本文档描述如何将腾讯云语音SDK（ASR和TTS）接入到CozyChat项目中，实现语音识别和语音合成功能。

### 1.1 目标

- 实现腾讯ASR（自动语音识别）引擎，支持实时语音转文本
- 实现腾讯TTS（文本转语音）引擎，支持文本转语音和流式合成
- 与现有语音引擎架构无缝集成
- 保持与OpenAI引擎相同的接口规范

### 1.2 技术栈

- **腾讯SDK**: `tencentcloud-speech-sdk-python`（位于`example/`目录）
- **SDK依赖**: `websocket-client==0.48`, `requests`
- **项目架构**: 基于FastAPI的异步架构

## 2. 腾讯SDK分析

### 2.1 ASR（语音识别）SDK分析

#### 2.1.1 核心类：`SpeechRecognizer`

**位置**: `example/tencentcloud-speech-sdk-python/asr/speech_recognizer.py`

**特点**:
- 基于WebSocket的实时语音识别
- 使用监听器模式（Listener Pattern）处理回调
- 同步API（需要转换为异步）

**主要方法**:
```python
class SpeechRecognizer:
    def __init__(self, appid, credential, engine_model_type, listener)
    def start()  # 启动WebSocket连接
    def write(data: bytes)  # 发送音频数据
    def stop()  # 停止识别
```

**监听器接口**:
```python
class SpeechRecognitionListener:
    def on_recognition_start(self, response)  # 识别开始
    def on_sentence_begin(self, response)  # 句子开始
    def on_recognition_result_change(self, response)  # 识别结果变化
    def on_sentence_end(self, response)  # 句子结束
    def on_recognition_complete(self, response)  # 识别完成
    def on_fail(self, response)  # 识别失败
```

**配置参数**:
- `engine_model_type`: 引擎类型（如`"16k_zh"`）
- `filter_modal`: 过滤语气词（0/1）
- `filter_punc`: 过滤标点（0/1）
- `filter_dirty`: 过滤脏话（0/1）
- `need_vad`: 是否需要VAD（0/1）
- `voice_format`: 音频格式（1=PCM, 4=WAV等）
- `word_info`: 是否返回词级时间戳（0/1）

**识别结果格式**:
```python
{
    "code": 0,
    "message": "success",
    "voice_id": "xxx",
    "result": {
        "slice_type": 0/1/2,  # 0=句子开始, 1=中间结果, 2=句子结束
        "voice_text_str": "识别的文本",
        "word_list": [...]  # 词级信息（可选）
    },
    "final": 0/1  # 是否最终结果
}
```

#### 2.1.2 使用流程

1. 创建`Credential`对象（包含`secret_id`和`secret_key`）
2. 实现`SpeechRecognitionListener`监听器
3. 创建`SpeechRecognizer`实例并配置参数
4. 调用`start()`启动WebSocket连接
5. 循环调用`write()`发送音频数据块
6. 在监听器回调中处理识别结果
7. 调用`stop()`停止识别

### 2.2 TTS（语音合成）SDK分析

#### 2.2.1 核心类：`SpeechSynthesizer`（HTTP流式）

**位置**: `example/tencentcloud-speech-sdk-python/tts/speech_synthesizer.py`

**特点**:
- 基于HTTP POST的流式合成
- 使用监听器模式处理回调
- 同步API（需要转换为异步）

**主要方法**:
```python
class SpeechSynthesizer:
    def __init__(self, appid, credential, voice_type, listener)
    def set_codec(codec)  # 设置音频格式: "pcm"或"mp3"
    def set_sample_rate(rate)  # 设置采样率: 8000/16000
    def set_speed(speed)  # 设置语速: -2到2
    def set_volume(volume)  # 设置音量: -10到10
    def synthesis(text: str)  # 执行合成
```

**监听器接口**:
```python
class SpeechSynthesisListener:
    def on_message(self, response)  # 接收到音频数据块
    def on_complete(self, response)  # 合成完成
    def on_fail(self, response)  # 合成失败
```

#### 2.2.2 核心类：`SpeechSynthesizer`（WebSocket流式）

**位置**: `example/tencentcloud-speech-sdk-python/tts/speech_synthesizer_ws.py`

**特点**:
- 基于WebSocket的流式合成
- 支持更灵活的流式控制
- 同步API（需要转换为异步）

**主要方法**:
```python
class SpeechSynthesizer:
    def __init__(self, appid, credential, listener)
    def set_text(text)  # 设置要合成的文本
    def set_voice_type(voice_type)  # 设置音色类型
    def set_codec(codec)  # 设置音频格式
    def set_sample_rate(rate)  # 设置采样率
    def set_speed(speed)  # 设置语速
    def set_volume(volume)  # 设置音量
    def start()  # 启动WebSocket连接
    def wait()  # 等待合成完成
```

**监听器接口**:
```python
class SpeechSynthesisListener:
    def on_synthesis_start(self, session_id)  # 合成开始
    def on_audio_result(self, audio_bytes)  # 接收到音频数据
    def on_text_result(self, response)  # 接收到文本结果（字幕等）
    def on_synthesis_end(self)  # 合成结束
    def on_synthesis_fail(self, response)  # 合成失败
```

#### 2.2.3 配置参数

- `voice_type`: 音色类型（整数，如`101001`）
- `codec`: 音频格式（`"pcm"`或`"mp3"`）
- `sample_rate`: 采样率（`8000`或`16000`）
- `speed`: 语速（`-2`到`2`，默认`0`）
- `volume`: 音量（`-10`到`10`，默认`0`）

### 2.3 SDK依赖

```python
# 必需依赖
websocket-client==0.48  # WebSocket客户端（必须0.48版本）
requests  # HTTP请求
```

## 3. 实现方案

### 3.1 架构设计

#### 3.1.1 目录结构

```
backend/app/engines/voice/
├── stt/
│   ├── base.py              # STT基类（已存在）
│   ├── openai_stt.py        # OpenAI实现（已存在）
│   ├── tencent_stt.py       # 腾讯ASR实现（新增）
│   └── factory.py           # 工厂类（需更新）
├── tts/
│   ├── base.py              # TTS基类（已存在）
│   ├── openai_tts.py        # OpenAI实现（已存在）
│   ├── tencent_tts.py       # 腾讯TTS实现（新增）
│   └── factory.py           # 工厂类（需更新）
└── ...
```

#### 3.1.2 设计要点

1. **异步包装**: 腾讯SDK是同步的，需要使用`asyncio`包装为异步
2. **线程安全**: WebSocket操作需要在独立线程中运行，使用`asyncio.to_thread()`或`concurrent.futures.ThreadPoolExecutor`
3. **结果收集**: 使用`asyncio.Queue`或`threading.Event`收集识别/合成结果
4. **错误处理**: 统一异常处理和日志记录
5. **配置管理**: 从配置文件和环境变量读取配置

### 3.2 腾讯ASR引擎实现

#### 3.2.1 类设计

```python
class TencentSTTEngine(STTEngineBase):
    """腾讯ASR引擎
    
    使用腾讯云ASR SDK进行语音转文本
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化腾讯ASR引擎"""
        # 1. 调用基类初始化
        # 2. 读取配置（app_id, secret_id, secret_key）
        # 3. 创建Credential对象
        # 4. 初始化识别器配置
        
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """语音转文本（异步）"""
        # 1. 验证音频格式
        # 2. 创建监听器（收集结果）
        # 3. 创建识别器实例
        # 4. 在线程池中运行识别流程
        # 5. 等待识别完成并返回结果
        
    async def health_check(self) -> bool:
        """健康检查"""
        # 尝试创建一个测试识别器，检查配置是否正确
```

#### 3.2.2 实现细节

**1. 同步到异步转换**

使用`asyncio.to_thread()`或`ThreadPoolExecutor`在线程中运行同步代码：

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=5)

async def transcribe(self, audio_data: bytes, ...):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        self._transcribe_sync,
        audio_data,
        ...
    )
    return result
```

**2. 结果收集**

使用`asyncio.Queue`或`threading.Event`收集识别结果：

```python
class ResultCollector(SpeechRecognitionListener):
    def __init__(self):
        self.result_queue = asyncio.Queue()
        self.final_text = ""
        self.error = None
        self.completed = threading.Event()
    
    def on_recognition_result_change(self, response):
        # 收集中间结果
        text = response.get("result", {}).get("voice_text_str", "")
        if text:
            self.final_text = text
    
    def on_sentence_end(self, response):
        # 收集最终结果
        text = response.get("result", {}).get("voice_text_str", "")
        if text:
            self.final_text = text
    
    def on_recognition_complete(self, response):
        self.completed.set()
    
    def on_fail(self, response):
        self.error = response.get("message", "Unknown error")
        self.completed.set()
```

**3. 音频数据分块发送**

腾讯ASR需要分块发送音频数据（建议6400字节/块）：

```python
SLICE_SIZE = 6400

def _transcribe_sync(self, audio_data: bytes, ...):
    recognizer.start()
    try:
        # 分块发送音频数据
        offset = 0
        while offset < len(audio_data):
            chunk = audio_data[offset:offset + SLICE_SIZE]
            recognizer.write(chunk)
            offset += SLICE_SIZE
            time.sleep(0.02)  # 模拟实时发送间隔
    finally:
        recognizer.stop()
    
    # 等待识别完成
    collector.completed.wait(timeout=30)
    if collector.error:
        raise Exception(collector.error)
    return collector.final_text
```

**4. 配置映射**

将项目配置映射到腾讯SDK参数：

```python
# 语言代码映射
LANGUAGE_MAP = {
    "zh-CN": "16k_zh",
    "en-US": "16k_en",
    "zh": "16k_zh",
    "en": "16k_en",
}

# 音频格式映射
FORMAT_MAP = {
    "wav": 4,
    "pcm": 1,
    "mp3": 2,
}
```

### 3.3 腾讯TTS引擎实现

#### 3.3.1 类设计

```python
class TencentTTSEngine(TTSEngineBase):
    """腾讯TTS引擎
    
    使用腾讯云TTS SDK进行文本转语音
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化腾讯TTS引擎"""
        # 1. 调用基类初始化
        # 2. 读取配置（app_id, secret_id, secret_key）
        # 3. 创建Credential对象
        # 4. 初始化合成器配置
        
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        **kwargs: Any
    ) -> bytes:
        """文本转语音（异步）"""
        # 1. 验证文本
        # 2. 创建监听器（收集音频数据）
        # 3. 创建合成器实例（HTTP或WebSocket）
        # 4. 在线程池中运行合成流程
        # 5. 等待合成完成并返回音频数据
        
    async def stream_synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        **kwargs: Any
    ) -> AsyncIterator[bytes]:
        """流式文本转语音（异步生成器）"""
        # 1. 验证文本
        # 2. 创建监听器（流式收集音频数据）
        # 3. 创建WebSocket合成器实例
        # 4. 在线程池中运行合成流程
        # 5. 通过队列流式返回音频数据块
        
    def get_available_voices(self) -> List[str]:
        """获取可用的语音列表"""
        # 返回腾讯支持的音色类型列表
        
    async def health_check(self) -> bool:
        """健康检查"""
        # 尝试创建一个测试合成器，检查配置是否正确
```

#### 3.3.2 实现细节

**1. 非流式合成（synthesize）**

使用HTTP流式合成器：

```python
class AudioCollector(SpeechSynthesisListener):
    def __init__(self):
        self.audio_data = bytes()
        self.completed = threading.Event()
        self.error = None
    
    def on_message(self, response):
        data = response.get("data", b"")
        if data:
            self.audio_data += data
    
    def on_complete(self, response):
        self.completed.set()
    
    def on_fail(self, response):
        self.error = response.get("Message", "Unknown error")
        self.completed.set()

async def synthesize(self, text: str, ...):
    collector = AudioCollector()
    synthesizer = SpeechSynthesizer(
        app_id, credential, voice_type, collector
    )
    # 配置参数...
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        executor,
        synthesizer.synthesis,
        text
    )
    
    collector.completed.wait(timeout=30)
    if collector.error:
        raise Exception(collector.error)
    return collector.audio_data
```

**2. 流式合成（stream_synthesize）**

使用WebSocket流式合成器：

```python
class StreamAudioCollector(SpeechSynthesisListener):
    def __init__(self):
        self.audio_queue = asyncio.Queue()
        self.completed = threading.Event()
        self.error = None
    
    def on_audio_result(self, audio_bytes):
        # 将音频数据放入队列
        asyncio.run_coroutine_threadsafe(
            self.audio_queue.put(audio_bytes),
            asyncio.get_event_loop()
        )
    
    def on_synthesis_end(self):
        # 发送结束标记
        asyncio.run_coroutine_threadsafe(
            self.audio_queue.put(None),
            asyncio.get_event_loop()
        )
        self.completed.set()
    
    def on_synthesis_fail(self, response):
        self.error = response.get("message", "Unknown error")
        asyncio.run_coroutine_threadsafe(
            self.audio_queue.put(None),
            asyncio.get_event_loop()
        )
        self.completed.set()

async def stream_synthesize(self, text: str, ...):
    collector = StreamAudioCollector()
    synthesizer = SpeechSynthesizer(
        app_id, credential, collector
    )
    # 配置参数...
    
    # 在线程中启动合成
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        executor,
        self._stream_synthesize_sync,
        synthesizer,
        text
    )
    
    # 从队列中流式返回音频数据
    while True:
        chunk = await collector.audio_queue.get()
        if chunk is None:
            break
        yield chunk
    
    if collector.error:
        raise Exception(collector.error)
```

**3. 音色类型映射**

将项目配置的voice名称映射到腾讯的音色类型：

```python
VOICE_TYPE_MAP = {
    "亲和女声": 0,
    "亲和男声": 1,
    "成熟男声": 2,
    "活力男声": 3,
    "温暖女声": 4,
    "温暖男声": 5,
    # 或者使用数字ID
    "101001": 101001,
    "101002": 101002,
    # ...
}

def _get_voice_type(self, voice: str) -> int:
    """将voice名称转换为腾讯音色类型"""
    if voice.isdigit():
        return int(voice)
    return VOICE_TYPE_MAP.get(voice, 0)  # 默认亲和女声
```

**4. 语速和音量映射**

将项目配置的speed（0.25-4.0）映射到腾讯的speed（-2到2）：

```python
def _convert_speed(self, speed: float) -> int:
    """将OpenAI格式的speed转换为腾讯格式"""
    # OpenAI: 0.25-4.0, 默认1.0
    # 腾讯: -2到2, 默认0
    if speed <= 0.25:
        return -2
    elif speed <= 0.5:
        return -1
    elif speed <= 1.0:
        return 0
    elif speed <= 2.0:
        return 1
    else:
        return 2
```

### 3.4 工厂类更新

#### 3.4.1 STT工厂更新

```python
# backend/app/engines/voice/stt/factory.py

from .tencent_stt import TencentSTTEngine

class STTEngineFactory:
    @staticmethod
    def create_engine(provider: str, config: Optional[Dict[str, Any]] = None):
        # ...
        elif provider_lower == STTProvider.TENCENT.value:
            # 从环境变量读取配置
            api_config = config.get("api", {})
            if not api_config.get("app_id"):
                api_config["app_id"] = os.getenv("TENCENT_ASR_APP_ID")
            if not api_config.get("secret_id"):
                api_config["secret_id"] = os.getenv("TENCENT_SECRET_ID")
            if not api_config.get("secret_key"):
                api_config["secret_key"] = os.getenv("TENCENT_SECRET_KEY")
            
            engine = TencentSTTEngine(config)
        # ...
```

#### 3.4.2 TTS工厂更新

```python
# backend/app/engines/voice/tts/factory.py

from .tencent_tts import TencentTTSEngine

class TTSEngineFactory:
    @staticmethod
    def create_engine(provider: str, config: Optional[Dict[str, Any]] = None):
        # ...
        elif provider_lower == TTSProvider.TENCENT.value:
            # 从环境变量读取配置
            api_config = config.get("api", {})
            if not api_config.get("app_id"):
                api_config["app_id"] = os.getenv("TENCENT_TTS_APP_ID")
            if not api_config.get("secret_id"):
                api_config["secret_id"] = os.getenv("TENCENT_SECRET_ID")
            if not api_config.get("secret_key"):
                api_config["secret_key"] = os.getenv("TENCENT_SECRET_KEY")
            
            engine = TencentTTSEngine(config)
        # ...
```

### 3.5 配置文件更新

#### 3.5.1 STT配置

```yaml
# backend/config/voice/stt.yaml

engines:
  stt:
    tencent:
      provider: "tencent"
      model: "16k_zh"  # 引擎类型
      language: "zh-CN"
      # ASR参数
      filter_modal: 1      # 过滤语气词
      filter_punc: 1       # 过滤标点
      filter_dirty: 1      # 过滤脏话
      need_vad: 1          # 需要VAD
      word_info: 0         # 不返回词级时间戳
      voice_format: 1      # PCM格式
      # API配置
      api:
        app_id: null        # 从环境变量获取
        secret_id: null
        secret_key: null
        timeout: 30
        max_retries: 2
        retry_delay: 1.0
```

#### 3.5.2 TTS配置

```yaml
# backend/config/voice/tts.yaml

engines:
  tts:
    tencent:
      provider: "tencent"
      voice_type: 0         # 音色类型（0=亲和女声）
      codec: "mp3"          # 音频格式：pcm/mp3
      sample_rate: 16000   # 采样率：8000/16000
      speed: 0             # 语速：-2到2
      volume: 0            # 音量：-10到10
      # API配置
      api:
        app_id: null        # 从环境变量获取
        secret_id: null
        secret_key: null
        timeout: 30
        max_retries: 2
        retry_delay: 1.0
      # 流式配置
      streaming:
        enabled: true
        use_websocket: true  # 使用WebSocket流式合成
```

### 3.6 依赖管理

#### 3.6.1 添加依赖

```txt
# backend/requirements/base.txt

# 腾讯语音SDK依赖
websocket-client==0.48  # 必须0.48版本
requests>=2.28.0
```

#### 3.6.2 SDK集成方式

**方案A：直接使用example目录的SDK（推荐）**

将`example/tencentcloud-speech-sdk-python`目录复制到项目中，或作为子模块：

```python
import sys
sys.path.append("example/tencentcloud-speech-sdk-python")

from common import credential
from asr import speech_recognizer
from tts import speech_synthesizer_ws
```

**方案B：安装为Python包**

如果SDK支持pip安装，添加到requirements：

```txt
tencentcloud-speech-sdk-python>=1.0.0
```

### 3.7 环境变量配置

```bash
# backend/.env

# 腾讯云ASR配置
TENCENT_ASR_APP_ID=your_app_id
TENCENT_SECRET_ID=your_secret_id
TENCENT_SECRET_KEY=your_secret_key

# 腾讯云TTS配置（可以与ASR共用）
TENCENT_TTS_APP_ID=your_app_id  # 如果不同则单独配置
```

## 4. 实现步骤

### 4.1 第一阶段：基础实现

1. **创建腾讯ASR引擎**
   - [ ] 创建`backend/app/engines/voice/stt/tencent_stt.py`
   - [ ] 实现`TencentSTTEngine`类
   - [ ] 实现`transcribe()`方法（同步转异步）
   - [ ] 实现`health_check()`方法

2. **创建腾讯TTS引擎**
   - [ ] 创建`backend/app/engines/voice/tts/tencent_tts.py`
   - [ ] 实现`TencentTTSEngine`类
   - [ ] 实现`synthesize()`方法（非流式）
   - [ ] 实现`get_available_voices()`方法
   - [ ] 实现`health_check()`方法

3. **更新工厂类**
   - [ ] 更新`STTEngineFactory`支持腾讯ASR
   - [ ] 更新`TTSEngineFactory`支持腾讯TTS

4. **更新配置文件**
   - [ ] 完善`stt.yaml`中的腾讯配置
   - [ ] 完善`tts.yaml`中的腾讯配置

### 4.2 第二阶段：流式支持

1. **实现流式TTS**
   - [ ] 实现`stream_synthesize()`方法
   - [ ] 使用WebSocket流式合成器
   - [ ] 实现异步生成器

### 4.3 第三阶段：测试和优化

1. **单元测试**
   - [ ] 编写ASR引擎测试
   - [ ] 编写TTS引擎测试
   - [ ] 测试异步转换
   - [ ] 测试错误处理

2. **集成测试**
   - [ ] 测试API接口
   - [ ] 测试配置加载
   - [ ] 测试环境变量读取

3. **性能优化**
   - [ ] 优化线程池大小
   - [ ] 优化音频分块大小
   - [ ] 添加连接池（如需要）

## 5. 注意事项

### 5.1 异步转换

- 腾讯SDK是同步的，必须在线程中运行
- 使用`asyncio.to_thread()`或`ThreadPoolExecutor`
- 注意线程安全和资源清理

### 5.2 WebSocket连接管理

- 每个识别/合成任务需要独立的WebSocket连接
- 确保正确关闭连接，避免资源泄漏
- 设置合理的超时时间

### 5.3 错误处理

- 统一异常类型
- 记录详细的错误日志
- 实现重试机制（如配置中指定）

### 5.4 配置安全

- 敏感信息（secret_id, secret_key）从环境变量读取
- 不在代码中硬编码密钥
- 配置文件中的密钥字段设为`null`

### 5.5 音频格式

- 腾讯ASR支持多种音频格式，需要正确配置`voice_format`
- 腾讯TTS输出格式为PCM或MP3，需要根据需求选择
- 注意采样率匹配（8000/16000）

## 6. 测试计划

### 6.1 单元测试

```python
# tests/test_engines/test_voice/test_tencent_stt.py

@pytest.mark.asyncio
async def test_tencent_stt_transcribe():
    """测试腾讯ASR识别"""
    engine = TencentSTTEngine(config)
    text = await engine.transcribe(audio_data)
    assert isinstance(text, str)
    assert len(text) > 0

@pytest.mark.asyncio
async def test_tencent_tts_synthesize():
    """测试腾讯TTS合成"""
    engine = TencentTTSEngine(config)
    audio = await engine.synthesize("测试文本")
    assert isinstance(audio, bytes)
    assert len(audio) > 0
```

### 6.2 集成测试

```python
# tests/test_api/test_voice_api.py

def test_transcription_with_tencent():
    """测试使用腾讯ASR的转录API"""
    response = client.post(
        "/v1/audio/transcriptions",
        files={"file": audio_file},
        data={"provider": "tencent"}
    )
    assert response.status_code == 200
    assert "text" in response.json()
```

## 7. 参考文档

- 腾讯云ASR文档: https://cloud.tencent.com/document/product/1093
- 腾讯云TTS文档: https://cloud.tencent.com/document/product/1073
- 项目架构文档: `docs/02-后端架构设计.md`
- 开发规范: `docs/06-开发规范.md`

## 8. 后续优化

1. **连接池**: 复用WebSocket连接（如腾讯SDK支持）
2. **缓存**: 缓存常用文本的合成结果
3. **监控**: 添加性能监控和指标收集
4. **降级**: 实现自动降级机制（腾讯失败时切换到OpenAI）

---

**文档版本**: v1.0  
**创建日期**: 2024-12-19  
**最后更新**: 2024-12-19

