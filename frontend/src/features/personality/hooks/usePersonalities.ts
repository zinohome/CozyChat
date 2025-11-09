import { useQuery } from '@tanstack/react-query';
import { personalityApi } from '@/services/personality';
import type { Personality } from '@/types/personality';

/**
 * 人格Hook
 *
 * 使用React Query管理人格相关的服务端状态。
 */
export const usePersonalities = () => {
  // 获取人格列表
  const { data: personalities = [], isLoading } = useQuery({
    queryKey: ['personalities'],
    queryFn: () => personalityApi.getPersonalities(),
    staleTime: 10 * 60 * 1000, // 10分钟
  });

  return {
    personalities,
    isLoading,
  };
};

