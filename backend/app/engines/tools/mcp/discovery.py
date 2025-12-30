"""
MCP工具发现

自动发现和注册MCP服务器的工具
"""

# 标准库
import os
import re
from typing import Any, Dict, List, Optional

# 本地库
from app.config.config import settings
from app.engines.tools.registry import ToolRegistry
from app.utils.logger import logger
from app.utils.config_loader import get_config_loader
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
    
    def _resolve_env_vars(self, value: str) -> str:
        """解析环境变量占位符
        
        Args:
            value: 可能包含 ${VAR_NAME} 格式的字符串
            
        Returns:
            str: 解析后的字符串
        """
        if not isinstance(value, str):
            return value
        
        # 匹配 ${VAR_NAME} 格式
        pattern = r'\$\{([^}]+)\}'
        
        def replace_var(match):
            var_name = match.group(1)
            # 先从 settings 获取，如果没有则从环境变量获取
            env_value = getattr(settings, var_name.lower(), None)
            if env_value is None:
                env_value = os.getenv(var_name)
            if env_value is None:
                logger.warning(f"Environment variable {var_name} not found, using empty string")
                return ""
            return str(env_value)
        
        return re.sub(pattern, replace_var, value)
    
    def _prepare_env(self, env_config: Dict[str, Any]) -> Dict[str, str]:
        """准备环境变量字典
        
        Args:
            env_config: 环境变量配置字典
            
        Returns:
            Dict[str, str]: 解析后的环境变量字典
        """
        env = {}
        for key, value in env_config.items():
            if isinstance(value, str):
                # 解析环境变量占位符
                env[key] = self._resolve_env_vars(value)
            else:
                env[key] = str(value)
        return env
    
    async def discover_from_config(self) -> Dict[str, List[str]]:
        """从配置发现MCP服务器
        
        从 config/tools/mcp.yaml 加载MCP服务器配置并发现工具
        
        Returns:
            Dict[str, List[str]]: 服务器名称到工具列表的映射
        """
        logger.info("Discovering MCP servers from config")
        
        try:
            # 加载MCP配置
            config_loader = get_config_loader()
            tool_config = config_loader.load_tool_config()
            mcp_config = tool_config.get("mcp", {})
            
            # 获取服务器列表
            servers = mcp_config.get("servers", [])
            
            if not servers:
                logger.info("No MCP servers configured")
                return {}
            
            # 检查是否启用自动发现
            discovery_config = mcp_config.get("discovery", {})
            if not discovery_config.get("enabled", True):
                logger.info("MCP discovery is disabled in config")
                return {}
            
            results = {}
            
            for server_config in servers:
                server_name = server_config.get("name")
                enabled = server_config.get("enabled", True)
                
                if not server_name:
                    logger.warning("MCP server config missing 'name' field, skipping")
                    continue
                
                if not enabled:
                    logger.info(f"MCP server '{server_name}' is disabled, skipping")
                    continue
                
                # 构建命令
                command = server_config.get("command")
                args = server_config.get("args", [])
                
                if not command:
                    logger.warning(f"MCP server '{server_name}' missing 'command' field, skipping")
                    continue
                
                # 构建完整命令列表
                full_command = [command] + args
                
                # 准备环境变量
                env_config = server_config.get("env", {})
                env = self._prepare_env(env_config)
                
                # 发现服务器工具
                logger.info(
                    f"Discovering MCP server: {server_name}",
                    extra={"server_name": server_name, "command": full_command}
                )
                
                tools = await self.discover_server(
                    server_name=server_name,
                    command=full_command,
                    env=env if env else None
                )
                
                results[server_name] = tools
            
            logger.info(
                f"MCP discovery completed: {len(results)} servers, {sum(len(tools) for tools in results.values())} tools",
                extra={"servers": list(results.keys())}
            )
            
            return results
            
        except Exception as e:
            logger.error(
                f"Failed to discover MCP servers from config: {e}",
                exc_info=True
            )
            return {}
    
    async def close_all(self):
        """关闭所有MCP客户端连接"""
        for server_name, client in self.clients.items():
            try:
                await client.close()
            except Exception as e:
                logger.error(f"Failed to close MCP client {server_name}: {e}", exc_info=True)
        
        self.clients.clear()
        logger.info("All MCP clients closed")

