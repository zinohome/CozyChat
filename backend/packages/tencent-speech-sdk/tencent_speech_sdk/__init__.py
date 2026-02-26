"""
Tencent Speech SDK Wrapper

腾讯语音SDK的包装模块，自动添加SDK路径到sys.path
"""
import sys
import os
from pathlib import Path

# 获取SDK路径（相对于项目根目录）
_current_file = Path(__file__).resolve()

# 尝试多个可能的路径
# 1. 相对路径（开发模式/源码模式）
_sdk_path_relative = _current_file.parent.parent.parent.parent / "vendor" / "tencentcloud-speech-sdk-python"
# 2. Docker 容器中的绝对路径
_sdk_path_docker = Path("/opt/cozychat/backend/vendor/tencentcloud-speech-sdk-python")
# 3. 备选项目根目录路径
_sdk_path_alt = Path("/app/vendor/tencentcloud-speech-sdk-python")

_sdk_path = None
for p in [_sdk_path_relative, _sdk_path_docker, _sdk_path_alt]:
    if p.exists():
        _sdk_path = p
        break

# 检查SDK是否存在
if _sdk_path is None:
    raise ImportError(
        f"Tencent Speech SDK not found. Checked paths:\n"
        f"  - {_sdk_path_relative}\n"
        f"  - {_sdk_path_docker}\n"
        "Please ensure the SDK is properly installed via git submodule or manual clone into backend/vendor/."
    )

# 添加SDK路径到sys.path（如果还没有添加）
_sdk_path_str = str(_sdk_path)
if _sdk_path_str not in sys.path:
    sys.path.insert(0, _sdk_path_str)

# 配置SSL证书（用于WebSocket连接）
try:
    import ssl
    import certifi
    from websocket import WebSocketApp
    
    # 设置默认的SSL上下文使用certifi的证书
    ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())
    
    # Monkey-patch WebSocketApp.run_forever 来强制使用certifi证书
    # 注意：websocket-client==0.48 的签名
    _original_run_forever = WebSocketApp.run_forever
    
    def patched_run_forever(self, sockopt=None, sslopt=None,
                           ping_interval=0, ping_timeout=None,
                           http_proxy_host=None, http_proxy_port=None,
                           http_no_proxy=None, http_proxy_auth=None,
                           skip_utf8_validation=False,
                           host=None, origin=None, dispatcher=None):
        """Patched run_forever that uses certifi certificates for websocket-client 0.48"""
        # 如果没有提供sslopt，使用certifi证书
        if sslopt is None:
            sslopt = {
                "cert_reqs": ssl.CERT_REQUIRED,
                "ca_certs": certifi.where(),
                "check_hostname": True,
            }
        
        # 调用原始方法，只传递0.48版本支持的参数
        return _original_run_forever(
            self, 
            sockopt=sockopt, 
            sslopt=sslopt,
            ping_interval=ping_interval, 
            ping_timeout=ping_timeout,
            http_proxy_host=http_proxy_host, 
            http_proxy_port=http_proxy_port,
            http_no_proxy=http_no_proxy, 
            http_proxy_auth=http_proxy_auth,
            skip_utf8_validation=skip_utf8_validation,
            host=host, 
            origin=origin, 
            dispatcher=dispatcher
        )
    
    # 应用monkey-patch
    WebSocketApp.run_forever = patched_run_forever
    
    print(f"[tencent_speech_sdk] SSL configuration applied using certifi: {certifi.where()}")
    
except ImportError as e:
    print(f"[tencent_speech_sdk] Warning: Failed to configure SSL - {e}")
    pass  # certifi不可用，使用系统默认证书

# 导出常用模块
try:
    from common import credential
    from asr import flash_recognizer, speech_recognizer
    from tts import speech_synthesizer, speech_synthesizer_ws, flowing_speech_synthesizer
    
    __all__ = [
        "credential",
        "flash_recognizer",
        "speech_recognizer",
        "speech_synthesizer",
        "speech_synthesizer_ws",
        "flowing_speech_synthesizer",
    ]
except ImportError as e:
    raise ImportError(
        f"Failed to import Tencent Speech SDK modules: {e}\n"
        f"SDK path: {_sdk_path}\n"
        "Please ensure the SDK is properly installed via git submodule."
    ) from e
