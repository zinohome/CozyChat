"""
zhconv 类型存根文件

为 zhconv 库提供类型注解，避免 type: ignore[import-untyped]
"""

def convert(text: str, variant: str = "zh-cn") -> str:
    """转换文本
    
    Args:
        text: 要转换的文本
        variant: 目标变体，默认为 "zh-cn"（简体中文）
        
    Returns:
        str: 转换后的文本
    """
    ...
