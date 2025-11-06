"""
工具管理器

提供工具执行、并发控制、错误处理等高级功能
"""

# 标准库
import asyncio
from typing import Any, Dict, List, Optional

# 本地库
from app.utils.logger import logger
from .base import Tool, ToolType
from .registry import ToolRegistry


class ToolManager:
    """工具管理器
    
    提供工具执行、并发控制、错误处理等功能
    
    Attributes:
        registry: 工具注册中心
        max_concurrent_tools: 最大并发工具数
        tool_timeout: 工具执行超时时间（秒）
    """
    
    def __init__(
        self,
        max_concurrent_tools: int = 3,
        tool_timeout: float = 30.0
    ):
        """初始化工具管理器
        
        Args:
            max_concurrent_tools: 最大并发工具数
            tool_timeout: 工具执行超时时间（秒）
        """
        self.registry = ToolRegistry()
        self.max_concurrent_tools = max_concurrent_tools
        self.tool_timeout = tool_timeout
        
        logger.info(
            "Tool manager initialized",
            extra={
                "max_concurrent_tools": max_concurrent_tools,
                "tool_timeout": tool_timeout
            }
        )
    
    def create_tool(self, tool_name: str, **kwargs: Any) -> Optional[Tool]:
        """创建工具实例
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具初始化参数
            
        Returns:
            Tool: 工具实例，如果工具不存在返回None
        """
        tool_class = self.registry.get_tool_class(tool_name)
        if tool_class is None:
            logger.warning(f"Tool '{tool_name}' not found in registry")
            return None
        
        try:
            tool = tool_class(**kwargs)
            logger.debug(f"Created tool instance: {tool_name}")
            return tool
        except Exception as e:
            logger.error(f"Failed to create tool '{tool_name}': {e}", exc_info=True)
            return None
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        **tool_kwargs: Any
    ) -> Dict[str, Any]:
        """执行工具
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            **tool_kwargs: 工具初始化参数
            
        Returns:
            Dict[str, Any]: 执行结果，格式：
            {
                "success": bool,
                "result": Any,  # 成功时的结果
                "error": str,   # 失败时的错误信息
                "tool_name": str
            }
        """
        tool = self.create_tool(tool_name, **tool_kwargs)
        if tool is None:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "tool_name": tool_name
            }
        
        try:
            # 验证参数
            tool.validate_parameters(**parameters)
            
            # 执行工具（带超时）
            logger.debug(
                f"Executing tool: {tool_name}",
                extra={"tool_name": tool_name, "parameters": list(parameters.keys())}
            )
            
            result = await asyncio.wait_for(
                tool.execute(**parameters),
                timeout=self.tool_timeout
            )
            
            logger.info(
                f"Tool execution completed: {tool_name}",
                extra={"tool_name": tool_name, "success": True}
            )
            
            return {
                "success": True,
                "result": result,
                "tool_name": tool_name
            }
            
        except asyncio.TimeoutError:
            error_msg = f"Tool '{tool_name}' execution timeout ({self.tool_timeout}s)"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "tool_name": tool_name
            }
        except ValueError as e:
            error_msg = f"Invalid parameters for tool '{tool_name}': {str(e)}"
            logger.warning(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "tool_name": tool_name
            }
        except Exception as e:
            error_msg = f"Tool '{tool_name}' execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "tool_name": tool_name
            }
    
    async def execute_tools_concurrent(
        self,
        tool_calls: List[Dict[str, Any]],
        **tool_kwargs: Any
    ) -> List[Dict[str, Any]]:
        """并发执行多个工具
        
        Args:
            tool_calls: 工具调用列表，每个元素格式：
                {
                    "tool_name": str,
                    "parameters": Dict[str, Any]
                }
            **tool_kwargs: 工具初始化参数
            
        Returns:
            List[Dict[str, Any]]: 执行结果列表，顺序与输入一致
        """
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent_tools)
        
        async def execute_with_semaphore(tool_call: Dict[str, Any]) -> Dict[str, Any]:
            """带信号量的工具执行"""
            async with semaphore:
                return await self.execute_tool(
                    tool_name=tool_call["tool_name"],
                    parameters=tool_call.get("parameters", {}),
                    **tool_kwargs
                )
        
        # 并发执行所有工具
        tasks = [
            execute_with_semaphore(tool_call)
            for tool_call in tool_calls
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Tool execution exception: {result}",
                    exc_info=True,
                    extra={"tool_call": tool_calls[i]}
                )
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "tool_name": tool_calls[i].get("tool_name", "unknown")
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_available_tools(
        self,
        tool_type: Optional[ToolType] = None
    ) -> List[str]:
        """获取可用工具列表
        
        Args:
            tool_type: 工具类型过滤（可选）
            
        Returns:
            List[str]: 工具名称列表
        """
        all_tools = self.registry.list_tools()
        
        if tool_type is None:
            return all_tools
        
        # 过滤指定类型的工具
        filtered_tools = []
        for tool_name in all_tools:
            tool_class = self.registry.get_tool_class(tool_name)
            if tool_class:
                try:
                    tool_instance = tool_class()
                    if tool_instance.tool_type == tool_type:
                        filtered_tools.append(tool_name)
                except Exception:
                    continue
        
        return filtered_tools
    
    def get_tools_for_openai(
        self,
        tool_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """获取OpenAI function calling格式的工具列表
        
        Args:
            tool_names: 工具名称列表（可选，如果不提供则返回所有工具）
            
        Returns:
            List[Dict[str, Any]]: OpenAI function格式的工具列表
        """
        if tool_names is None:
            tool_names = self.registry.list_tools()
        
        tools = []
        for tool_name in tool_names:
            tool = self.create_tool(tool_name)
            if tool:
                tools.append(tool.to_openai_function())
        
        return tools
    
    def health_check(self) -> Dict[str, Any]:
        """工具系统健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        registered_tools = self.registry.list_tools()
        
        return {
            "status": "healthy",
            "registered_tools_count": len(registered_tools),
            "registered_tools": registered_tools,
            "max_concurrent_tools": self.max_concurrent_tools,
            "tool_timeout": self.tool_timeout
        }

