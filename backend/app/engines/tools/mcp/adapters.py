"""
MCP工具适配器

将MCP工具适配为统一的工具接口
"""

# 标准库
from typing import Any, Dict

# 本地库
from app.engines.tools.base import Tool, ToolType
from app.utils.logger import logger
from .client import MCPClient


class MCPToolAdapter(Tool):
    """MCP工具适配器
    
    将MCP工具适配为统一的工具接口
    """
    
    def __init__(
        self,
        mcp_client: MCPClient,
        server_name: str,
        tool_info: Dict[str, Any]
    ):
        """初始化MCP工具适配器
        
        Args:
            mcp_client: MCP客户端
            server_name: 服务器名称
            tool_info: 工具信息
        """
        super().__init__(tool_type=ToolType.MCP)
        self.mcp_client = mcp_client
        self.server_name = server_name
        self.tool_info = tool_info
        self._name = tool_info.get("name", "")
        self._description = tool_info.get("description", "")
        
        # 解析参数schema
        input_schema = tool_info.get("inputSchema", {})
        self._parameters = input_schema.get("properties", {})
        
        logger.debug(
            f"Initializing MCP tool adapter: {self.name}",
            extra={"server_name": server_name, "tool_name": self._name}
        )
    
    @property
    def name(self) -> str:
        """工具名称（格式：server_name__tool_name）"""
        return f"{self.server_name}__{self._name}"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return self._description
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return self._parameters
    
    async def execute(self, **kwargs: Any) -> Any:
        """执行MCP工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            Any: 工具执行结果
        """
        try:
            result = await self.mcp_client.call_tool(
                server_name=self.server_name,
                tool_name=self._name,
                arguments=kwargs
            )
            
            logger.info(
                f"MCP tool executed: {self.name}",
                extra={"server_name": self.server_name, "tool_name": self._name}
            )
            
            return result
            
        except Exception as e:
            error_msg = f"MCP工具执行失败: {str(e)}"
            logger.error(
                f"MCP tool execution failed: {self.name}",
                exc_info=True,
                extra={"server_name": self.server_name, "tool_name": self._name, "error": str(e)}
            )
            return error_msg

