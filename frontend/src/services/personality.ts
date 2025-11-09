import { apiClient } from './api';
import type { Personality } from '@/types/personality';

/**
 * 人格API服务
 *
 * 封装人格相关的API调用。
 */
export const personalityApi = {
  /**
   * 获取人格列表
   */
  async getPersonalities(): Promise<Personality[]> {
    return apiClient.get<Personality[]>('/v1/personalities');
  },

  /**
   * 获取单个人格
   */
  async getPersonality(personalityId: string): Promise<Personality> {
    return apiClient.get<Personality>(`/v1/personalities/${personalityId}`);
  },
};

