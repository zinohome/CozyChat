"""
腾讯TTS引擎

使用腾讯云语音合成SDK进行文本转语音
"""

# 标准库
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, AsyncIterator, Dict, List, Optional

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from .base import TTSEngineBase, TTSProvider


class AudioCollector:
    """HTTP流式合成音频收集器"""
    
    def __init__(self):
        self.audio_chunks = []
        self.error = None
        self.completed = threading.Event()
    
    def on_message(self, response):
        """收到音频数据"""
        data = response.get("data")
        if data:
            self.audio_chunks.append(data)
            logger.debug(f"Received audio chunk: {len(data)} bytes")
    
    def on_complete(self, response):
        """合成完成"""
        logger.info("TTS synthesis complete")
        self.completed.set()
    
    def on_fail(self, response):
        """合成失败"""
        code = response.get("Code", "unknown")
        message = response.get("Message", "Unknown error")
        self.error = f"TTS synthesis failed: {message} (code: {code})"
        logger.error(self.error)
        self.completed.set()


class StreamAudioCollector:
    """WebSocket流式合成音频收集器"""
    
    def __init__(self, audio_queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        self.audio_queue = audio_queue
        self.loop = loop  # 保存event loop引用
        self.error = None
        self.session_id = None
    
    def on_synthesis_start(self, session_id):
        """合成开始"""
        self.session_id = session_id
        logger.debug(f"TTS synthesis started: {session_id}")
    
    def on_synthesis_end(self):
        """合成结束"""
        logger.info("TTS synthesis ended")
        # 发送结束信号
        try:
            asyncio.run_coroutine_threadsafe(
                self.audio_queue.put(None),
                self.loop
            )
        except Exception as e:
            logger.error(f"Error sending end signal: {e}")
    
    def on_audio_result(self, audio_bytes):
        """收到音频数据"""
        try:
            asyncio.run_coroutine_threadsafe(
                self.audio_queue.put(audio_bytes),
                self.loop
            )
            logger.debug(f"Received audio chunk: {len(audio_bytes)} bytes")
        except Exception as e:
            logger.error(f"Error putting audio to queue: {e}")
    
    def on_text_result(self, response):
        """收到字幕结果（可选）"""
        pass
    
    def on_synthesis_fail(self, response):
        """合成失败"""
        code = response.get("code", "unknown")
        message = response.get("message", "Unknown error")
        self.error = f"TTS synthesis failed: {message} (code: {code})"
        logger.error(self.error)
        # 发送错误信号
        try:
            asyncio.run_coroutine_threadsafe(
                self.audio_queue.put(None),
                self.loop
            )
        except Exception as e:
            logger.error(f"Error sending error signal: {e}")


class TencentTTSEngine(TTSEngineBase):
    """腾讯TTS引擎
    
    支持两种合成方式：
    1. HTTP流式合成（适合短文本）
    2. WebSocket流式合成（适合长文本或实时场景）
    """
    
    # 音色类型映射（名称 -> voice_type整数）
    VOICE_TYPE_MAP = {
        # 基础音色 (0-5)
        "female": 0,        # 亲和女声
        "male": 1,          # 亲和男声
        "mature_male": 2,   # 成熟男声
        "energetic_male": 3,  # 活力男声
        "warm_female": 4,   # 温暖女声
        "warm_male": 5,     # 温暖男声
        # 数字直接映射
        "0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
        
        # 大模型音色 (101xxx 系列) - 需要购买大模型语音合成资源包
        # 注意：这些音色只能在WebSocket模式下使用
        "ai_female": 101001,      # AI女声1号
        "ai_male": 101002,        # AI男声1号
        "ai_narrator": 101003,    # AI播音员
        "ai_warm_female": 101004, # AI温暖女声
        "ai_energetic": 101005,   # AI活力女声
        # 数字直接映射
        "101001": 101001, "101002": 101002, "101003": 101003,
        "101004": 101004, "101005": 101005,
    }
    
    # 可用音色列表
    AVAILABLE_VOICES = [
        # 基础音色
        "female", "male", "mature_male", "energetic_male", 
        "warm_female", "warm_male",
        "0", "1", "2", "3", "4", "5",
        # 大模型音色（需要大模型语音合成资源包）
        "ai_female", "ai_male", "ai_narrator", "ai_warm_female", "ai_energetic",
        "101001", "101002", "101003", "101004", "101005",
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化腾讯TTS引擎
        
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
                "Tencent TTS requires app_id, secret_id and secret_key. "
                "Please set TENCENT_APP_ID, TENCENT_SECRET_ID and TENCENT_SECRET_KEY environment variables."
            )
        
        # 创建凭证
        # 类型存根文件位于 stubs/tencent_speech_sdk/__init__.pyi
        from tencent_speech_sdk import credential
        self.credential = credential.Credential(self.secret_id, self.secret_key)
        
        # 配置参数
        self.voice_type = config.get("voice_type", 0)
        self.codec = config.get("codec", "mp3")
        self.sample_rate = config.get("sample_rate", 16000)
        self.volume = config.get("volume", 0)
        self.tts_mode = config.get("tts_mode", "http")  # http/websocket
        self.fast_voice_type = config.get("fast_voice_type", "")  # 大模型音色的快速音色类型（可选）
        
        # 创建线程池用于同步调用
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info(
            f"Tencent TTS engine initialized",
            extra={
                "provider": self.provider.value,
                "app_id": self.app_id,
                "voice_type": self.voice_type,
                "codec": self.codec,
                "tts_mode": self.tts_mode
            }
        )
    
    def _get_provider(self) -> TTSProvider:
        """返回提供商类型"""
        return TTSProvider.TENCENT
    
    def _map_voice_type(self, voice: Optional[str] = None) -> int:
        """映射音色名称到腾讯voice_type
        
        Args:
            voice: 音色名称
            
        Returns:
            int: voice_type整数
        """
        voice_name = voice or self.voice
        
        # 如果已经是整数
        if isinstance(voice_name, int):
            return voice_name
        
        # 从映射表查找
        voice_type = self.VOICE_TYPE_MAP.get(str(voice_name).lower(), None)
        if voice_type is not None:
            return voice_type
        
        # 尝试直接解析为整数
        try:
            return int(voice_name)
        except (ValueError, TypeError):
            pass
        
        # 默认返回0
        logger.warning(f"Unknown voice type '{voice_name}', using default 0")
        return 0
    
    def _is_ai_voice(self, voice_type: int) -> bool:
        """判断是否为AI大模型音色
        
        Args:
            voice_type: 音色类型编号
            
        Returns:
            bool: 是否为AI大模型音色（101xxx系列）
        """
        return voice_type >= 101000
    
    def _convert_speed(self, speed: Optional[float] = None) -> int:
        """转换语速参数
        
        OpenAI格式: 0.25-4.0 (默认1.0)
        腾讯格式: -2到2 (默认0)
        
        Args:
            speed: OpenAI格式的语速
            
        Returns:
            int: 腾讯格式的语速
        """
        openai_speed = speed or self.speed
        
        # 转换公式: tencent_speed = (openai_speed - 1.0) * 2
        # 0.25 -> -1.5, 0.5 -> -1, 1.0 -> 0, 2.0 -> 2, 4.0 -> 6 (限制在-2到2)
        tencent_speed = (openai_speed - 1.0) * 2
        tencent_speed = max(-2, min(2, int(tencent_speed)))
        
        return tencent_speed
    
    def _convert_volume(self, volume: Optional[int] = None) -> int:
        """转换音量参数
        
        Args:
            volume: 音量（-10到10，默认0）
            
        Returns:
            int: 腾讯格式的音量
        """
        vol = volume or self.volume
        return max(-10, min(10, int(vol)))
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        **kwargs: Any
    ) -> bytes:
        """文本转语音（非流式）
        
        Args:
            text: 要转换的文本
            voice: 音色名称（可选）
            speed: 语速（可选）
            **kwargs: 其他参数
            
        Returns:
            bytes: 音频数据
            
        Raises:
            ValueError: 如果文本为空
            Exception: 如果转换失败
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            # 检查是否为AI音色（AI音色必须使用WebSocket）
            voice_type = self._map_voice_type(voice)
            is_ai_voice = self._is_ai_voice(voice_type)
            
            logger.info(
                f"Synthesizing text",
                extra={
                    "text_length": len(text),
                    "voice": voice,
                    "voice_type": voice_type,
                    "is_ai_voice": is_ai_voice,
                    "speed": speed
                }
            )
            
            # AI音色使用WebSocket流式合成并收集所有音频
            if is_ai_voice:
                logger.info("AI voice detected, using WebSocket synthesis and collecting all audio")
                audio_chunks = []
                async for chunk in self.stream_synthesize(text, voice, speed, **kwargs):
                    audio_chunks.append(chunk)
                return b"".join(audio_chunks)
            
            # 基础音色使用HTTP流式合成收集所有音频
            # 类型存根文件位于 stubs/tencent_speech_sdk/__init__.pyi
            from tencent_speech_sdk import speech_synthesizer
            
            # 创建音频收集器
            collector = AudioCollector()
            
            # 创建合成器
            voice_type = self._map_voice_type(voice)
            synthesizer = speech_synthesizer.SpeechSynthesizer(
                self.app_id,
                self.credential,
                voice_type,
                collector
            )
            
            # 配置参数
            synthesizer.set_codec(self.codec)
            synthesizer.set_sample_rate(self.sample_rate)
            synthesizer.set_speed(self._convert_speed(speed))
            synthesizer.set_volume(self._convert_volume(kwargs.get("volume")))
            
            # 在线程中运行合成
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._executor,
                synthesizer.synthesis,
                text
            )
            
            # 等待合成完成
            timeout = self.config.get("api", {}).get("timeout", 30)
            if collector.completed.wait(timeout=timeout):
                if collector.error:
                    raise Exception(collector.error)
                
                # 合并所有音频块
                audio_data = b"".join(collector.audio_chunks)
                logger.info(f"Synthesis complete: {len(audio_data)} bytes")
                return audio_data
            else:
                raise TimeoutError(f"TTS synthesis timeout after {timeout} seconds")
                
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}", exc_info=True)
            raise
    
    async def stream_synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        **kwargs: Any
    ) -> AsyncIterator[bytes]:
        """流式文本转语音
        
        Args:
            text: 要转换的文本
            voice: 音色名称（可选）
            speed: 语速（可选）
            **kwargs: 其他参数
                - use_websocket: bool - 强制使用WebSocket
            
        Yields:
            bytes: 音频数据块
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            # 确定使用的模式
            # 注意：AI大模型音色只支持WebSocket模式
            voice_type = self._map_voice_type(voice)
            is_ai_voice = self._is_ai_voice(voice_type)
            use_websocket = kwargs.get("use_websocket", self.tts_mode == "websocket") or is_ai_voice
            
            if is_ai_voice and not use_websocket:
                logger.info(f"AI voice type {voice_type} requires WebSocket mode, switching to WebSocket")
                use_websocket = True
            
            logger.info(
                f"Streaming synthesis",
                extra={
                    "text_length": len(text),
                    "voice": voice,
                    "speed": speed,
                    "use_websocket": use_websocket
                }
            )
            
            if use_websocket:
                # 使用WebSocket流式合成
                async for chunk in self._stream_synthesize_ws(text, voice, speed, **kwargs):
                    yield chunk
            else:
                # 使用HTTP流式合成
                async for chunk in self._stream_synthesize_http(text, voice, speed, **kwargs):
                    yield chunk
                    
        except Exception as e:
            logger.error(f"Stream synthesis failed: {e}", exc_info=True)
            raise
    
    async def _stream_synthesize_http(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        **kwargs: Any
    ) -> AsyncIterator[bytes]:
        """HTTP流式合成"""
        # 类型存根文件位于 stubs/tencent_speech_sdk/__init__.pyi
        from tencent_speech_sdk import speech_synthesizer
        
        # 创建音频队列
        audio_queue = asyncio.Queue()
        
        # 获取当前事件循环，在线程中使用
        loop = asyncio.get_event_loop()
        
        # 创建自定义收集器，将音频放入队列
        class QueueCollector:
            def __init__(self, queue, event_loop):
                self.queue = queue
                self.loop = event_loop
                self.error = None
            
            def on_message(self, response):
                data = response.get("data")
                if data:
                    try:
                        asyncio.run_coroutine_threadsafe(
                            self.queue.put(data),
                            self.loop
                        )
                    except Exception as e:
                        logger.error(f"Error putting data to queue: {e}")
            
            def on_complete(self, response):
                try:
                    asyncio.run_coroutine_threadsafe(
                        self.queue.put(None),  # 结束信号
                        self.loop
                    )
                except Exception as e:
                    logger.error(f"Error sending completion signal: {e}")
            
            def on_fail(self, response):
                code = response.get("Code", "unknown")
                message = response.get("Message", "Unknown error")
                self.error = f"TTS synthesis failed: {message} (code: {code})"
                try:
                    asyncio.run_coroutine_threadsafe(
                        self.queue.put(None),
                        self.loop
                    )
                except Exception as e:
                    logger.error(f"Error sending fail signal: {e}")
        
        collector = QueueCollector(audio_queue, loop)
        
        # 创建合成器
        voice_type = self._map_voice_type(voice)
        synthesizer = speech_synthesizer.SpeechSynthesizer(
            self.app_id,
            self.credential,
            voice_type,
            collector
        )
        
        # 配置参数
        synthesizer.set_codec(self.codec)
        synthesizer.set_sample_rate(self.sample_rate)
        synthesizer.set_speed(self._convert_speed(speed))
        synthesizer.set_volume(self._convert_volume(kwargs.get("volume")))
        
        # 在线程中启动合成（重用之前获取的loop）
        loop.run_in_executor(
            self._executor,
            synthesizer.synthesis,
            text
        )
        
        # 从队列中读取音频块
        while True:
            chunk = await audio_queue.get()
            if chunk is None:  # 结束信号
                if collector.error:
                    raise Exception(collector.error)
                break
            yield chunk
    
    async def _stream_synthesize_ws(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        **kwargs: Any
    ) -> AsyncIterator[bytes]:
        """WebSocket流式合成
        
        注意：SSL证书配置已在tencent_speech_sdk包装器中全局设置
        """
        # 类型存根文件位于 stubs/tencent_speech_sdk/__init__.pyi
        from tencent_speech_sdk import speech_synthesizer_ws
        
        # 创建音频队列
        audio_queue = asyncio.Queue()
        
        # 获取当前event loop
        loop = asyncio.get_event_loop()
        
        # 创建收集器（传入event loop用于线程间通信）
        collector = StreamAudioCollector(audio_queue, loop)
        
        # 创建合成器
        synthesizer = speech_synthesizer_ws.SpeechSynthesizer(
            self.app_id,
            self.credential,
            collector
        )
        
        # 配置参数
        voice_type = self._map_voice_type(voice)
        synthesizer.set_voice_type(voice_type)
        synthesizer.set_codec(self.codec)
        synthesizer.set_sample_rate(self.sample_rate)
        synthesizer.set_speed(self._convert_speed(speed))
        synthesizer.set_volume(self._convert_volume(kwargs.get("volume")))
        synthesizer.set_text(text)
        
        # 设置大模型音色的FastVoiceType（如果有）
        if self.fast_voice_type:
            synthesizer.set_fast_voice_type(self.fast_voice_type)
        
        # 如果是AI大模型音色，记录日志
        if self._is_ai_voice(voice_type):
            logger.info(f"Using AI voice type: {voice_type}, requires AI model TTS resource pack")
        
        # 在线程中启动合成（WebSocket版本使用start和wait方法）
        def run_synthesis():
            try:
                synthesizer.start()
                synthesizer.wait()  # 等待合成完成
            except Exception as e:
                logger.error(f"WebSocket synthesis error: {e}")
                # 发送错误信号
                try:
                    asyncio.run_coroutine_threadsafe(
                        audio_queue.put(None),
                        asyncio.get_event_loop()
                    )
                except Exception:
                    pass
        
        loop = asyncio.get_event_loop()
        loop.run_in_executor(
            self._executor,
            run_synthesis
        )
        
        # 从队列中读取音频块
        while True:
            chunk = await audio_queue.get()
            if chunk is None:  # 结束信号
                if collector.error:
                    raise Exception(collector.error)
                break
            yield chunk
    
    def get_available_voices(self) -> List[str]:
        """获取可用的语音列表
        
        Returns:
            List[str]: 语音名称列表
        """
        return self.AVAILABLE_VOICES.copy()
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 引擎是否健康
        """
        try:
            # 检查配置是否完整
            if not all([self.app_id, self.secret_id, self.secret_key]):
                logger.error("Tencent TTS config incomplete")
                return False
            
            # 尝试创建一个简单的合成器来验证凭证
            # 类型存根文件位于 stubs/tencent_speech_sdk/__init__.pyi
            from tencent_speech_sdk import speech_synthesizer
            
            class DummyCollector:
                def on_message(self, response): pass
                def on_complete(self, response): pass
                def on_fail(self, response): pass
            
            synthesizer = speech_synthesizer.SpeechSynthesizer(
                self.app_id,
                self.credential,
                0,
                DummyCollector()
            )
            
            logger.info("Tencent TTS health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Tencent TTS health check failed: {e}")
            return False
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)

