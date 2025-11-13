import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sessionApi } from '@/services/session';
import { useChatStore } from '@/store/slices/chatSlice';
import { useAuthStore } from '@/store/slices/authSlice';
import type { Session, CreateSessionRequest, UpdateSessionRequest } from '@/types/session';

/**
 * 会话Hook
 *
 * 使用React Query管理会话相关的服务端状态。
 */
export const useSessions = () => {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const userId = user?.id || null;

  // 获取会话列表（按用户隔离）
  const { data: sessions = [], isLoading, error: sessionsError } = useQuery({
    queryKey: ['sessions', userId],
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
    enabled: !!userId, // 只有用户ID存在时才查询
    staleTime: 1 * 60 * 1000, // 1分钟
    retry: 1, // 只重试1次
    retryDelay: 1000, // 重试延迟1秒
  });

  // 创建会话Mutation
  const createMutation = useMutation({
    mutationFn: (request: CreateSessionRequest) => sessionApi.createSession(request),
    onSuccess: async (newSession) => {
      if (!userId) return;
      
      const sessionId = newSession.id || newSession.session_id;
      
      // 更新会话列表缓存（按用户隔离）
      queryClient.setQueryData(['sessions', userId], (old: Session[] = []) => [
        newSession,
        ...old,
      ]);
      
      // 移除消息缓存，然后显式触发重新查询（确保获取到欢迎消息）
      queryClient.removeQueries({ queryKey: ['chat', 'messages', sessionId] });
      
      // 更新当前会话ID
      useChatStore.getState().setCurrentSessionId(sessionId);
      
      // 显式触发消息查询（确保欢迎消息能够显示）
      // 使用 refetchQueries 而不是 invalidateQueries，因为 invalidateQueries 可能不会立即执行
      await queryClient.refetchQueries({ 
        queryKey: ['chat', 'messages', sessionId],
        exact: true 
      });
    },
  });

  // 更新会话Mutation
  const updateMutation = useMutation({
    mutationFn: ({ sessionId, request }: { sessionId: string; request: UpdateSessionRequest }) =>
      sessionApi.updateSession(sessionId, request),
    onSuccess: (updatedSession) => {
      if (!userId) return;
      
      // 更新会话列表缓存（按用户隔离）
      queryClient.setQueryData(['sessions', userId], (old: Session[] = []) =>
        old.map((s) => {
          // 支持 id 和 session_id 两种字段
          const currentId = s.id || s.session_id;
          const updatedId = updatedSession.id || updatedSession.session_id;
          return currentId === updatedId ? updatedSession : s;
        })
      );
      
      // 更新会话详情缓存
      queryClient.setQueryData(['session', updatedSession.id || updatedSession.session_id], updatedSession);
      
      // 同时使查询失效，确保数据同步
      queryClient.invalidateQueries({ queryKey: ['sessions', userId] });
    },
  });

  // 删除会话Mutation
  const deleteMutation = useMutation({
    mutationFn: (sessionId: string) => sessionApi.deleteSession(sessionId),
    onSuccess: (_, sessionId) => {
      if (!userId) return;
      
      const { currentSessionId, setCurrentSessionId } = useChatStore.getState();
      
      // 1. 如果当前会话是被删除的会话，切换到其他会话
      if (currentSessionId === sessionId) {
        // 获取会话列表，切换到第一个
        const sessions = queryClient.getQueryData<Session[]>(['sessions', userId]) || [];
        const remainingSessions = sessions.filter(
          (s) => (s.id || s.session_id) !== sessionId
        );
        
        if (remainingSessions.length > 0) {
          setCurrentSessionId(remainingSessions[0].id || remainingSessions[0].session_id);
        } else {
          setCurrentSessionId(null);
        }
      }
      
      // 2. 取消所有正在进行的相关查询（防止404错误）
      queryClient.cancelQueries({ queryKey: ['chat', 'messages', sessionId] });
      queryClient.cancelQueries({ queryKey: ['session', sessionId] });
      
      // 3. 从会话列表缓存移除（按用户隔离）
      queryClient.setQueryData(['sessions', userId], (old: Session[] = []) =>
        old.filter((s) => {
          const currentId = s.id || s.session_id;
          return currentId !== sessionId;
        })
      );
      
      // 4. 清除 React Query 缓存中的消息和会话详情
      queryClient.removeQueries({ queryKey: ['chat', 'messages', sessionId] });
      queryClient.removeQueries({ queryKey: ['session', sessionId] });
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

