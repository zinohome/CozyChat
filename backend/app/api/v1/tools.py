"""
工具管理API

提供工具列表查询和执行功能
"""

# 标准库
from typing import Any, Dict, List, Optional

# 第三方库
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

# 本地库
from app.api.deps import get_current_active_user
from app.engines.tools.manager import ToolManager
from app.engines.tools.base import ToolType
from app.models.user import User
from app.utils.logger import logger

router = APIRouter(prefix="/tools", tags=["tools"])


# ===== 请求/响应模型 =====

class ToolInfo(BaseModel):
    """工具信息"""
    name: str = Field(..., description="工具名称")
    type: str = Field(..., description="工具类型：builtin/mcp")
    description: str = Field(..., description="工具描述")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    enabled: bool = Field(default=True, description="是否启用")
    server: Optional[str] = Field(None, description="MCP服务器名称（仅MCP工具）")


class ToolsListResponse(BaseModel):
    """工具列表响应"""
    tools: List[ToolInfo]
    total: int


class ExecuteToolRequest(BaseModel):
    """执行工具请求"""
    tool_name: str = Field(..., description="工具名称")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")


class ExecuteToolResponse(BaseModel):
    """执行工具响应"""
    tool_name: str
    result: Any = Field(..., description="执行结果")
    execution_time: float = Field(..., description="执行时间（秒）")
    success: bool = Field(..., description="是否成功")


# ===== API路由 =====

@router.get("", response_model=ToolsListResponse)
async def list_tools(
    type: Optional[str] = Query(None, description="工具类型过滤：builtin/mcp/all"),
    user: User = Depends(get_current_active_user)
) -> ToolsListResponse:
    """列出所有可用工具
    
    Args:
        type: 工具类型过滤（可选）
        user: 当前用户
        
    Returns:
        ToolsListResponse: 工具列表
    """
    try:
        manager = ToolManager()
        registry = manager.registry
        
        # 获取所有工具
        all_tools = registry.list_tools()
        
        # 类型过滤
        tool_type_filter = None
        if type and type != "all":
            if type == "builtin":
                tool_type_filter = ToolType.BUILTIN
            elif type == "mcp":
                tool_type_filter = ToolType.MCP
        
        # 过滤工具
        if tool_type_filter:
            filtered_tools = manager.get_available_tools(tool_type_filter)
        else:
            filtered_tools = all_tools
        
        # 构建工具信息列表
        tools: List[ToolInfo] = []
        for tool_name in filtered_tools:
            try:
                tool_class = registry.get_tool_class(tool_name)
                if tool_class:
                    # 创建工具实例以获取信息
                    tool = manager.create_tool(tool_name)
                    if tool:
                        tools.append(ToolInfo(
                            name=tool.name,
                            type="builtin" if tool.tool_type == ToolType.BUILTIN else "mcp",
                            description=tool.description,
                            parameters=tool.parameters,
                            enabled=True,
                            server=getattr(tool, 'server', None) if tool.tool_type == ToolType.MCP else None
                        ))
            except Exception as e:
                logger.warning(
                    f"Failed to get info for tool {tool_name}: {e}",
                    exc_info=True
                )
                continue
        
        logger.info(
            "Listed tools",
            extra={"user_id": str(user.id), "count": len(tools), "type": type}
        )
        
        return ToolsListResponse(
            tools=tools,
            total=len(tools)
        )
        
    except Exception as e:
        logger.error(f"Failed to list tools: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tools"
        )


@router.post("/execute", response_model=ExecuteToolResponse)
async def execute_tool(
    request: ExecuteToolRequest,
    user: User = Depends(get_current_active_user)
) -> ExecuteToolResponse:
    """执行单个工具
    
    Args:
        request: 执行工具请求
        user: 当前用户
        
    Returns:
        ExecuteToolResponse: 执行结果
        
    Raises:
        HTTPException: 如果工具不存在或执行失败
    """
    try:
        import time
        start_time = time.time()
        
        manager = ToolManager()
        
        # 执行工具
        result = await manager.execute_tool(
            tool_name=request.tool_name,
            parameters=request.parameters
        )
        
        execution_time = time.time() - start_time
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Tool execution failed")
            )
        
        logger.info(
            "Tool executed",
            extra={
                "user_id": str(user.id),
                "tool_name": request.tool_name,
                "execution_time": execution_time
            }
        )
        
        return ExecuteToolResponse(
            tool_name=request.tool_name,
            result=result.get("result"),
            execution_time=execution_time,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute tool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute tool"
        )

