/**
 * 工具 API 服务
 */

import { apiClient } from './api';
import type {
  ToolsListResponse,
  ExecuteToolRequest,
  ExecuteToolResponse,
} from '@/types/tools';

/**
 * 工具 API
 */
export const toolsApi = {
  /**
   * 获取工具列表
   * 
   * @param type - 工具类型过滤：builtin/mcp/all（可选）
   * @returns 工具列表
   */
  async listTools(type?: 'builtin' | 'mcp' | 'all'): Promise<ToolsListResponse> {
    const params = type ? { type } : {};
    return apiClient.get<ToolsListResponse>('/v1/tools', { params });
  },

  /**
   * 执行工具
   * 
   * @param request - 执行工具请求
   * @returns 执行结果
   */
  async executeTool(request: ExecuteToolRequest): Promise<ExecuteToolResponse> {
    return apiClient.post<ExecuteToolResponse>('/v1/tools/execute', request);
  },
};

