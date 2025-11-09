import { useState, useCallback, useRef } from 'react';
import { chatApi } from '@/services/chat';
import { useChatStore } from '@/store/slices/chatSlice';
import type { ChatRequest, Message, StreamChunk } from '@/types/chat';

/**
 * 流式聊天Hook
 *
 * 处理SSE流式响应。
 */
export const useStreamChat = (
  sessionId: string,
  personalityId: string
) => {
  const { addMessage, updateMessage, setLoading, setError } = useChatStore();
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

        // 构建请求
        const request: ChatRequest = {
          messages: [
            { role: 'user', content },
          ],
          personality_id: personalityId,
          session_id: sessionId,
          stream: true,
          use_memory: true,
        };

        // 处理流式响应
        let accumulatedContent = '';
        for await (const chunk of chatApi.streamChat(request)) {
          const content = chunk.choices?.[0]?.delta?.content || '';
          if (content) {
            accumulatedContent += content;
            updateMessage(aiMessageId, {
              content: accumulatedContent,
            });
          }

          // 检查是否完成
          if (chunk.choices?.[0]?.finish_reason) {
            break;
          }
        }

        setLoading(false);
        setIsStreaming(false);
      } catch (error: any) {
        setError(error.message || '流式响应失败');
        setLoading(false);
        setIsStreaming(false);
      }
    },
    [sessionId, personalityId, addMessage, updateMessage, setLoading, setError]
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

