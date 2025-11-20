"""提示词构建器"""

# 标准库
from typing import Dict, Any, Optional, Tuple

# 本地库
from .loader import PromptLoader
from app.utils.logger import logger


class PromptBuilder:
    """提示词构建器
    
    根据用户偏好和配置动态构建提示词
    """
    
    def __init__(self, loader: Optional[PromptLoader] = None):
        """初始化PromptBuilder
        
        Args:
            loader: 提示词加载器实例
        """
        self.loader = loader or PromptLoader()
    
    def build_user_message(
        self,
        content: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Optional[str]]:
        """构建用户消息和指令
        
        Args:
            content: 用户消息内容
            preferences: 用户偏好设置
            
        Returns:
            (消息内容, 指令文本)
        """
        if not content:
            return content, None
        
        if not preferences:
            preferences = {}
        
        instructions = []
        
        # 1. 基础指令
        base_config = self.loader.load_base_instructions()
        if base_config and "common" in base_config:
            common = base_config["common"]
            if "avoid_stiff_opening" in common:
                instructions.append(common["avoid_stiff_opening"])
        
        # 2. 响应风格
        response_style = preferences.get("response_style", "standard")
        style_config = self.loader.load_response_style(response_style)
        if style_config and "instructions" in style_config:
            instructions.append(style_config["instructions"])
        
        # 3. 风格预设
        style_preset = preferences.get("style_preset")
        if style_preset:
            preset_config = self.loader.load_style_preset(style_preset)
            if preset_config and "instructions" in preset_config:
                instructions.append(preset_config["instructions"])
        
        # 4. 输出格式
        if preferences.get("prefer_list"):
            base_config = self.loader.load_base_instructions()
            if base_config and "common" in base_config:
                list_instruction = base_config["common"].get("use_list_format")
                if list_instruction:
                    instructions.append(list_instruction)
        
        # 5. 语言
        language = preferences.get("default_language", "zh-CN")
        lang_config = self.loader.load_language(language)
        if lang_config and "instruction" in lang_config:
            instructions.append(lang_config["instruction"])
        
        instruction_text = "\n\n".join(instructions).strip()
        
        logger.debug(
            f"Built user message with preferences",
            extra={
                "response_style": response_style,
                "has_instructions": bool(instruction_text)
            }
        )
        
        return content, instruction_text if instruction_text else None
    
    def reload_configs(self):
        """重新加载配置(热更新)"""
        self.loader.clear_cache()
        logger.info("Prompt builder configs reloaded")

