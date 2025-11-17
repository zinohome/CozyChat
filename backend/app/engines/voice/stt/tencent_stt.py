"""
腾讯ASR引擎

使用腾讯云语音识别SDK进行语音转文本
"""

# 标准库
import asyncio
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from .base import STTEngineBase, STTProvider


class ResultCollector:
    """实时识别结果收集器
    
    用于收集WebSocket实时识别的结果
    """
    
    def __init__(self):
        self.final_text = ""
        self.error = None
        self.completed = threading.Event()
    
    def on_recognition_start(self, response):
        """识别开始"""
        logger.debug(f"Recognition started: {response}")
    
    def on_sentence_begin(self, response):
        """句子开始"""
        logger.debug(f"Sentence begin: {response}")
    
    def on_recognition_result_change(self, response):
        """识别结果变化（中间结果）"""
        logger.debug(f"Result change: {response}")
    
    def on_sentence_end(self, response):
        """句子结束（获取最终结果）"""
        try:
            result = response.get("result", {})
            text = result.get("voice_text_str", "")
            if text:
                self.final_text += text
            logger.debug(f"Sentence end: {text}")
        except Exception as e:
            logger.error(f"Error parsing sentence end: {e}")
    
    def on_recognition_complete(self, response):
        """识别完成"""
        logger.info(f"Recognition complete: {self.final_text}")
        self.completed.set()
    
    def on_fail(self, response):
        """识别失败"""
        code = response.get("code", "unknown")
        message = response.get("message", "Unknown error")
        self.error = f"Recognition failed: {message} (code: {code})"
        logger.error(self.error)
        self.completed.set()


class TencentSTTEngine(STTEngineBase):
    """腾讯ASR引擎
    
    支持两种识别方式：
    1. FlashRecognizer - 一句话识别（HTTP，适合短音频）
    2. SpeechRecognizer - 实时识别（WebSocket，适合长音频或实时场景）
    """
    
    # 音频格式映射
    FORMAT_MAP = {
        "wav": "wav",
        "mp3": "mp3",
        "pcm": "pcm",
        "opus": "opus",
        "speex": "speex",
    }
    
    # 引擎类型映射（语言代码 -> 腾讯引擎类型）
    ENGINE_TYPE_MAP = {
        "zh": "16k_zh",
        "zh-CN": "16k_zh",
        "zh-cn": "16k_zh",
        "en": "16k_en",
        "en-US": "16k_en",
        "en-us": "16k_en",
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化腾讯ASR引擎
        
        Args:
            config: 配置字典，必须包含app_id, secret_id, secret_key
        """
        if config is None:
            config = {}
        
        super().__init__(config)
        
        # 获取认证信息
        self.app_id = config.get("app_id") or settings.tencent_app_id
        self.secret_id = config.get("secret_id") or settings.tencent_secret_id
        self.secret_key = config.get("secret_key") or settings.tencent_secret_key
        
        if not all([self.app_id, self.secret_id, self.secret_key]):
            raise ValueError(
                "Tencent ASR requires app_id, secret_id and secret_key. "
                "Please set TENCENT_APP_ID, TENCENT_SECRET_ID and TENCENT_SECRET_KEY environment variables."
            )
        
        # 创建凭证
        from tencent_speech_sdk import credential
        self.credential = credential.Credential(self.secret_id, self.secret_key)
        
        # 配置参数
        self.recognition_mode = config.get("recognition_mode", "auto")  # flash/realtime/auto
        self.filter_modal = config.get("filter_modal", 1)
        self.filter_punc = config.get("filter_punc", 1)
        self.filter_dirty = config.get("filter_dirty", 1)
        self.need_vad = config.get("need_vad", 1)
        self.voice_format = config.get("voice_format", "wav")
        
        # 音频大小阈值（字节），超过此值使用实时识别
        self.realtime_threshold = config.get("realtime_threshold", 1024 * 1024)  # 1MB
        
        # 创建线程池用于同步调用
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info(
            f"Tencent ASR engine initialized",
            extra={
                "provider": self.provider.value,
                "app_id": self.app_id,
                "recognition_mode": self.recognition_mode,
                "model": self.model
            }
        )
    
    def _get_provider(self) -> STTProvider:
        """返回提供商类型"""
        return STTProvider.TENCENT
    
    def _get_engine_type(self, language: Optional[str] = None) -> str:
        """获取腾讯引擎类型
        
        Args:
            language: 语言代码（zh-CN, en-US等）
            
        Returns:
            str: 腾讯引擎类型（16k_zh, 16k_en等）
        """
        lang = language or self.language
        
        # 尝试从配置的model获取
        if self.model and "_" in self.model:
            return self.model
        
        # 从语言代码映射
        for key, value in self.ENGINE_TYPE_MAP.items():
            if lang.lower().startswith(key.lower()):
                return value
        
        # 默认返回中文
        return "16k_zh"
    
    def _detect_format(self, audio_data: bytes) -> str:
        """检测音频格式
        
        Args:
            audio_data: 音频数据
            
        Returns:
            str: 音频格式
        """
        # 检查文件头魔数
        if audio_data.startswith(b"RIFF"):
            return "wav"
        elif audio_data.startswith(b"ID3") or audio_data.startswith(b"\xff\xfb"):
            return "mp3"
        elif audio_data.startswith(b"OggS"):
            return "opus"
        
        # 默认返回配置的格式
        return self.voice_format
    
    def _get_format_code(self, audio_data: bytes) -> int:
        """获取音频格式代码（用于实时识别）
        
        Args:
            audio_data: 音频数据
            
        Returns:
            int: 格式代码（1-wav, 3-opus, 4-speex, 6-mp3, 7-m4a, 8-aac）
        """
        fmt = self._detect_format(audio_data)
        
        format_code_map = {
            "wav": 1,
            "opus": 3,
            "speex": 4,
            "mp3": 6,
            "m4a": 7,
            "aac": 8,
        }
        
        return format_code_map.get(fmt, 1)  # 默认wav
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """语音转文本
        
        根据配置和音频大小自动选择识别方式
        
        Args:
            audio_data: 音频数据（bytes）
            language: 语言代码（可选）
            **kwargs: 其他参数
                - realtime: bool - 强制使用实时识别
                - flash: bool - 强制使用一句话识别
            
        Returns:
            str: 识别的文本
            
        Raises:
            ValueError: 如果音频数据无效
            Exception: 如果识别失败
        """
        try:
            # 验证音频格式
            if not self.validate_audio_format(audio_data):
                raise ValueError("Unsupported audio format")
            
            # 确定识别方式
            force_realtime = kwargs.get("realtime", False)
            force_flash = kwargs.get("flash", False)
            
            if self.recognition_mode == "flash" or force_flash:
                use_realtime = False
            elif self.recognition_mode == "realtime" or force_realtime:
                use_realtime = True
            else:  # auto
                # 根据音频大小自动选择
                use_realtime = len(audio_data) > self.realtime_threshold
            
            logger.info(
                f"Transcribing audio",
                extra={
                    "size": len(audio_data),
                    "use_realtime": use_realtime,
                    "language": language
                }
            )
            
            if use_realtime:
                return await self._transcribe_realtime(audio_data, language)
            else:
                return await self._transcribe_flash(audio_data, language)
                
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            raise
    
    async def _transcribe_flash(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> str:
        """使用FlashRecognizer进行一句话识别
        
        Args:
            audio_data: 音频数据
            language: 语言代码
            
        Returns:
            str: 识别的文本
        """
        from tencent_speech_sdk import flash_recognizer
        
        # 创建识别器
        recognizer = flash_recognizer.FlashRecognizer(
            self.app_id,
            self.credential
        )
        
        # 创建请求
        engine_type = self._get_engine_type(language)
        req = flash_recognizer.FlashRecognitionRequest(engine_type)
        req.set_voice_format(self._detect_format(audio_data))
        req.set_filter_modal(self.filter_modal)
        req.set_filter_punc(self.filter_punc)
        req.set_filter_dirty(self.filter_dirty)
        
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
        
        # 检查错误
        code = resp.get("code")
        if code != 0:
            message = resp.get("message", "Unknown error")
            raise Exception(f"Flash recognition failed: {message} (code: {code})")
        
        # 提取文本
        flash_result = resp.get("flash_result", [])
        if flash_result and len(flash_result) > 0:
            text = flash_result[0].get("text", "")
            logger.info(f"Flash recognition result: {text}")
            return text
        
        return ""
    
    async def _transcribe_realtime(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> str:
        """使用SpeechRecognizer进行实时识别
        
        Args:
            audio_data: 音频数据
            language: 语言代码
            
        Returns:
            str: 识别的文本
        """
        from tencent_speech_sdk import speech_recognizer
        
        # 创建结果收集器
        collector = ResultCollector()
        
        # 创建识别器
        engine_type = self._get_engine_type(language)
        recognizer = speech_recognizer.SpeechRecognizer(
            self.app_id,
            self.credential,
            engine_type,
            collector
        )
        
        # 配置参数
        recognizer.set_filter_modal(self.filter_modal)
        recognizer.set_filter_punc(self.filter_punc)
        recognizer.set_filter_dirty(self.filter_dirty)
        recognizer.set_need_vad(self.need_vad)
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
        timeout = self.config.get("api", {}).get("timeout", 30)
        if collector.completed.wait(timeout=timeout):
            if collector.error:
                raise Exception(collector.error)
            logger.info(f"Realtime recognition result: {collector.final_text}")
            return collector.final_text
        else:
            raise TimeoutError(f"Realtime recognition timeout after {timeout} seconds")
    
    def _realtime_recognize_sync(
        self,
        recognizer,
        audio_data: bytes,
        collector: ResultCollector
    ):
        """同步执行实时识别
        
        在线程中运行，发送音频数据并等待识别完成
        
        Args:
            recognizer: SpeechRecognizer实例
            audio_data: 音频数据
            collector: 结果收集器
        """
        try:
            # 启动识别
            recognizer.start()
            
            # 分片发送音频数据（每次6400字节）
            chunk_size = 6400
            offset = 0
            
            while offset < len(audio_data):
                end = min(offset + chunk_size, len(audio_data))
                chunk = audio_data[offset:end]
                recognizer.write(chunk)
                offset = end
            
            # 结束识别
            recognizer.stop()
            
        except Exception as e:
            collector.error = f"Realtime recognition error: {str(e)}"
            collector.completed.set()
            logger.error(f"Realtime recognition error: {e}", exc_info=True)
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 引擎是否健康
        """
        try:
            # 检查配置是否完整
            if not all([self.app_id, self.secret_id, self.secret_key]):
                logger.error("Tencent ASR config incomplete")
                return False
            
            # 尝试创建一个简单的识别器来验证凭证
            from tencent_speech_sdk import flash_recognizer
            recognizer = flash_recognizer.FlashRecognizer(
                self.app_id,
                self.credential
            )
            
            logger.info("Tencent ASR health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Tencent ASR health check failed: {e}")
            return False
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)

