/**
 * 虚拟滚动消息列表组件
 * 
 * 使用 react-window 实现虚拟滚动，优化大量消息的渲染性能。
 */

import React, { useMemo, useRef, useEffect } from 'react';
import { List, ListImperativeAPI, RowComponentProps } from 'react-window';
import { MessageBubble } from './MessageBubble';
import type { Message } from '@/types/chat';
import type { UserPreferences } from '@/types/user';

/**
 * 虚拟滚动消息列表属性
 */
interface VirtualizedMessageListProps {
  /** 消息列表 */
  messages: Message[];
  /** 是否正在语音通话 */
  isVoiceCallActive: boolean;
  /** 语音通话消息列表 */
  voiceCallMessages: Message[];
  /** 删除消息回调 */
  onDeleteMessage: (id: string) => void;
  /** 人格ID */
  personalityId: string;
  /** 正在自动播放的消息ID */
  autoPlayingMessageId: string | null;
  /** 停止自动播放回调 */
  onStopAutoPlay: () => void;
  /** 用户偏好设置 */
  preferences?: UserPreferences;
  /** 容器高度 */
  height: number;
  /** 消息项高度估算函数（用于VariableSizeList） */
  estimateItemSize?: (index: number) => number;
  /** 固定项高度（用于FixedSizeList，如果提供则使用FixedSizeList） */
  itemSize?: number;
}

/**
 * 消息项组件（用于虚拟滚动）
 * 
 * react-window 会将 rowProps 中的属性展开到组件 props 中
 */
const MessageItem = React.memo((props: RowComponentProps<{
  messages: Message[];
  isVoiceCallActive: boolean;
  voiceCallMessages: Message[];
  onDeleteMessage: (id: string) => void;
  personalityId: string;
  autoPlayingMessageId: string | null;
  onStopAutoPlay: () => void;
  preferences?: UserPreferences;
}>) => {
  const { index, style, messages, isVoiceCallActive, voiceCallMessages, onDeleteMessage, personalityId, autoPlayingMessageId, onStopAutoPlay, preferences } = props;
  
  // 安全检查：确保消息存在
  if (!messages || index >= messages.length) {
    return <div style={style} />;
  }
  
  const msg = messages[index];
  if (!msg) {
    return <div style={style} />;
  }
  
  // 判断是否为语音通话消息
  const isVoiceCallMsg = 
    (isVoiceCallActive && voiceCallMessages.some((vm: Message) => vm.id === msg.id)) ||
    (msg.metadata?.is_voice_call === true);
  
  return (
    <div style={{ ...style, paddingBottom: '8px' }}>
      <MessageBubble
        key={msg.id}
        id={msg.id}
        role={msg.role === 'user' || msg.role === 'assistant' ? msg.role : 'user'}
        content={
          typeof msg.content === 'string'
            ? msg.content
            : (msg.content as any)?.text || ''
        }
        timestamp={msg.timestamp}
        onDelete={onDeleteMessage}
        personalityId={personalityId}
        isAutoPlaying={autoPlayingMessageId === msg.id}
        onStopAutoPlay={onStopAutoPlay}
        isVoiceCall={isVoiceCallMsg}
        preferences={preferences}
      />
    </div>
  );
}, (prevProps, nextProps) => {
  // 自定义比较函数，优化重渲染
  // 安全检查：确保消息存在
  if (
    !prevProps.messages || 
    !nextProps.messages ||
    prevProps.index >= prevProps.messages.length ||
    nextProps.index >= nextProps.messages.length
  ) {
    return false; // 索引越界，需要重新渲染
  }
  
  const prevMsg = prevProps.messages[prevProps.index];
  const nextMsg = nextProps.messages[nextProps.index];
  
  // 如果消息不存在，需要重新渲染
  if (!prevMsg || !nextMsg) {
    return false;
  }
  
  // 如果消息ID不同，需要重新渲染
  if (prevMsg.id !== nextMsg.id) {
    return false;
  }
  
  // 检查消息内容是否变化
  const prevContent = typeof prevMsg.content === 'string' 
    ? prevMsg.content 
    : (prevMsg.content as any)?.text || '';
  const nextContent = typeof nextMsg.content === 'string' 
    ? nextMsg.content 
    : (nextMsg.content as any)?.text || '';
  
  if (prevContent !== nextContent) {
    return false; // 内容变化，需要重新渲染
  }
  
  // 检查语音通话状态是否变化
  const prevIsVoiceCall = 
    (prevProps.isVoiceCallActive && prevProps.voiceCallMessages.some((vm: Message) => vm.id === prevMsg.id)) ||
    (prevMsg.metadata?.is_voice_call === true);
  const nextIsVoiceCall = 
    (nextProps.isVoiceCallActive && nextProps.voiceCallMessages.some((vm: Message) => vm.id === nextMsg.id)) ||
    (nextMsg.metadata?.is_voice_call === true);
  
  if (prevIsVoiceCall !== nextIsVoiceCall) {
    return false; // 语音通话状态变化，需要重新渲染
  }
  
  // 检查自动播放状态是否变化
  if (prevProps.autoPlayingMessageId !== nextProps.autoPlayingMessageId) {
    return false; // 自动播放状态变化，需要重新渲染
  }
  
  // 其他属性未变化，可以跳过渲染
  return true;
});

MessageItem.displayName = 'MessageItem';

/**
 * 虚拟滚动消息列表组件
 */
export const VirtualizedMessageList: React.FC<VirtualizedMessageListProps> = ({
  messages,
  isVoiceCallActive,
  voiceCallMessages,
  onDeleteMessage,
  personalityId,
  autoPlayingMessageId,
  onStopAutoPlay,
  preferences,
  height,
  estimateItemSize = () => 100, // 默认估算高度100px
}) => {
  const listRef = useRef<ListImperativeAPI>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const lastMessageIdRef = useRef<string | null>(null);
  const lastMessagesLengthRef = useRef<number>(0);
  const lastContentLengthRef = useRef<number>(0); // 跟踪最后一条消息的内容长度，用于检测流式更新
  const lastScrollTimeRef = useRef<number>(0); // 跟踪上次滚动时间，用于节流
  const hasScrolledToBottomRef = useRef<boolean>(false); // 标记是否已经滚动到底部
  const isInitialMountRef = useRef<boolean>(true); // 标记是否是首次挂载
  const firstMessageIdRef = useRef<string | null>(null); // 跟踪第一条消息ID，用于检测会话切换
  
  // 准备虚拟滚动的数据（作为 rowProps 传递给 List）
  const rowProps = useMemo(() => ({
    messages,
    isVoiceCallActive,
    voiceCallMessages,
    onDeleteMessage,
    personalityId,
    autoPlayingMessageId,
    onStopAutoPlay,
    preferences,
  }), [
    messages,
    isVoiceCallActive,
    voiceCallMessages,
    onDeleteMessage,
    personalityId,
    autoPlayingMessageId,
    onStopAutoPlay,
    preferences,
  ]);
  
  // 计算消息的唯一标识（用于检测消息变化）
  const messagesKey = useMemo(() => {
    if (messages.length === 0) return '';
    // 使用最后一条消息的ID和内容长度作为标识
    const lastMsg = messages[messages.length - 1];
    const content = typeof lastMsg.content === 'string' 
      ? lastMsg.content 
      : (lastMsg.content as any)?.text || '';
    return `${lastMsg.id}-${content.length}-${messages.length}`;
  }, [messages]);
  
  // 滚动到底部的辅助函数
  const scrollToBottom = React.useCallback((immediate = false) => {
    if (messages.length === 0) return;
    
    const performScroll = () => {
      // 虚拟滚动模式
      if (messages.length >= 50 && listRef.current) {
        try {
          // react-window 2.x 使用 scrollToItem 方法
          const api = listRef.current as any;
          if (typeof api.scrollToItem === 'function') {
            // 对于流式更新，使用 'end' 对齐，确保滚动到最底部
            api.scrollToItem(messages.length - 1, 'end');
            // 如果内容很长，可能需要额外滚动一点，确保完全显示
            // 使用 requestAnimationFrame 确保 DOM 已更新
            requestAnimationFrame(() => {
              if (containerRef.current) {
                const container = containerRef.current;
                // 确保滚动到最底部
                container.scrollTop = container.scrollHeight;
              }
            });
          } else if (typeof api.scrollToRow === 'function') {
            api.scrollToRow(messages.length - 1, 'end');
            // 同样确保滚动到最底部
            requestAnimationFrame(() => {
              if (containerRef.current) {
                containerRef.current.scrollTop = containerRef.current.scrollHeight;
              }
            });
          } else {
            // 备用方案：直接设置滚动位置
            const container = containerRef.current;
            if (container) {
              container.scrollTop = container.scrollHeight;
            }
          }
        } catch (error) {
          console.warn('Failed to scroll virtualized list:', error);
          // 备用方案：直接滚动容器
          if (containerRef.current) {
            containerRef.current.scrollTop = containerRef.current.scrollHeight;
          }
        }
      }
      // 非虚拟滚动模式
      else if (messages.length < 50) {
        if (messagesEndRef.current) {
          messagesEndRef.current.scrollIntoView({ 
            behavior: immediate ? 'auto' : 'smooth', 
            block: 'end' 
          });
        } else if (containerRef.current) {
          // 如果 messagesEndRef 不可用，直接滚动容器
          containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
      }
      // 备用方案：直接滚动容器
      else if (containerRef.current) {
        containerRef.current.scrollTop = containerRef.current.scrollHeight;
      }
    };
    
    if (immediate) {
      // 立即滚动（用于初始加载）
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          performScroll();
        });
      });
    } else {
      // 延迟滚动（用于新消息和流式更新）
      // 使用 requestAnimationFrame 确保 DOM 已更新
      requestAnimationFrame(() => {
        setTimeout(performScroll, 50); // 减少延迟，提高响应速度
      });
    }
  }, [messages.length]);
  
  // 检测会话切换（通过第一条消息ID变化）
  useEffect(() => {
    if (messages.length > 0) {
      const firstMsgId = messages[0]?.id || null;
      // 如果第一条消息ID变化，说明切换了会话，需要重置状态
      if (firstMessageIdRef.current !== null && firstMessageIdRef.current !== firstMsgId) {
        // 会话已切换，重置状态
        isInitialMountRef.current = true;
        hasScrolledToBottomRef.current = false;
        lastMessageIdRef.current = null;
        lastMessagesLengthRef.current = 0;
      }
      firstMessageIdRef.current = firstMsgId;
    } else {
      // 消息为空时，重置第一条消息ID
      firstMessageIdRef.current = null;
    }
  }, [messages]);
  
  // 初始加载时滚动到底部（页面重新加载时或会话切换时）
  useEffect(() => {
    if (isInitialMountRef.current && messages.length > 0) {
      // 首次挂载且有消息，需要滚动到底部
      // 使用多次 requestAnimationFrame 确保虚拟滚动组件已完全初始化
      const scrollAttempts = [100, 300, 500, 800]; // 多次尝试，确保成功
      
      scrollAttempts.forEach((delay, index) => {
        setTimeout(() => {
          scrollToBottom(index === scrollAttempts.length - 1); // 最后一次使用立即滚动
          hasScrolledToBottomRef.current = true;
        }, delay);
      });
      
      isInitialMountRef.current = false;
    }
  }, [messages.length, scrollToBottom]);
  
  // 自动滚动到底部（当新消息到达或消息内容更新时）
  useEffect(() => {
    // 如果消息为空，重置引用
    if (messages.length === 0) {
      lastMessageIdRef.current = null;
      lastMessagesLengthRef.current = 0;
      lastContentLengthRef.current = 0;
      hasScrolledToBottomRef.current = false;
      return;
    }
    
    const lastMsg = messages[messages.length - 1];
    const lastMsgId = lastMsg?.id || null;
    const content = typeof lastMsg.content === 'string' 
      ? lastMsg.content 
      : (lastMsg.content as any)?.text || '';
    const contentLength = content.length;
    
    const hasNewMessage = lastMsgId !== lastMessageIdRef.current;
    const hasLengthChange = messages.length !== lastMessagesLengthRef.current;
    const hasContentChange = lastMsgId === lastMessageIdRef.current && contentLength !== lastContentLengthRef.current;
    
    // 更新引用
    lastMessageIdRef.current = lastMsgId;
    lastMessagesLengthRef.current = messages.length;
    lastContentLengthRef.current = contentLength;
    
    // 如果有新消息、长度变化或内容变化（流式更新），自动滚动到底部
    // 但跳过初始挂载时的滚动（由上面的 useEffect 处理）
    if ((hasNewMessage || hasLengthChange || hasContentChange) && !isInitialMountRef.current) {
      const now = Date.now();
      const timeSinceLastScroll = now - lastScrollTimeRef.current;
      const SCROLL_THROTTLE_MS = 200; // 流式更新时，最多每200ms滚动一次
      
      // 对于新消息或长度变化，立即滚动
      // 对于流式更新（内容变化），使用时间节流，避免过于频繁的滚动
      const shouldScroll = hasNewMessage || hasLengthChange || (hasContentChange && timeSinceLastScroll >= SCROLL_THROTTLE_MS);
      
      if (shouldScroll) {
        scrollToBottom();
        hasScrolledToBottomRef.current = true;
        lastScrollTimeRef.current = now;
      }
    }
  }, [messagesKey, messages.length, scrollToBottom]);
  
  // 如果消息数量较少（< 50），不使用虚拟滚动，直接渲染
  if (messages.length < 50) {
    return (
      <div 
        ref={containerRef}
        style={{ 
          height: '100%', 
          overflowY: 'auto', 
          overflowX: 'hidden',
          // 隐藏滚动条但保持滚动功能
          scrollbarWidth: 'none', // Firefox
          msOverflowStyle: 'none', // IE/Edge
        }}
        className="hide-scrollbar"
      >
        {messages.map((msg) => {
          const isVoiceCallMsg = 
            (isVoiceCallActive && voiceCallMessages.some(vm => vm.id === msg.id)) ||
            (msg.metadata?.is_voice_call === true);
          return (
            <MessageBubble
              key={msg.id}
              id={msg.id}
              role={msg.role === 'user' || msg.role === 'assistant' ? msg.role : 'user'}
              content={
                typeof msg.content === 'string'
                  ? msg.content
                  : (msg.content as any)?.text || ''
              }
              timestamp={msg.timestamp}
              onDelete={onDeleteMessage}
              personalityId={personalityId}
              isAutoPlaying={autoPlayingMessageId === msg.id}
              onStopAutoPlay={onStopAutoPlay}
              isVoiceCall={isVoiceCallMsg}
              preferences={preferences}
            />
          );
        })}
        <div ref={messagesEndRef} style={{ height: '1px' }} />
      </div>
    );
  }
  
  // 使用虚拟滚动渲染大量消息
  // react-window 2.x 使用统一的 List 组件，支持动态高度
  return (
    <div 
      ref={containerRef}
      style={{ 
        height: '100%', 
        width: '100%',
        // 隐藏滚动条但保持滚动功能
        scrollbarWidth: 'none', // Firefox
        msOverflowStyle: 'none', // IE/Edge
      }}
      className="hide-scrollbar"
    >
      <List
        listRef={listRef}
        rowCount={messages.length}
        rowHeight={estimateItemSize || (() => 100)}
        rowComponent={MessageItem as any}
        rowProps={rowProps}
        overscanCount={5} // 预渲染5个额外项目，提升滚动体验
        style={{ 
          height: `${height}px`,
          width: '100%',
          padding: 0,
        }}
        className="hide-scrollbar"
      />
    </div>
  );
};

