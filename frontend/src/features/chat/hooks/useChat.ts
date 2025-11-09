import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useChatStore } from '@/store/slices/chatSlice';
import { chatApi } from '@/services/chat';
import { sessionApi } from '@/services/session';
import type { ChatRequest, Message } from '@/types/chat';

/**
 * 聊天Hook
 *
 * 使用React Query管理聊天相关的服务端状态。
 */
export const useChat = (sessionId: string, personalityId: string) => {
  const queryClient = useQueryClient();
  const { 
    messages, 
    setMessages, 
    addMessage, 
    setLoading, 
    setError 
  } = useChatStore();

  // 获取历史消息
  const { data: historyMessages = [], isLoading: isLoadingHistory } = useQuery({
    queryKey: ['chat', 'messages', sessionId],
    queryFn: async () => {
      if (!sessionId) return [];
      const response = await chatApi.getHistory(sessionId);
      setMessages(response);
      return response;
    },
    enabled: !!sessionId,
    staleTime: 5 * 60 * 1000, // 5分钟
  });

  // 发送消息Mutation
  const sendMutation = useMutation({
    mutationFn: async (content: string) => {
      setLoading(true);
      setError(null);

      // 构建消息列表
      const messageList = [
        ...historyMessages.map((m) => ({
          role: m.role,
          content: typeof m.content === 'string' ? m.content : (m.content as any).text || '',
        })),
        { role: 'user' as const, content },
      ];

      // 发送请求
      const request: ChatRequest = {
        messages: messageList,
        personality_id: personalityId,
        session_id: sessionId,
        stream: false,
        use_memory: true,
      };

      const response = await chatApi.send(request);

      // 添加用户消息
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date(),
        session_id: sessionId,
      };
      addMessage(userMessage);

      // 添加AI消息
      const aiMessage: Message = {
        id: response.id || `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.choices[0]?.message?.content || '',
        timestamp: new Date(response.created * 1000),
        session_id: sessionId,
      };
      addMessage(aiMessage);

      // 更新缓存
      queryClient.setQueryData(
        ['chat', 'messages', sessionId],
        (old: Message[] = []) => [...old, userMessage, aiMessage]
      );

      return response;
    },
    onError: (error: any) => {
      setError(error.message || '发送消息失败');
      setLoading(false);
    },
    onSuccess: () => {
      setLoading(false);
    },
  });

  /**
   * 发送消息
   */
  const sendMessage = async (content: string) => {
    await sendMutation.mutateAsync(content);
  };

  return {
    messages: messages.length > 0 ? messages : historyMessages,
    isLoading: isLoadingHistory || sendMutation.isPending,
    sendMessage,
    isSending: sendMutation.isPending,
    error: useChatStore.getState().error,
  };
};

