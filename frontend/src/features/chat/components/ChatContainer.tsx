import React, { useCallback, useEffect } from 'react';
import Chat from '@chatui/core';
import '@chatui/core/dist/index.css';
import { Alert } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { useChatStore } from '@/store/slices/chatSlice';
import { useStreamChat } from '../hooks/useStreamChat';
import { chatApi } from '@/services/chat';
import { showError } from '@/utils/errorHandler';

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
  const { isLoading: isLoadingStore, error, setError } = useChatStore();
  const { sendStreamMessage } = useStreamChat(sessionId, personalityId);

  // 显示错误提示
  useEffect(() => {
    if (error) {
      showError(error);
      // 清除错误状态
      setError(null);
    }
  }, [error, setError]);

  // 从 React Query 获取消息（自动按 sessionId 隔离）
  const { data: messages = [], isLoading: isLoadingHistory } = useQuery({
    queryKey: ['chat', 'messages', sessionId],
    queryFn: async () => {
      if (!sessionId || sessionId === 'default') return [];
      try {
        const response = await chatApi.getHistory(sessionId);
        return Array.isArray(response) ? response : [];
      } catch (error) {
        showError(error, '加载历史消息失败');
        return [];
      }
    },
    enabled: !!sessionId && sessionId !== 'default',
    staleTime: 5 * 60 * 1000, // 5分钟
  });

  // 合并加载状态（已移除，ChatUI 不支持 loading prop）

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
          title: 'SelfCEO',
        }}
        messages={chatUIMessages}
        onSend={handleSend}
        placeholder="输入消息..."
        locale="zh-CN"
        renderMessageContent={(msg: any) => {
          return <div>{msg.content?.text || ''}</div>;
        }}
      />
    </div>
  );
};

