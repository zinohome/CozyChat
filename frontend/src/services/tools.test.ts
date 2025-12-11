/**
 * toolsApi服务测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { toolsApi } from './tools';
import { apiClient } from './api';

// Mock apiClient
vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('toolsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该获取工具列表', async () => {
    const mockTools = {
      tools: [
        { name: 'tool1', description: 'Tool 1' },
        { name: 'tool2', description: 'Tool 2' },
      ],
    };
    (apiClient.get as any).mockResolvedValue(mockTools);

    const result = await toolsApi.listTools();
    
    expect(apiClient.get).toHaveBeenCalledWith('/v1/tools', { params: {} });
    expect(result).toEqual(mockTools);
  });

  it('应该执行工具', async () => {
    const mockResult = { result: 'success' };
    (apiClient.post as any).mockResolvedValue(mockResult);

    const result = await toolsApi.executeTool({
      tool_name: 'tool1',
      arguments: { param: 'value' },
    });
    
    expect(apiClient.post).toHaveBeenCalledWith('/v1/tools/execute', {
      tool_name: 'tool1',
      arguments: { param: 'value' },
    });
    expect(result).toEqual(mockResult);
  });
});
