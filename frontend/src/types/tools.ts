/**
 * 工具相关类型定义
 */

/**
 * 工具信息
 */
export interface ToolInfo {
  /** 工具名称 */
  name: string;
  /** 工具类型：builtin/mcp */
  type: 'builtin' | 'mcp';
  /** 工具描述 */
  description: string;
  /** 工具参数（JSON Schema 格式） */
  parameters: Record<string, any>;
  /** 是否启用 */
  enabled: boolean;
  /** MCP服务器名称（仅MCP工具） */
  server?: string;
}

/**
 * 工具列表响应
 */
export interface ToolsListResponse {
  /** 工具列表 */
  tools: ToolInfo[];
  /** 总数 */
  total: number;
}

/**
 * 执行工具请求
 */
export interface ExecuteToolRequest {
  /** 工具名称 */
  tool_name: string;
  /** 工具参数 */
  parameters: Record<string, any>;
}

/**
 * 执行工具响应
 */
export interface ExecuteToolResponse {
  /** 工具名称 */
  tool_name: string;
  /** 执行结果 */
  result: any;
  /** 执行时间（秒） */
  execution_time: number;
  /** 是否成功 */
  success: boolean;
}

/**
 * Realtime API 工具格式
 * 
 * 用于传递给 RealtimeAgent 的工具定义
 */
export interface RealtimeTool {
  type: 'function';
  function: {
    name: string;
    description: string;
    parameters: Record<string, any>;
  };
}

