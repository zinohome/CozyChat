"""工具调用处理服务

负责解析、执行工具调用,并格式化结果
"""

# 标准库
import json
from typing import Any, Dict, List, Optional

# 本地库
from app.engines.tools.factory import ToolManagerFactory
from app.utils.logger import logger
from app.utils.token_utils import estimate_tokens


class ToolCallHandler:
    """工具调用处理器
    
    处理AI生成的工具调用请求,执行工具并返回结果
    """
    
    def __init__(self, tool_factory: ToolManagerFactory):
        """初始化ToolCallHandler
        
        Args:
            tool_factory: 工具管理器工厂
        """
        self.tool_factory = tool_factory
    
    async def execute_tool_calls(
        self,
        tool_call_chunks: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        available_tokens: Optional[int] = 500
    ) -> List[Dict[str, Any]]:
        """执行工具调用并返回结果
        
        Args:
            tool_call_chunks: 工具调用列表
            max_tokens: 最大token限制
            available_tokens: 可用于工具结果的token数
            
        Returns:
            List[Dict[str, Any]]: 工具执行结果列表
        """
        tool_manager = self.tool_factory.get_tool_manager()
        tool_results = []
        
        for tc in tool_call_chunks:
            if not tc or not tc.get("function", {}).get("name"):
                continue
            
            tool_name = tc["function"]["name"]
            try:
                # 解析参数
                args = json.loads(tc["function"].get("arguments", "{}"))
                
                # 执行工具
                result = await tool_manager.execute_tool(
                    tool_name=tool_name,
                    parameters=args
                )
                
                # 格式化结果(content应该是字符串,不是JSON字符串)
                if result.get("success"):
                    result_content = result.get("result", "")
                    # 如果结果是字典或列表,转换为JSON字符串;否则直接使用字符串
                    if isinstance(result_content, (dict, list)):
                        result_content = json.dumps(result_content, ensure_ascii=False)
                    else:
                        result_content = str(result_content)
                    
                    # 截断过长的工具结果
                    if available_tokens:
                        result_content = self._truncate_result(
                            result_content,
                            available_tokens
                        )
                    
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id", ""),
                        "content": result_content
                    })
                else:
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id", ""),
                        "content": f"工具执行失败: {result.get('error', 'Unknown error')}"
                    })
                
                logger.info(
                    f"Tool executed: {tool_name}",
                    extra={"tool_name": tool_name, "success": result.get("success")}
                )
            except Exception as e:
                logger.error(f"Tool execution error: {e}", exc_info=True)
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": f"工具执行出错: {str(e)}"
                })
        
        return tool_results
    
    def _truncate_result(
        self,
        result_content: str,
        available_tokens: int
    ) -> str:
        """截断过长的工具结果
        
        Args:
            result_content: 工具结果内容
            available_tokens: 可用token数
            
        Returns:
            str: 截断后的内容
        """
        result_tokens = estimate_tokens(result_content)
        
        if result_tokens > available_tokens:
            # 计算可以保留的字符数(大约2字符/token)
            max_chars = available_tokens * 2
            if len(result_content) > max_chars:
                truncated_content = result_content[:max_chars] + f"\n\n[结果已截断，原始长度: {len(result_content)} 字符]"
                logger.warning(
                    f"Tool result truncated",
                    extra={
                        "original_length": len(result_content),
                        "truncated_length": len(truncated_content),
                        "original_tokens": result_tokens,
                        "truncated_tokens": estimate_tokens(truncated_content)
                    }
                )
                return truncated_content
        
        return result_content
    
    @staticmethod
    def format_tool_calls_for_message(
        tool_call_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """格式化工具调用为消息格式
        
        Args:
            tool_call_chunks: 工具调用列表
            
        Returns:
            List[Dict[str, Any]]: 格式化后的工具调用列表
        """
        formatted_calls = []
        for tc in tool_call_chunks:
            if tc and tc.get("function", {}).get("name"):
                formatted_calls.append({
                    "id": tc.get("id", ""),
                    "type": tc.get("type", "function"),
                    "function": tc.get("function", {})
                })
        return formatted_calls

