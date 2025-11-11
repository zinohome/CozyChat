import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Input, Button, Spin, Alert } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useChatStore } from '@/store/slices/chatSlice';
import { useStreamChat } from '../hooks/useStreamChat';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { chatApi } from '@/services/chat';
import { MessageBubble } from './MessageBubble';
import { showError } from '@/utils/errorHandler';
import type { Message } from '@/types/chat';

const { TextArea } = Input;

/**
 * 增强聊天容器组件属性
 */
interface EnhancedChatContainerProps {
  /** 会话ID */
  sessionId: string;
  /** 人格ID */
  personalityId: string;
}

/**
 * 增强聊天容器组件
 *
 * 使用自定义消息渲染，支持Markdown、代码高亮和消息操作。
 */
export const EnhancedChatContainer: React.FC<EnhancedChatContainerProps> = ({
  sessionId,
  personalityId,
}) => {
  const { messages, setMessages, isLoading, error, setError, removeMessage } = useChatStore();
  const { sendStreamMessage, isStreaming } = useStreamChat(sessionId, personalityId);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<any>(null);
  const isMobile = useIsMobile();

  // 显示错误提示
  useEffect(() => {
    if (error) {
      showError(error);
      setError(null);
    }
  }, [error, setError]);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
        showError(error, '加载历史消息失败');
        return [];
      }
    },
    enabled: !!sessionId && sessionId !== 'default',
    staleTime: 5 * 60 * 1000, // 5分钟
  });

  /**
   * 处理发送消息
   */
  const handleSend = useCallback(async () => {
    if (!inputValue.trim() || isLoading || isStreaming) return;

    const content = inputValue.trim();
    setInputValue('');
    await sendStreamMessage(content);
    
    // 聚焦输入框
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  }, [inputValue, isLoading, isStreaming, sendStreamMessage]);

  /**
   * 处理键盘事件
   */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  /**
   * 处理删除消息
   */
  const handleDeleteMessage = useCallback(
    (messageId: string) => {
      removeMessage(messageId);
    },
    [removeMessage]
  );

  /**
   * 处理编辑消息
   */
  const handleEditMessage = useCallback(
    (messageId: string, newContent: string) => {
      // 更新消息内容
      const updatedMessages = messages.map((msg) =>
        msg.id === messageId ? { ...msg, content: newContent } : msg
      );
      setMessages(updatedMessages);
      // TODO: 调用API更新后端消息
    },
    [messages, setMessages]
  );

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#fff',
      }}
    >
      {/* 消息列表 */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: isMobile ? '12px' : '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        {isLoadingHistory ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" />
          </div>
        ) : messages.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              padding: '40px',
              color: '#999',
            }}
          >
            开始对话吧！
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                id={msg.id}
                role={msg.role}
                content={
                  typeof msg.content === 'string'
                    ? msg.content
                    : (msg.content as any)?.text || ''
                }
                timestamp={msg.timestamp}
                onDelete={handleDeleteMessage}
                onEdit={handleEditMessage}
              />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* 输入区域 */}
      <div
        style={{
          borderTop: '1px solid #e8e8e8',
          padding: '12px 16px',
          backgroundColor: '#fafafa',
        }}
      >
        <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
          <TextArea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息... (Shift+Enter换行)"
            autoSize={{ minRows: 1, maxRows: 4 }}
            disabled={isLoading || isStreaming}
            style={{ flex: 1 }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={isLoading || isStreaming}
            disabled={!inputValue.trim() || isLoading || isStreaming}
          >
            发送
          </Button>
        </div>
      </div>
    </div>
  );
};

