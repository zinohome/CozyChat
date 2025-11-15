/**
 * 工具管理器
 * 
 * 负责：
 * - 获取工具列表（从后端）
 * - 转换工具格式（适配 RealtimeAgent）
 * - 执行工具调用
 * - 管理工具缓存
 */

import { toolsApi } from '@/services/tools';
import type { ToolInfo, RealtimeTool } from '@/types/tools';

/**
 * 工具缓存项
 */
interface ToolCacheItem {
  tools: ToolInfo[];
  timestamp: number;
}

/**
 * 工具管理器类
 */
export class ToolManager {
  /** 工具缓存（按 personalityId 缓存） */
  private cache: Map<string, ToolCacheItem> = new Map();

  /** 缓存有效期（5分钟） */
  private readonly CACHE_TTL = 5 * 60 * 1000;

  /**
   * 获取工具列表
   * 
   * @param personalityId - 人格ID（用于缓存键）
   * @param type - 工具类型过滤
   * @returns 工具列表
   */
  async getTools(
    personalityId?: string,
    type: 'builtin' | 'mcp' | 'all' = 'all'
  ): Promise<ToolInfo[]> {
    const cacheKey = `${personalityId || 'default'}_${type}`;

    // 检查缓存
    const cached = this.cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < this.CACHE_TTL) {
      console.log(`[ToolManager] 使用缓存的工具列表: ${cacheKey}`);
      return cached.tools;
    }

    // 从后端获取
    console.log(`[ToolManager] 从后端获取工具列表: ${cacheKey}`);
    try {
      const response = await toolsApi.listTools(type);
      const tools = response.tools;

      // 更新缓存
      this.cache.set(cacheKey, {
        tools,
        timestamp: Date.now(),
      });

      return tools;
    } catch (error) {
      console.error('[ToolManager] 获取工具列表失败:', error);
      throw error;
    }
  }

  /**
   * 转换工具格式为 RealtimeAgent 需要的格式
   * 
   * RealtimeAgent 期望的格式：
   * {
   *   type: "function",
   *   function: {
   *     name: string,
   *     description: string,
   *     parameters: object (JSON Schema)
   *   }
   * }
   * 
   * @param tools - 后端返回的工具列表
   * @returns RealtimeAgent 格式的工具列表
   */
  convertToRealtimeFormat(tools: ToolInfo[]): RealtimeTool[] {
    return tools
      .filter((tool) => tool.enabled) // 只包含启用的工具
      .map((tool) => ({
        type: 'function' as const,
        function: {
          name: tool.name,
          description: tool.description,
          parameters: this.convertParameters(tool.parameters),
        },
      }));
  }

  /**
   * 转换参数格式
   * 
   * 确保参数符合 JSON Schema 格式
   * 
   * @param parameters - 后端返回的参数
   * @returns JSON Schema 格式的参数
   */
  private convertParameters(parameters: Record<string, any>): Record<string, any> {
    // 如果已经是标准的 JSON Schema 格式，直接返回
    if (parameters.type && parameters.properties) {
      return parameters;
    }

    // 否则，包装成标准格式
    return {
      type: 'object',
      properties: parameters,
      required: Object.keys(parameters).filter(
        (key) => parameters[key].required === true
      ),
    };
  }

  /**
   * 执行工具调用
   * 
   * @param toolName - 工具名称
   * @param parameters - 工具参数
   * @returns 执行结果
   */
  async executeTool(
    toolName: string,
    parameters: Record<string, any>
  ): Promise<any> {
    console.log(`[ToolManager] 执行工具: ${toolName}`, parameters);

    try {
      const response = await toolsApi.executeTool({
        tool_name: toolName,
        parameters,
      });

      if (!response.success) {
        throw new Error(`工具执行失败: ${response.tool_name}`);
      }

      console.log(
        `[ToolManager] 工具执行成功: ${toolName}`,
        response.result
      );

      return response.result;
    } catch (error) {
      console.error(`[ToolManager] 工具执行失败: ${toolName}`, error);
      throw error;
    }
  }

  /**
   * 清除缓存
   * 
   * @param personalityId - 人格ID（可选，不传则清除所有）
   */
  clearCache(personalityId?: string): void {
    if (personalityId) {
      // 清除特定人格的缓存
      const keysToDelete: string[] = [];
      this.cache.forEach((_, key) => {
        if (key.startsWith(`${personalityId}_`)) {
          keysToDelete.push(key);
        }
      });
      keysToDelete.forEach((key) => this.cache.delete(key));
      console.log(`[ToolManager] 清除缓存: ${personalityId}`);
    } else {
      // 清除所有缓存
      this.cache.clear();
      console.log('[ToolManager] 清除所有缓存');
    }
  }
}

/**
 * 导出单例实例
 */
export const toolManager = new ToolManager();

