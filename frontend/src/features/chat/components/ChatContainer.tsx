import React, { useCallback, useEffect } from 'react';
import { Chat } from '@chatui/core';
import '@chatui/core/dist/index.css';
import { Alert } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { useChatStore } from '@/store/slices/chatSlice';
import { useStreamChat } from '../hooks/useStreamChat';
import { chatApi } from '@/services/chat';
import { showError } from '@/utils/errorHandler';
import type { Message } from '@/types/chat';

/**
 * 聊天容器组件属性
 */
interface ChatContainerProps {
  /** 会话ID */
  sessionId: string;
  /** 人格ID */
  personalityId: string;
}

/**
 * 聊天容器组件
 *
 * 使用ChatUI核心组件构建聊天界面，支持流式响应。
 */
export const ChatContainer: React.FC<ChatContainerProps> = ({
  sessionId,
  personalityId,
}) => {
  const { messages, setMessages, isLoading, error, setError } = useChatStore();
  const { sendStreamMessage, isStreaming } = useStreamChat(sessionId, personalityId);

  // 显示错误提示
  useEffect(() => {
    if (error) {
      showError(error);
      // 清除错误状态
      setError(null);
    }
  }, [error, setError]);

  // 获取历史消息
  const { isLoading: isLoadingHistory } = useQuery({
    queryKey: ['chat', 'messages', sessionId],
    queryFn: async () => {
      if (!sessionId || sessionId === 'default') return [];
      try {
        const response = await chatApi.getHistory(sessionId);
        setMessages(response);
        return response;
      } catch (error) {
        console.error('Failed to load history:', error);
        return [];
      }
    },
    enabled: !!sessionId && sessionId !== 'default',
    staleTime: 5 * 60 * 1000, // 5分钟
  });

  /**
   * 处理发送消息
   */
  const handleSend = useCallback(
    async (type: string, val: string) => {
      if (type === 'text' && val.trim()) {
        await sendStreamMessage(val);
      }
    },
    [sendStreamMessage]
  );

  /**
   * 转换消息格式为ChatUI格式
   */
  const chatUIMessages = messages.map((msg) => {
    const content = typeof msg.content === 'string' 
      ? msg.content 
      : (msg.content as any)?.text || '';
    
    return {
      _id: msg.id,
      type: 'text' as const,
      content: { text: content },
      user: {
        id: msg.role === 'user' ? 'user' : 'assistant',
        avatar: msg.role === 'user' ? '👤' : '🤖',
      },
      createdAt: typeof msg.timestamp === 'string' 
        ? new Date(msg.timestamp).getTime() 
        : msg.timestamp instanceof Date 
          ? msg.timestamp.getTime() 
          : Date.now(),
    };
  });

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {error && (
        <Alert
          type="error"
          message={error}
          closable
          onClose={() => setError(null)}
          style={{ margin: '8px' }}
        />
      )}
      <Chat
        navbar={{
          title: 'CozyChat',
        }}
        messages={chatUIMessages}
        onSend={handleSend}
        placeholder="输入消息..."
        locale="zh-CN"
        loading={isLoading || isLoadingHistory || isStreaming}
      />
    </div>
  );
};

