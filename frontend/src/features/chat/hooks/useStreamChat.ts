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

        // 构建消息列表（包含历史消息）
        // 使用 getState() 获取最新消息，避免依赖项导致的重建
        const currentMessages = useChatStore.getState().messages.length > 0 
          ? useChatStore.getState().messages 
          : (queryClient.getQueryData<Message[]>(['chat', 'messages', sessionId]) || []);
        
        const messageList = [
          ...currentMessages.map((m) => ({
            role: m.role,
            content: typeof m.content === 'string' 
              ? m.content 
              : (m.content as any)?.text || '',
          })),
          { role: 'user' as const, content },
        ];

        // 构建请求（不传model，让后端根据personality_id自动选择）
        const request: ChatRequest = {
          messages: messageList,
          personality_id: personalityId,
          session_id: sessionId,
          stream: true,
          use_memory: true,
        };

        // 处理流式响应
        let accumulatedContent = '';
        let toolCalls: any[] = [];
        let finishReason: string | null = null;
        let lastUpdateTime = 0;
        let pendingUpdate: NodeJS.Timeout | null = null;
        let lastUpdateContent = ''; // 记录上次更新的内容
        const UPDATE_THROTTLE_MS = 150; // 节流：最多每150ms更新一次
        
        // 节流更新函数
        const throttledUpdate = (content: string) => {
          // 如果内容没有变化，直接返回
          if (content === lastUpdateContent) {
            return;
          }
          
          const now = Date.now();
          if (now - lastUpdateTime >= UPDATE_THROTTLE_MS) {
            // 立即更新
            updateMessage(aiMessageId, {
              content,
            });
            lastUpdateTime = now;
            lastUpdateContent = content;
            if (pendingUpdate) {
              clearTimeout(pendingUpdate);
              pendingUpdate = null;
            }
          } else {
            // 延迟更新
            if (pendingUpdate) {
              clearTimeout(pendingUpdate);
            }
            pendingUpdate = setTimeout(() => {
              updateMessage(aiMessageId, {
                content,
              });
              lastUpdateTime = Date.now();
              lastUpdateContent = content;
              pendingUpdate = null;
            }, UPDATE_THROTTLE_MS - (now - lastUpdateTime));
          }
        };
        
        for await (const chunk of chatApi.streamChat(request)) {
          const choice = chunk.choices?.[0];
          const delta = choice?.delta;
          
          // 处理内容增量
          const deltaContent = delta?.content || '';
          if (deltaContent) {
            accumulatedContent += deltaContent;
            // 使用节流更新
            throttledUpdate(accumulatedContent);
          }
          
          // 处理工具调用
          if (delta?.tool_calls) {
            // 合并工具调用（OpenAI流式API会分多个chunk发送）
            for (const toolCall of delta.tool_calls) {
              const index = toolCall.index || 0;
              if (!toolCalls[index]) {
                toolCalls[index] = {
                  id: toolCall.id || '',
                  type: toolCall.type || 'function',
                  function: {
                    name: toolCall.function?.name || '',
                    arguments: toolCall.function?.arguments || '',
                  },
                };
              } else {
                // 合并增量数据
                if (toolCall.id) toolCalls[index].id = toolCall.id;
                if (toolCall.function?.name) toolCalls[index].function.name = toolCall.function.name;
                if (toolCall.function?.arguments) {
                  toolCalls[index].function.arguments += toolCall.function.arguments;
                }
              }
            }
            
            // 显示工具调用信息
            const toolCallText = toolCalls
              .filter(tc => tc.function.name)
              .map(tc => `🔧 调用工具: ${tc.function.name}`)
              .join('\n');
            
            if (toolCallText) {
              updateMessage(aiMessageId, {
                content: accumulatedContent + (accumulatedContent ? '\n\n' : '') + toolCallText,
              });
            }
          }
          
          // 检查完成原因
          if (choice?.finish_reason) {
            finishReason = choice.finish_reason;
            
            // 如果是工具调用，显示完整信息，但不要退出循环（后端会继续生成回复）
            if (finishReason === 'tool_calls' && toolCalls.length > 0) {
              const toolCallText = toolCalls
                .filter(tc => tc.function.name)
                .map(tc => {
                  try {
                    const args = JSON.parse(tc.function.arguments || '{}');
                    const argsStr = Object.entries(args)
                      .map(([k, v]) => `${k}=${v}`)
                      .join(', ');
                    return `🔧 调用工具: ${tc.function.name}(${argsStr})`;
                  } catch {
                    return `🔧 调用工具: ${tc.function.name}`;
                  }
                })
                .join('\n');
              
              // 更新消息，显示工具调用信息
              const currentContent = accumulatedContent || '';
              const displayContent = currentContent 
                ? `${currentContent}\n\n${toolCallText}\n\n⏳ 正在执行工具...`
                : `${toolCallText}\n\n⏳ 正在执行工具...`;
              
              updateMessage(aiMessageId, {
                content: displayContent,
              });
              
              // 重置工具调用列表，准备接收后续回复
              toolCalls = [];
              // 不要 break，继续接收后续的回复内容
            } else {
              // 其他完成原因（如 'stop'），正常退出
              break;
            }
          }
        }

        // 清理待处理的更新
        if (pendingUpdate) {
          clearTimeout(pendingUpdate);
          pendingUpdate = null;
        }
        
        // 更新最终消息内容和时间戳（确保最终内容被保存）
        // 只在内容有变化时才更新
        if (accumulatedContent !== lastUpdateContent) {
          updateMessage(aiMessageId, {
            content: accumulatedContent,
            timestamp: new Date(),
          });
        } else {
          // 只更新时间戳
          updateMessage(aiMessageId, {
            timestamp: new Date(),
          });
        }

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
        // 清理待处理的更新
        if (pendingUpdate) {
          clearTimeout(pendingUpdate);
          pendingUpdate = null;
        }
        
        const failedMessageId = currentMessageIdRef.current;
        setError(error.message || '流式响应失败');
        setLoading(false);
        setIsStreaming(false);
        currentMessageIdRef.current = null;
        
        // 如果出错，删除占位符消息
        if (failedMessageId) {
          const { removeMessage } = useChatStore.getState();
          removeMessage(failedMessageId);
        }
      }
    },
    [sessionId, personalityId, addMessage, updateMessage, setLoading, setError, queryClient]
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

