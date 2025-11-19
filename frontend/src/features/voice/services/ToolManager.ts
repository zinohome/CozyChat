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
import { logger } from '@/utils/logger';
import {
  FRONTEND_EXECUTABLE_TOOLS,
  executeFrontendTool,
  getFrontendToolDefinitions,
} from '../tools/builtinTools';
import { tool } from '@openai/agents/realtime';

const log = logger.withTag('ToolManager');

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
      log.debug(`使用缓存的工具列表: ${cacheKey}`);
      return cached.tools;
    }

    // 从后端获取
    log.debug(`从后端获取工具列表: ${cacheKey}`);
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
      log.error('获取工具列表失败:', error);
      throw error;
    }
  }

  /**
   * 创建前端内置工具（使用 tool() 函数）
   * 
   * 只使用前端实现的内置工具，不加载后端工具。
   * 根据 OpenAI Agents SDK 文档：https://openai.github.io/openai-agents-js/guides/tools/
   * 
   * @returns RealtimeAgent 格式的工具列表（使用 tool() 函数创建）
   */
  createFrontendTools(): any[] {
    const toolDefinitions = getFrontendToolDefinitions();
    
    log.debug('创建前端内置工具:', {
      toolCount: toolDefinitions.length,
      toolNames: toolDefinitions.map((t) => t.name),
    });

    return toolDefinitions.map((toolDef) => {
      // 使用 tool() 函数创建工具，包含执行函数
      return tool({
        name: toolDef.name,
        description: toolDef.description,
        parameters: toolDef.parameters,
        // 执行函数：调用 executeFrontendTool
        execute: async (args: Record<string, any>) => {
          log.debug(`工具执行被调用: ${toolDef.name}`, args);
          try {
            const result = await executeFrontendTool(toolDef.name, args);
            // 确保返回字符串（Realtime API 可能需要字符串结果）
            return typeof result === 'string' ? result : JSON.stringify(result);
          } catch (error) {
            log.error(`工具执行失败: ${toolDef.name}`, error);
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            return `错误: ${errorMessage}`;
          }
        },
      });
    });
  }

  /**
   * 转换工具格式为 RealtimeAgent 需要的格式（已废弃，使用 createFrontendTools）
   * 
   * @deprecated 使用 createFrontendTools() 代替
   */
  convertToRealtimeFormat(tools: ToolInfo[]): any[] {
    return tools
      .filter((toolInfo) => toolInfo.enabled) // 只包含启用的工具
      .map((toolInfo) => {
        // 使用 tool() 函数创建工具，包含执行函数
        return tool({
          name: toolInfo.name,
          description: toolInfo.description,
          parameters: this.convertParameters(toolInfo.parameters),
          // 执行函数：调用 toolManager.executeTool
          execute: async (args: Record<string, any>) => {
            log.debug(`工具执行被调用: ${toolInfo.name}`, args);
            try {
              const result = await this.executeTool(toolInfo.name, args);
              // 确保返回字符串（Realtime API 可能需要字符串结果）
              return typeof result === 'string' ? result : JSON.stringify(result);
            } catch (error) {
              log.error(`工具执行失败: ${toolInfo.name}`, error);
              const errorMessage = error instanceof Error ? error.message : 'Unknown error';
              return `错误: ${errorMessage}`;
            }
          },
        });
      });
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
   * 优先在前端执行内置工具（calculator、time、unit_converter、random_generator），
   * 其他工具通过后端 API 执行。
   * 
   * @param toolName - 工具名称
   * @param parameters - 工具参数
   * @returns 执行结果
   */
  async executeTool(
    toolName: string,
    parameters: Record<string, any>
  ): Promise<any> {
    log.debug(`执行工具: ${toolName}`, parameters);

    // 检查是否可以在前端执行
    if (FRONTEND_EXECUTABLE_TOOLS.includes(toolName)) {
      try {
        log.debug(`前端执行工具: ${toolName}`);
        const result = await executeFrontendTool(toolName, parameters);
        log.debug(`工具执行成功（前端）: ${toolName}`, result);
        return result;
      } catch (error) {
        log.error(`前端工具执行失败: ${toolName}`, error);
        // 如果前端执行失败，尝试后端执行（降级策略）
        log.warn(`前端执行失败，尝试后端执行: ${toolName}`);
      }
    }

    // 后端执行（需要 API key 的工具或前端执行失败的情况）
    try {
      log.debug(`后端执行工具: ${toolName}`);
      const response = await toolsApi.executeTool({
        tool_name: toolName,
        parameters,
      });

      if (!response.success) {
        throw new Error(`工具执行失败: ${response.tool_name}`);
      }

      log.debug(
        `工具执行成功（后端）: ${toolName}`,
        response.result
      );

      return response.result;
    } catch (error) {
      log.error(`工具执行失败: ${toolName}`, error);
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
      log.debug(`清除缓存: ${personalityId}`);
    } else {
      // 清除所有缓存
      this.cache.clear();
      log.debug('清除所有缓存');
    }
  }
}

/**
 * 导出单例实例
 */
export const toolManager = new ToolManager();

