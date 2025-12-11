/**
 * personalityApi服务测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { personalityApi } from './personality';
import { apiClient } from './api';

// Mock apiClient
vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe('personalityApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该获取人格列表', async () => {
    const mockPersonalities = [
      {
        id: 'personality-1',
        name: 'Personality 1',
        description: 'Description 1',
      },
      {
        id: 'personality-2',
        name: 'Personality 2',
        description: 'Description 2',
      },
    ];
    (apiClient.get as any).mockResolvedValue(mockPersonalities);

    const result = await personalityApi.getPersonalities();
    
    expect(apiClient.get).toHaveBeenCalledWith('/v1/personalities');
    expect(result).toEqual(mockPersonalities);
    expect(result).toHaveLength(2);
  });

  it('应该获取单个人格', async () => {
    const mockPersonality = {
      id: 'personality-1',
      name: 'Personality 1',
      description: 'Description 1',
    };
    (apiClient.get as any).mockResolvedValue(mockPersonality);

    const result = await personalityApi.getPersonality('personality-1');
    
    expect(apiClient.get).toHaveBeenCalledWith('/v1/personalities/personality-1');
    expect(result).toEqual(mockPersonality);
  });
});
