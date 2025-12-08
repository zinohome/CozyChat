"""
工具服务

统一处理工具相关的所有操作，包括执行、验证、列表等
"""

# 标准库
from typing import Any, Dict, List, Optional

# 本地库
from app.engines.tools.factory import ToolManagerFactory
from app.services.chat.tool_handler import ToolCallHandler
from app.utils.logger import logger


class ToolService:
    """工具服务
    
    统一处理工具相关的所有操作
    """
    
    def __init__(self, tool_factory: ToolManagerFactory):
        """初始化ToolService
        
        Args:
            tool_factory: 工具管理器工厂
        """
        self.tool_factory = tool_factory
        self.tool_handler = ToolCallHandler(tool_factory)
        logger.info("ToolService initialized")
    
    async def execute_tool_calls(
        self,
        tool_call_chunks: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        available_tokens: Optional[int] = 500
    ) -> List[Dict[str, Any]]:
        """执行工具调用
        
        Args:
            tool_call_chunks: 工具调用列表
            max_tokens: 最大token限制
            available_tokens: 可用于工具结果的token数
            
        Returns:
            List[Dict[str, Any]]: 工具执行结果列表
        """
        return await self.tool_handler.execute_tool_calls(
            tool_call_chunks=tool_call_chunks,
            max_tokens=max_tokens,
            available_tokens=available_tokens
        )
    
    def format_tool_calls_for_message(
        self,
        tool_call_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """格式化工具调用为消息格式
        
        Args:
            tool_call_chunks: 工具调用列表
            
        Returns:
            List[Dict[str, Any]]: 格式化后的工具调用列表
        """
        return ToolCallHandler.format_tool_calls_for_message(tool_call_chunks)
    
    def get_available_tools(
        self,
        allowed_tools: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """获取可用工具列表
        
        Args:
            allowed_tools: 允许的工具列表（可选，用于过滤）
            
        Returns:
            List[Dict[str, Any]]: 工具列表（OpenAI格式）
        """
        tool_manager = self.tool_factory.get_tool_manager(allowed_tools=allowed_tools)
        return tool_manager.get_tools_for_openai(tool_names=allowed_tools)
    
    async def validate_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证工具调用参数
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            
        Returns:
            Dict[str, Any]: 验证结果 {"valid": bool, "error": str}
        """
        try:
            tool_manager = self.tool_factory.get_tool_manager()
            # 检查工具是否存在
            tools = tool_manager.get_tools_for_openai()
            tool_exists = any(t.get("function", {}).get("name") == tool_name for t in tools)
            
            if not tool_exists:
                return {"valid": False, "error": f"Tool '{tool_name}' not found"}
            
            # 这里可以添加更详细的参数验证逻辑
            return {"valid": True, "error": None}
            
        except Exception as e:
            logger.error(f"Tool validation error: {e}", exc_info=True)
            return {"valid": False, "error": str(e)}
