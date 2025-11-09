import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Chat } from '@chatui/core';
import '@chatui/core/dist/index.css';
import { useChat } from '../hooks/useChat';
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
 * 使用ChatUI核心组件构建聊天界面。
 */
export const ChatContainer: React.FC<ChatContainerProps> = ({
  sessionId,
  personalityId,
}) => {
  const { messages, sendMessage, isLoading } = useChat(sessionId, personalityId);

  /**
   * 处理发送消息
   */
  const handleSend = useCallback(
    async (type: string, val: string) => {
      if (type === 'text' && val.trim()) {
        await sendMessage(val);
      }
    },
    [sendMessage]
  );

  /**
   * 转换消息格式为ChatUI格式
   */
  const chatUIMessages = messages.map((msg) => ({
    _id: msg.id,
    type: 'text',
    content: { text: typeof msg.content === 'string' ? msg.content : msg.content.text || '' },
    user: {
      id: msg.role === 'user' ? 'user' : 'assistant',
      avatar: msg.role === 'user' ? '👤' : '🤖',
    },
    createdAt: typeof msg.timestamp === 'string' 
      ? new Date(msg.timestamp).getTime() 
      : msg.timestamp instanceof Date 
        ? msg.timestamp.getTime() 
        : Date.now(),
  }));

  return (
    <Chat
      navbar={{
        title: 'CozyChat',
      }}
      messages={chatUIMessages}
      onSend={handleSend}
      placeholder="输入消息..."
      locale="zh-CN"
      loading={isLoading}
    />
  );
};

