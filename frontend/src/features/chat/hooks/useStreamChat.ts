import { useState, useCallback, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { chatApi } from '@/services/chat';
import { useChatStore } from '@/store/slices/chatSlice';
import type { ChatRequest, Message, StreamChunk } from '@/types/chat';

/**
 * 流式聊天Hook
 *
 * 处理SSE流式响应，支持历史消息上下文。
 */
export const useStreamChat = (
  sessionId: string,
  personalityId: string
) => {
  const queryClient = useQueryClient();
  const { messages, addMessage, updateMessage, setLoading, setError } = useChatStore();
  const [isStreaming, setIsStreaming] = useState(false);
  const currentMessageIdRef = useRef<string | null>(null);

  /**
   * 发送流式消息
   */
  const sendStreamMessage = useCallback(
    async (content: string) => {
      setIsStreaming(true);
      setLoading(true);
      setError(null);

      try {
        // 添加用户消息
        const userMessage: Message = {
          id: `user-${Date.now()}`,
          role: 'user',
          content,
          timestamp: new Date(),
          session_id: sessionId,
        };
        addMessage(userMessage);

        // 创建AI消息占位符
        const aiMessageId = `assistant-${Date.now()}`;
        currentMessageIdRef.current = aiMessageId;
        const aiMessage: Message = {
          id: aiMessageId,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          session_id: sessionId,
        };
        addMessage(aiMessage);

        // 构建消息列表（包含历史消息）
        const currentMessages = messages.length > 0 ? messages : 
          (queryClient.getQueryData<Message[]>(['chat', 'messages', sessionId]) || []);
        
        const messageList = [
          ...currentMessages.map((m) => ({
            role: m.role,
            content: typeof m.content === 'string' 
              ? m.content 
              : (m.content as any)?.text || '',
          })),
          { role: 'user' as const, content },
        ];

        // 构建请求
        const request: ChatRequest = {
          messages: messageList,
          personality_id: personalityId,
          session_id: sessionId,
          stream: true,
          use_memory: true,
        };

        // 处理流式响应
        let accumulatedContent = '';
        for await (const chunk of chatApi.streamChat(request)) {
          const deltaContent = chunk.choices?.[0]?.delta?.content || '';
          if (deltaContent) {
            accumulatedContent += deltaContent;
            updateMessage(aiMessageId, {
              content: accumulatedContent,
            });
          }

          // 检查是否完成
          if (chunk.choices?.[0]?.finish_reason) {
            break;
          }
        }

        // 更新最终消息时间戳
        updateMessage(aiMessageId, {
          timestamp: new Date(),
        });

        // 更新React Query缓存
        queryClient.setQueryData(
          ['chat', 'messages', sessionId],
          (old: Message[] = []) => {
            const updated = old.map((msg) => 
              msg.id === aiMessageId 
                ? { ...msg, content: accumulatedContent, timestamp: new Date() }
                : msg
            );
            // 确保用户消息也在缓存中
            const hasUserMessage = updated.some((msg) => msg.id === userMessage.id);
            if (!hasUserMessage) {
              return [...updated, userMessage];
            }
            return updated;
          }
        );

        setLoading(false);
        setIsStreaming(false);
        currentMessageIdRef.current = null;
      } catch (error: any) {
        const failedMessageId = currentMessageIdRef.current;
        setError(error.message || '流式响应失败');
        setLoading(false);
        setIsStreaming(false);
        currentMessageIdRef.current = null;
        
        // 如果出错，删除占位符消息
        if (failedMessageId) {
          const state = useChatStore.getState();
          useChatStore.setState({
            messages: state.messages.filter((msg) => msg.id !== failedMessageId),
          });
        }
      }
    },
    [sessionId, personalityId, messages, addMessage, updateMessage, setLoading, setError, queryClient]
  );

  /**
   * 停止流式响应
   */
  const stopStream = useCallback(() => {
    setIsStreaming(false);
    setLoading(false);
  }, [setLoading]);

  return {
    sendStreamMessage,
    isStreaming,
    stopStream,
  };
};

