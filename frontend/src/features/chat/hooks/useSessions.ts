import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sessionApi } from '@/services/session';
import type { Session, CreateSessionRequest, UpdateSessionRequest } from '@/types/session';

/**
 * 会话Hook
 *
 * 使用React Query管理会话相关的服务端状态。
 */
export const useSessions = () => {
  const queryClient = useQueryClient();

  // 获取会话列表
  const { data: sessions = [], isLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: async () => {
      try {
        const response = await sessionApi.getSessions();
        // 确保返回数组，避免返回 undefined
        return response?.items || [];
      } catch (error) {
        // 查询失败时返回空数组
        console.error('Failed to fetch sessions:', error);
        return [];
      }
    },
    staleTime: 1 * 60 * 1000, // 1分钟
  });

  // 创建会话Mutation
  const createMutation = useMutation({
    mutationFn: (request: CreateSessionRequest) => sessionApi.createSession(request),
    onSuccess: (newSession) => {
      // 更新缓存
      queryClient.setQueryData(['sessions'], (old: Session[] = []) => [
        newSession,
        ...old,
      ]);
    },
  });

  // 更新会话Mutation
  const updateMutation = useMutation({
    mutationFn: ({ sessionId, request }: { sessionId: string; request: UpdateSessionRequest }) =>
      sessionApi.updateSession(sessionId, request),
    onSuccess: (updatedSession) => {
      // 更新缓存
      queryClient.setQueryData(['sessions'], (old: Session[] = []) =>
        old.map((s) => {
          // 支持 id 和 session_id 两种字段
          const currentId = s.id || s.session_id;
          const updatedId = updatedSession.id || updatedSession.session_id;
          return currentId === updatedId ? updatedSession : s;
        })
      );
      // 同时使查询失效，确保数据同步
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
  });

  // 删除会话Mutation
  const deleteMutation = useMutation({
    mutationFn: (sessionId: string) => sessionApi.deleteSession(sessionId),
    onSuccess: (_, sessionId) => {
      // 更新缓存
      queryClient.setQueryData(['sessions'], (old: Session[] = []) =>
        old.filter((s) => s.id !== sessionId)
      );
    },
  });

  return {
    sessions,
    isLoading,
    createSession: createMutation.mutateAsync,
    updateSession: (sessionId: string, request: UpdateSessionRequest) =>
      updateMutation.mutateAsync({ sessionId, request }),
    deleteSession: deleteMutation.mutateAsync,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
};

