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
      const response = await sessionApi.getSessions();
      return response.items;
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
        old.map((s) => (s.id === updatedSession.id ? updatedSession : s))
      );
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

