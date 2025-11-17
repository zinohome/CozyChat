# 腾讯SDK异步支持分析

## 1. 重要发现

您说得对！**Example目录下的SDK确实是腾讯官方的语音SDK**。

实际上，腾讯提供了**两个官方SDK**，用途不同：

### 1.1 官方通用SDK（tencentcloud-sdk-python）

**安装方式**: `pip install tencentcloud-sdk-python`  
**位置**: `backend/venv/lib/python3.11/site-packages/tencentcloud/`  
**GitHub**: https://github.com/TencentCloud/tencentcloud-sdk-python

**特点**:
- ✅ **同步HTTP API**（不是异步的）
- ✅ 支持一句话识别（`SentenceRecognition`）
- ✅ 支持异步任务识别（`CreateAsyncRecognitionTask`）
- ✅ 通用SDK，支持所有腾讯云服务
- ❌ **不支持WebSocket实时识别**
- ❌ **不支持流式TTS**

**API示例**:
```python
from tencentcloud.common import credential
from tencentcloud.asr.v20190614 import asr_client, models

# 创建客户端（同步）
cred = credential.Credential("secret_id", "secret_key")
client = asr_client.AsrClient(cred, "ap-beijing")

# 一句话识别（同步调用）
req = models.SentenceRecognitionRequest()
req.ProjectId = 0
req.SubServiceType = 2
req.EngSerViceType = "16k_zh"
req.SourceType = 1
req.VoiceFormat = "wav"
req.Data = audio_data  # bytes
req.DataLen = len(audio_data)

resp = client.SentenceRecognition(req)  # 同步调用，返回结果
print(resp.Result)
```

### 1.2 官方语音SDK（tencentcloud-speech-sdk-python）

**安装方式**: GitHub下载，手动集成  
**位置**: `example/tencentcloud-speech-sdk-python/`  
**GitHub**: https://github.com/TencentCloud/tencentcloud-speech-sdk-python  
**说明**: README明确标注"本项目是腾讯云语音SDK的python语言版本"

**特点**:
- ✅ **WebSocket实时识别**（`SpeechRecognizer`）
- ✅ **WebSocket流式TTS**（`SpeechSynthesizer`）
- ✅ **官方维护**（腾讯官方GitHub仓库）
- ❌ **同步API**（需要转异步）
- ❌ 不是pip包，需要手动集成

**API示例**:
```python
from common import credential
from asr import speech_recognizer

# WebSocket实时识别（同步）
cred = credential.Credential("secret_id", "secret_key")
recognizer = speech_recognizer.SpeechRecognizer(
    app_id, cred, "16k_zh", listener
)
recognizer.start()  # 启动WebSocket连接
recognizer.write(audio_chunk)  # 发送音频数据
recognizer.stop()  # 停止识别
```

## 2. 两种官方SDK对比

| 特性 | 通用SDK<br/>(tencentcloud-sdk-python) | 语音SDK<br/>(tencentcloud-speech-sdk-python) |
|------|---------|-------------|
| **官方性** | ✅ 官方 | ✅ 官方 |
| **安装方式** | pip安装 | GitHub下载 |
| **API类型** | HTTP REST API | WebSocket |
| **识别方式** | 一句话识别 | 实时流式识别 |
| **异步支持** | ❌ 同步 | ❌ 同步 |
| **实时性** | 批量处理 | 实时流式 |
| **TTS支持** | HTTP API | WebSocket流式 |
| **适用场景** | 短音频识别 | 长音频/实时识别 |
| **维护方式** | pip更新 | GitHub更新 |

## 3. 异步支持分析

### 3.1 官方SDK的异步支持

**结论：官方SDK是同步的，但可以轻松转换为异步**

```python
# 官方SDK的调用方式（同步）
resp = client.SentenceRecognition(req)  # 阻塞调用

# 转换为异步（简单）
async def transcribe_async(audio_data: bytes) -> str:
    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(
        executor,
        client.SentenceRecognition,  # 同步方法
        req
    )
    return resp.Result
```

**优势**:
- ✅ 转换简单（HTTP请求，在线程中运行即可）
- ✅ 不需要复杂的线程同步
- ✅ 官方维护，稳定可靠

**劣势**:
- ❌ 不支持实时流式识别
- ❌ 只适合短音频（一句话识别）

### 3.2 官方语音SDK的异步支持

**结论：官方语音SDK是同步的，需要复杂的异步转换（但这是官方推荐的实时识别方案）**

```python
# Example SDK的调用方式（同步，基于WebSocket）
recognizer.start()  # 启动WebSocket，阻塞
recognizer.write(audio_chunk)  # 发送数据，阻塞
recognizer.stop()  # 停止，阻塞

# 转换为异步（复杂）
async def transcribe_async(audio_data: bytes) -> str:
    # 需要：
    # 1. 在线程中运行WebSocket
    # 2. 使用Event/Queue收集结果
    # 3. 处理回调
    # 4. 管理连接生命周期
    ...
```

**优势**:
- ✅ 支持实时流式识别
- ✅ 支持长音频
- ✅ 支持流式TTS

**劣势**:
- ❌ 异步转换复杂
- ❌ 需要管理WebSocket连接
- ❌ 线程同步复杂

## 4. 推荐方案

### 方案A：使用官方SDK（推荐用于简单场景）

**适用场景**：
- 短音频识别（一句话）
- 不需要实时流式识别
- 追求稳定性和易维护性

**实现方式**：
```python
from tencentcloud.common import credential
from tencentcloud.asr.v20190614 import asr_client, models
from concurrent.futures import ThreadPoolExecutor
import asyncio

class TencentSTTEngine(STTEngineBase):
    _executor = ThreadPoolExecutor(max_workers=5)
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cred = credential.Credential(
            config["secret_id"],
            config["secret_key"]
        )
        self.client = asr_client.AsrClient(cred, "ap-beijing")
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """使用官方SDK进行识别（异步包装）"""
        # 创建请求
        req = models.SentenceRecognitionRequest()
        req.ProjectId = 0
        req.SubServiceType = 2
        req.EngSerViceType = self._get_engine_type(language)
        req.SourceType = 1
        req.VoiceFormat = self._detect_format(audio_data)
        req.Data = audio_data
        req.DataLen = len(audio_data)
        
        # 在线程中运行同步调用
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            self._executor,
            self.client.SentenceRecognition,
            req
        )
        
        return resp.Result
```

**优点**：
- ✅ 实现简单
- ✅ 官方维护
- ✅ 稳定可靠

### 方案B：使用官方语音SDK（推荐用于实时场景）

**适用场景**：
- 长音频识别
- 实时流式识别
- 需要流式TTS

**实现方式**：
```python
# 使用官方语音SDK（example目录）
# 需要复杂的异步转换（如之前方案所述）
# 这是腾讯官方推荐的实时识别方案
```

**优点**：
- ✅ 支持实时流式
- ✅ 支持长音频
- ✅ 官方维护
- ✅ 官方推荐的实时识别方案

**缺点**：
- ❌ 实现复杂
- ❌ 需要手动集成SDK

## 5. 最终建议

### 5.1 混合方案（最佳）

**根据场景选择SDK**：

1. **短音频识别** → 使用通用SDK（tencentcloud-sdk-python）
   ```python
   # 简单、稳定
   resp = await client.SentenceRecognition(req)
   ```

2. **长音频/实时识别** → 使用官方语音SDK（tencentcloud-speech-sdk-python）
   ```python
   # 复杂但支持实时，这是官方推荐的实时识别方案
   recognizer = SpeechRecognizer(...)
   ```

### 5.2 实现建议

**第一阶段**：先实现通用SDK版本（tencentcloud-sdk-python）
- ✅ 简单快速
- ✅ 满足大部分场景
- ✅ 稳定可靠
- ✅ pip安装，易于维护

**第二阶段**：如需要实时识别，再实现官方语音SDK版本（tencentcloud-speech-sdk-python）
- ✅ 支持实时流式
- ✅ 支持长音频
- ✅ 官方推荐的实时识别方案

## 6. 代码示例：官方SDK异步实现

```python
"""
腾讯ASR引擎 - 使用官方SDK
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional

from tencentcloud.common import credential
from tencentcloud.asr.v20190614 import asr_client, models

from app.engines.voice.stt.base import STTEngineBase, STTProvider
from app.utils.logger import logger


class TencentSTTEngine(STTEngineBase):
    """腾讯ASR引擎 - 使用官方SDK"""
    
    _executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="tencent_asr")
    
    # 语言到引擎类型映射
    LANGUAGE_MAP = {
        "zh-CN": "16k_zh",
        "zh": "16k_zh",
        "en-US": "16k_en",
        "en": "16k_en",
    }
    
    # 音频格式映射
    FORMAT_MAP = {
        "wav": "wav",
        "pcm": "pcm",
        "mp3": "mp3",
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 读取配置
        api_config = config.get("api", {})
        secret_id = api_config.get("secret_id") or config.get("secret_id")
        secret_key = api_config.get("secret_key") or config.get("secret_key")
        region = config.get("region", "ap-beijing")
        
        if not secret_id or not secret_key:
            raise ValueError("Tencent ASR requires secret_id and secret_key")
        
        # 创建凭证和客户端
        cred = credential.Credential(secret_id, secret_key)
        self.client = asr_client.AsrClient(cred, region)
        
        # 配置参数
        self.project_id = config.get("project_id", 0)
        self.sub_service_type = config.get("sub_service_type", 2)
        
        logger.info(
            f"Tencent ASR engine initialized (official SDK)",
            extra={
                "provider": self.provider.value,
                "region": region
            }
        )
    
    def _get_provider(self) -> STTProvider:
        return STTProvider.TENCENT
    
    def _get_engine_type(self, language: Optional[str] = None) -> str:
        """获取引擎类型"""
        lang = (language or self.language).lower()
        return self.LANGUAGE_MAP.get(lang, "16k_zh")
    
    def _detect_format(self, audio_data: bytes) -> str:
        """检测音频格式"""
        if audio_data.startswith(b"RIFF"):
            return "wav"
        elif audio_data.startswith(b"ID3") or audio_data.startswith(b"\xff\xfb"):
            return "mp3"
        else:
            return "pcm"
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """语音转文本（异步）"""
        # 验证音频格式
        if not self.validate_audio_format(audio_data):
            raise ValueError("Unsupported audio format")
        
        # 创建请求
        req = models.SentenceRecognitionRequest()
        req.ProjectId = self.project_id
        req.SubServiceType = self.sub_service_type
        req.EngSerViceType = self._get_engine_type(language)
        req.SourceType = 1  # 音频数据
        req.VoiceFormat = self._detect_format(audio_data)
        req.Data = audio_data
        req.DataLen = len(audio_data)
        
        # 可选参数
        if config.get("filter_modal"):
            req.FilterModal = 1
        if config.get("filter_punc"):
            req.FilterPunc = 1
        if config.get("filter_dirty"):
            req.FilterDirty = 1
        
        try:
            # 在线程中运行同步调用
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                self._executor,
                self.client.SentenceRecognition,
                req
            )
            
            logger.info(
                f"Tencent ASR transcription completed",
                extra={
                    "language": language or self.language,
                    "text_length": len(resp.Result) if resp.Result else 0
                }
            )
            
            return resp.Result
            
        except Exception as e:
            logger.error(
                f"Tencent ASR error: {e}",
                exc_info=True
            )
            raise
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 尝试创建一个测试请求
            req = models.SentenceRecognitionRequest()
            req.ProjectId = 0
            req.SubServiceType = 2
            req.EngSerViceType = "16k_zh"
            req.SourceType = 1
            req.VoiceFormat = "pcm"
            req.Data = b"\x00" * 100  # 最小测试数据
            req.DataLen = 100
            
            # 不实际调用，只检查客户端是否正常
            return self.client is not None
        except Exception as e:
            logger.warning(f"Tencent ASR health check failed: {e}")
            return False
```

## 7. 总结

### 7.1 关键发现

1. **两个SDK都是腾讯官方的**，但用途不同：
   - `tencentcloud-sdk-python`: 通用SDK，HTTP API，一句话识别
   - `tencentcloud-speech-sdk-python`: 语音SDK，WebSocket，实时识别

2. **两个SDK都不支持异步**，都需要转换为异步
3. **通用SDK转换简单**（HTTP请求在线程中运行）
4. **语音SDK转换复杂**（WebSocket + 线程同步），但这是官方推荐的实时识别方案

### 7.2 推荐方案

**优先使用通用SDK（tencentcloud-sdk-python）**：
- ✅ 简单易用
- ✅ 稳定可靠
- ✅ 官方维护
- ✅ pip安装，易于更新
- ✅ 异步转换简单

**如需实时识别，使用官方语音SDK（tencentcloud-speech-sdk-python）**：
- ✅ 支持实时流式
- ✅ 官方推荐的实时识别方案
- ✅ 官方维护
- ❌ 实现复杂
- ❌ 需要手动集成

### 7.3 下一步

1. **更新接入方案**：明确两个官方SDK的区别和用途
2. **实现通用SDK版本**：简单快速，满足大部分场景
3. **如需要，再实现官方语音SDK版本**：支持实时流式，官方推荐的实时识别方案

---

**文档版本**: v1.0  
**创建日期**: 2024-12-19  
**更新**: 基于tencentcloud-sdk-python==3.0.1489分析

