"""
文本转换工具

提供繁体中文转简体中文等功能
"""

# 标准库
from typing import Optional

# 本地库
from app.utils.logger import logger

try:
    # 尝试导入 zhconv（如果已安装）
    # 类型存根文件位于 stubs/zhconv/__init__.pyi
    import zhconv
    ZHCONV_AVAILABLE = True
except ImportError:
    ZHCONV_AVAILABLE = False
    logger.warning("zhconv not installed, traditional to simplified conversion will be disabled")


def to_simplified(text: str) -> str:
    """将繁体中文转换为简体中文
    
    Args:
        text: 输入文本（可能是繁体或简体）
    
    Returns:
        str: 转换后的简体中文文本
    
    Note:
        如果 zhconv 未安装，将返回原文本
    """
    if not text:
        return text
    
    if not ZHCONV_AVAILABLE:
        logger.debug("zhconv not available, skipping conversion")
        return text
    
    try:
        # zhconv.convert 会自动检测并转换繁体到简体
        # 如果文本已经是简体，不会改变
        converted = zhconv.convert(text, "zh-cn")
        
        # 记录转换情况（仅在确实有变化时记录）
        if converted != text:
            logger.debug(
                "Converted traditional Chinese to simplified",
                extra={
                    "original_length": len(text),
                    "converted_length": len(converted),
                    "original_preview": text[:50] if len(text) > 50 else text,
                    "converted_preview": converted[:50] if len(converted) > 50 else converted
                }
            )
        
        return converted
    except Exception as e:
        logger.warning(
            f"Failed to convert text to simplified Chinese: {e}",
            exc_info=True
        )
        # 转换失败时返回原文本
        return text


def is_traditional_chinese(text: str) -> bool:
    """检测文本是否包含繁体中文
    
    Args:
        text: 输入文本
    
    Returns:
        bool: 如果包含繁体中文返回True，否则返回False
    
    Note:
        如果 zhconv 未安装，将返回False
    """
    if not text or not ZHCONV_AVAILABLE:
        return False
    
    try:
        # 如果转换后文本有变化，说明包含繁体
        converted = zhconv.convert(text, "zh-cn")
        return converted != text
    except Exception:
        return False

