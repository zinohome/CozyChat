import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Input, Button, Spin, Alert } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useChatStore } from '@/store/slices/chatSlice';
import { useStreamChat } from '../hooks/useStreamChat';
import { useSessions } from '../hooks/useSessions';
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
  const { messages, setMessages, isLoading, error, setError, removeMessage, setCurrentSessionId, addMessage, updateMessage, setLoading } = useChatStore();
  const { sessions, createSession } = useSessions();
  const queryClient = useQueryClient();
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<any>(null);
  const isMobile = useIsMobile();
  const [currentSessionId, setCurrentSessionIdLocal] = useState(sessionId);
  
  // 使用动态的 sessionId 创建 sendStreamMessage
  const { sendStreamMessage, isStreaming } = useStreamChat(currentSessionId, personalityId);

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

  // 同步 currentSessionId 状态
  useEffect(() => {
    setCurrentSessionIdLocal(sessionId);
  }, [sessionId]);

  // 获取历史消息
  const { isLoading: isLoadingHistory } = useQuery({
    queryKey: ['chat', 'messages', currentSessionId],
    queryFn: async () => {
      if (!currentSessionId || currentSessionId === 'default') return [];
      try {
        const response = await chatApi.getHistory(currentSessionId);
        setMessages(response);
        return response;
      } catch (error) {
        showError(error, '加载历史消息失败');
        return [];
      }
    },
    enabled: !!currentSessionId && currentSessionId !== 'default',
    staleTime: 5 * 60 * 1000, // 5分钟
  });

  /**
   * 处理发送消息
   */
  const handleSend = useCallback(async () => {
    if (!inputValue.trim() || isLoading || isStreaming) return;

    let actualSessionId = currentSessionId;

    // 如果没有有效会话（sessionId 为 'default' 或会话列表为空），自动创建新会话
    if (!actualSessionId || actualSessionId === 'default' || sessions.length === 0) {
      try {
        const newSession = await createSession({
          title: inputValue.trim().slice(0, 30) || '新会话', // 使用消息前30个字符作为标题
          personality_id: personalityId,
        });
        actualSessionId = newSession.id || newSession.session_id;
        if (actualSessionId) {
          setCurrentSessionIdLocal(actualSessionId);
          setCurrentSessionId(actualSessionId);
          // 更新 URL
          if (window.history && window.history.replaceState) {
            window.history.replaceState(null, '', `/chat/${actualSessionId}`);
          }
        } else {
          showError(new Error('创建会话失败：未返回会话ID'), '创建会话失败');
          return;
        }
      } catch (error) {
        showError(error, '创建会话失败');
        return;
      }
    }

    const content = inputValue.trim();
    setInputValue('');
    
    // 如果会话ID已更改，直接使用 chatApi 发送消息（因为不能在回调中调用 hook）
    if (actualSessionId !== currentSessionId) {
      // 直接调用流式聊天 API
      setLoading(true);
      setError(null);

      try {
        // 添加用户消息
        const userMessage: Message = {
          id: `user-${Date.now()}`,
          role: 'user',
          content,
          timestamp: new Date(),
          session_id: actualSessionId,
        };
        addMessage(userMessage);

        // 创建AI消息占位符
        const aiMessageId = `assistant-${Date.now()}`;
        const aiMessage: Message = {
          id: aiMessageId,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          session_id: actualSessionId,
        };
        addMessage(aiMessage);

        // 构建请求
        const request = {
          messages: [{ role: 'user' as const, content }],
          personality_id: personalityId,
          session_id: actualSessionId,
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
          ['chat', 'messages', actualSessionId],
          (old: Message[] = []) => {
            const updated = old.map((msg) => 
              msg.id === aiMessageId 
                ? { ...msg, content: accumulatedContent, timestamp: new Date() }
                : msg
            );
            const hasUserMessage = updated.some((msg) => msg.id === userMessage.id);
            if (!hasUserMessage) {
              return [...updated, userMessage];
            }
            return updated;
          }
        );

        setLoading(false);
      } catch (error: any) {
        setError(error.message || '发送消息失败');
        setLoading(false);
        showError(error, '发送消息失败');
      }
    } else {
      await sendStreamMessage(content);
    }
    
    // 聚焦输入框
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  }, [inputValue, isLoading, isStreaming, sendStreamMessage, currentSessionId, sessions, createSession, personalityId, setCurrentSessionId, addMessage, updateMessage, setLoading, setError, queryClient]);

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
    async (messageId: string) => {
      // 先更新UI
      removeMessage(messageId);

      // 调用API删除后端消息
      if (sessionId && sessionId !== 'default') {
        try {
          await chatApi.deleteMessage(sessionId, messageId);
        } catch (error) {
          // 如果删除失败，恢复消息
          const message = messages.find((msg) => msg.id === messageId);
          if (message) {
            setMessages([...messages, message]);
          }
          showError(error, '删除消息失败');
        }
      }
    },
    [removeMessage, sessionId, messages, setMessages]
  );

  /**
   * 处理编辑消息
   */
  const handleEditMessage = useCallback(
    async (messageId: string, newContent: string) => {
      // 先更新UI
      const updatedMessages = messages.map((msg) =>
        msg.id === messageId ? { ...msg, content: newContent } : msg
      );
      setMessages(updatedMessages);

      // 调用API更新后端消息
      if (sessionId && sessionId !== 'default') {
        try {
          await chatApi.updateMessage(sessionId, messageId, newContent);
        } catch (error) {
          // 如果更新失败，恢复原内容
          setMessages(messages);
          showError(error, '更新消息失败');
        }
      }
    },
    [messages, setMessages, sessionId]
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

