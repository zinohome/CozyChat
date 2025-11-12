import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sessionApi } from '@/services/session';
import { useChatStore } from '@/store/slices/chatSlice';
import type { Session, CreateSessionRequest, UpdateSessionRequest } from '@/types/session';

/**
 * 会话Hook
 *
 * 使用React Query管理会话相关的服务端状态。
 */
export const useSessions = () => {
  const queryClient = useQueryClient();
  const { clearMessagesBySessionId } = useChatStore();

  // 获取会话列表
  const { data: sessions = [], isLoading, error: sessionsError } = useQuery({
    queryKey: ['sessions'],
    queryFn: async () => {
      try {
        const response = await sessionApi.getSessions();
        // 确保返回数组，避免返回 undefined
        const items = response?.items || [];
        console.log('Sessions loaded:', items.length, 'items');
        return items;
      } catch (error) {
        // 查询失败时返回空数组
        console.error('Failed to fetch sessions:', error);
        return [];
      }
    },
    staleTime: 1 * 60 * 1000, // 1分钟
    retry: 1, // 只重试1次
    retryDelay: 1000, // 重试延迟1秒
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
      // 1. 如果当前会话是被删除的会话，先清除当前会话ID（防止后续查询）
      const currentSessionId = useChatStore.getState().currentSessionId;
      if (currentSessionId === sessionId) {
        useChatStore.getState().setCurrentSessionId(null);
      }
      
      // 2. 取消所有正在进行的相关查询（防止404错误）
      queryClient.cancelQueries({ queryKey: ['chat', 'messages', sessionId] });
      queryClient.cancelQueries({ queryKey: ['sessions', sessionId] });
      
      // 3. 更新会话列表缓存
      queryClient.setQueryData(['sessions'], (old: Session[] = []) =>
        old.filter((s) => {
          const currentId = s.id || s.session_id;
          return currentId !== sessionId;
        })
      );
      
      // 4. 清除该会话相关的所有消息
      // 4.1 清除 Zustand store 中的消息
      clearMessagesBySessionId(sessionId);
      
      // 4.2 清除 React Query 缓存中的消息和会话详情
      queryClient.removeQueries({ queryKey: ['chat', 'messages', sessionId] });
      queryClient.removeQueries({ queryKey: ['sessions', sessionId] });
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

