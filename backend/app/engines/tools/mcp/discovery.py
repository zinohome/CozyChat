"""
MCP工具发现

自动发现和注册MCP服务器的工具
"""

# 标准库
from typing import Any, Dict, List, Optional

# 本地库
from app.config.config import settings
from app.engines.tools.registry import ToolRegistry
from app.utils.logger import logger
from .client import MCPClient
from .adapters import MCPToolAdapter


class MCPDiscovery:
    """MCP工具发现器
    
    自动发现MCP服务器的工具并注册到工具注册中心
    """
    
    def __init__(self):
        """初始化MCP发现器"""
        self.clients: Dict[str, MCPClient] = {}
        self.registry = ToolRegistry()
        
        logger.info("MCP discovery initialized")
    
    async def discover_server(
        self,
        server_name: str,
        command: List[str],
        env: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """发现MCP服务器的工具
        
        Args:
            server_name: 服务器名称
            command: 启动服务器的命令
            env: 环境变量（可选）
            
        Returns:
            List[str]: 发现的工具名称列表
        """
        try:
            # 创建MCP客户端
            client = MCPClient(server_name, command, env)
            self.clients[server_name] = client
            
            # 初始化连接
            await client.initialize()
            
            # 列出工具
            tools = await client.list_tools()
            
            # 注册工具
            registered_tools = []
            for tool_info in tools:
                tool_name = tool_info.get("name")
                if not tool_name:
                    continue
                
                # 创建工具适配器
                adapter = MCPToolAdapter(client, server_name, tool_info)
                
                # 注册工具（使用server_name__tool_name格式）
                full_tool_name = f"{server_name}__{tool_name}"
                ToolRegistry.register(full_tool_name, type(adapter))
                
                registered_tools.append(full_tool_name)
                
                logger.info(
                    f"Discovered MCP tool: {full_tool_name}",
                    extra={"server_name": server_name, "tool_name": tool_name}
                )
            
            logger.info(
                f"MCP server discovery completed: {server_name}",
                extra={"server_name": server_name, "tools_count": len(registered_tools)}
            )
            
            return registered_tools
            
        except Exception as e:
            logger.error(
                f"MCP server discovery failed: {server_name}",
                exc_info=True,
                extra={"server_name": server_name, "error": str(e)}
            )
            return []
    
    async def discover_from_config(self) -> Dict[str, List[str]]:
        """从配置发现MCP服务器
        
        Returns:
            Dict[str, List[str]]: 服务器名称到工具列表的映射
        """
        # 这里应该从配置文件读取MCP服务器配置
        # 简化实现：返回空字典
        logger.info("Discovering MCP servers from config")
        
        # 示例：从环境变量或配置文件读取MCP服务器配置
        # mcp_servers = getattr(settings, "mcp_servers", {})
        
        results = {}
        # for server_name, config in mcp_servers.items():
        #     tools = await self.discover_server(
        #         server_name=server_name,
        #         command=config.get("command", []),
        #         env=config.get("env", {})
        #     )
        #     results[server_name] = tools
        
        return results
    
    async def close_all(self):
        """关闭所有MCP客户端连接"""
        for server_name, client in self.clients.items():
            try:
                await client.close()
            except Exception as e:
                logger.error(f"Failed to close MCP client {server_name}: {e}", exc_info=True)
        
        self.clients.clear()
        logger.info("All MCP clients closed")

