"""
文本摘要工具

提供文本摘要功能（使用LLM进行摘要）
"""

# 标准库
from typing import Any, Dict, Optional

# 本地库
from app.engines.tools.base import Tool, ToolType
from app.utils.logger import logger


class TextSummarizerTool(Tool):
    """文本摘要工具
    
    使用LLM对长文本进行摘要，支持指定摘要长度和风格
    """
    
    def __init__(self):
        """初始化文本摘要工具"""
        super().__init__(tool_type=ToolType.BUILTIN)
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "text_summarizer"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "对长文本进行摘要，提取关键信息和要点。"
            "适用于需要将长文本压缩为简短摘要的场景，如文章摘要、会议记录摘要、文档总结等。"
            "注意：此工具需要调用LLM进行摘要，可能需要一些时间。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "text": {
                "type": "string",
                "description": "要摘要的文本内容",
                "required": True
            },
            "max_length": {
                "type": "integer",
                "description": "摘要的最大长度（字符数），默认200。如果设置为0，则自动确定长度（约为原文的10-20%）",
                "required": False
            },
            "style": {
                "type": "string",
                "description": "摘要风格（可选）。可选值：'concise'（简洁，默认）、'detailed'（详细）、'bullet'（要点列表）、'paragraph'（段落形式）",
                "required": False
            },
            "language": {
                "type": "string",
                "description": "摘要语言（可选），默认为'zh'（中文）。可选值：'zh'（中文）、'en'（英文）",
                "required": False
            }
        }
    
    async def execute(
        self,
        text: str,
        max_length: Optional[int] = None,
        style: Optional[str] = None,
        language: Optional[str] = None
    ) -> str:
        """执行文本摘要
        
        Args:
            text: 要摘要的文本
            max_length: 摘要最大长度（字符数）
            style: 摘要风格
            language: 摘要语言
            
        Returns:
            str: 摘要结果或错误信息
        """
        try:
            # 参数验证
            if not text or not text.strip():
                return "错误：文本内容不能为空"
            
            # 设置默认值
            max_length = max_length or 200
            style = style or "concise"
            language = language or "zh"
            
            # 验证参数
            if max_length < 0:
                return "错误：max_length必须大于等于0"
            
            if style not in ["concise", "detailed", "bullet", "paragraph"]:
                return f"错误：不支持的摘要风格 '{style}'，可选值：'concise'、'detailed'、'bullet'、'paragraph'"
            
            if language not in ["zh", "en"]:
                return f"错误：不支持的语言 '{language}'，可选值：'zh'、'en'"
            
            # 如果文本很短，直接返回
            text_length = len(text)
            if text_length <= max_length and max_length > 0:
                logger.info(
                    f"Text is already short enough, returning original",
                    extra={"text_length": text_length, "max_length": max_length}
                )
                return text
            
            # 构建摘要提示词
            prompt = self._build_summary_prompt(text, max_length, style, language)
            
            # 注意：这里返回提示词，实际摘要需要由调用者使用LLM完成
            # 因为工具系统不应该直接调用AI引擎，这应该由orchestrator处理
            # 但为了工具接口的完整性，我们返回一个说明
            
            logger.info(
                f"Text summarizer called: text_length={text_length}, max_length={max_length}, style={style}",
                extra={
                    "text_length": text_length,
                    "max_length": max_length,
                    "style": style,
                    "language": language
                }
            )
            
            # 返回提示词说明
            return (
                f"文本摘要请求已接收。\n"
                f"原文长度：{text_length} 字符\n"
                f"目标长度：{max_length} 字符（{'自动' if max_length == 0 else '固定'}）\n"
                f"摘要风格：{style}\n"
                f"语言：{language}\n\n"
                f"注意：文本摘要功能需要由AI模型执行。"
                f"请将以下提示词发送给AI模型进行摘要：\n\n"
                f"{prompt}"
            )
            
        except Exception as e:
            error_msg = f"错误：文本摘要失败 - {str(e)}"
            logger.error(f"Text summarizer error: {error_msg}", exc_info=True)
            return error_msg
    
    def _build_summary_prompt(
        self,
        text: str,
        max_length: int,
        style: str,
        language: str
    ) -> str:
        """构建摘要提示词
        
        Args:
            text: 原文
            max_length: 最大长度
            style: 摘要风格
            language: 语言
            
        Returns:
            str: 摘要提示词
        """
        # 语言映射
        lang_map = {
            "zh": {
                "title": "请对以下文本进行摘要",
                "requirements": "要求",
                "style_concise": "简洁明了",
                "style_detailed": "详细完整",
                "style_bullet": "以要点列表形式",
                "style_paragraph": "以段落形式",
                "max_length": "摘要长度不超过",
                "characters": "字符",
                "preserve": "保留原文的关键信息和要点",
            },
            "en": {
                "title": "Please summarize the following text",
                "requirements": "Requirements",
                "style_concise": "Concise and clear",
                "style_detailed": "Detailed and complete",
                "style_bullet": "In bullet point format",
                "style_paragraph": "In paragraph format",
                "max_length": "Summary length should not exceed",
                "characters": "characters",
                "preserve": "Preserve key information and main points from the original text",
            }
        }
        
        lang_text = lang_map.get(language, lang_map["zh"])
        
        # 风格描述
        style_map = {
            "concise": lang_text["style_concise"],
            "detailed": lang_text["style_detailed"],
            "bullet": lang_text["style_bullet"],
            "paragraph": lang_text["style_paragraph"],
        }
        style_desc = style_map.get(style, lang_text["style_concise"])
        
        # 构建提示词
        if max_length == 0:
            # 自动长度
            length_desc = f"约为原文的10-20%"
        else:
            length_desc = f"{lang_text['max_length']} {max_length} {lang_text['characters']}"
        
        prompt = f"""{lang_text['title']}：

{text}

{lang_text['requirements']}：
1. {style_desc}
2. {length_desc}
3. {lang_text['preserve']}

请直接输出摘要内容，不要包含其他说明文字。"""
        
        return prompt

