/**
 * 虚拟滚动消息列表组件
 * 
 * 使用 react-window 实现虚拟滚动，优化大量消息的渲染性能。
 */

import React, { useMemo, useRef, useEffect, useCallback } from 'react';
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
 */
const MessageItem: React.FC<RowComponentProps<{
  messages: Message[];
  isVoiceCallActive: boolean;
  voiceCallMessages: Message[];
  onDeleteMessage: (id: string) => void;
  personalityId: string;
  autoPlayingMessageId: string | null;
  onStopAutoPlay: () => void;
  preferences?: UserPreferences;
}>> = React.memo(({ index, style, rowProps: data }) => {
  // 安全检查：确保消息存在
  if (!data.messages || index >= data.messages.length) {
    return <div style={style} />;
  }
  
  const msg = data.messages[index];
  if (!msg) {
    return <div style={style} />;
  }
  
  // 判断是否为语音通话消息
  const isVoiceCallMsg = 
    (data.isVoiceCallActive && data.voiceCallMessages.some(vm => vm.id === msg.id)) ||
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
        onDelete={data.onDeleteMessage}
        personalityId={data.personalityId}
        isAutoPlaying={data.autoPlayingMessageId === msg.id}
        onStopAutoPlay={data.onStopAutoPlay}
        isVoiceCall={isVoiceCallMsg}
        preferences={data.preferences}
      />
    </div>
  );
}, (prevProps, nextProps) => {
  // 自定义比较函数，优化重渲染
  // 安全检查：确保消息存在
  if (
    !prevProps.rowProps.messages || 
    !nextProps.rowProps.messages ||
    prevProps.index >= prevProps.rowProps.messages.length ||
    nextProps.index >= nextProps.rowProps.messages.length
  ) {
    return false; // 索引越界，需要重新渲染
  }
  
  const prevMsg = prevProps.rowProps.messages[prevProps.index];
  const nextMsg = nextProps.rowProps.messages[nextProps.index];
  
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
    (prevProps.rowProps.isVoiceCallActive && prevProps.rowProps.voiceCallMessages.some(vm => vm.id === prevMsg.id)) ||
    (prevMsg.metadata?.is_voice_call === true);
  const nextIsVoiceCall = 
    (nextProps.rowProps.isVoiceCallActive && nextProps.rowProps.voiceCallMessages.some(vm => vm.id === nextMsg.id)) ||
    (nextMsg.metadata?.is_voice_call === true);
  
  if (prevIsVoiceCall !== nextIsVoiceCall) {
    return false; // 语音通话状态变化，需要重新渲染
  }
  
  // 检查自动播放状态是否变化
  if (prevProps.rowProps.autoPlayingMessageId !== nextProps.rowProps.autoPlayingMessageId) {
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
  itemSize, // 固定项高度（已废弃，react-window 2.x 使用动态高度）
}) => {
  const listRef = useRef<ListImperativeAPI>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
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
  
  // 自动滚动到底部（当新消息到达时）
  useEffect(() => {
    if (listRef.current && messages.length > 0) {
      // 延迟滚动，确保DOM已更新
      setTimeout(() => {
        if (listRef.current) {
          listRef.current.scrollToRow({
            index: messages.length - 1,
            align: 'end',
            behavior: 'smooth',
          });
        }
      }, 100);
    }
  }, [messages.length]);
  
  // 如果消息数量较少（< 50），不使用虚拟滚动，直接渲染
  if (messages.length < 50) {
    return (
      <div style={{ height: '100%', overflowY: 'auto', overflowX: 'hidden' }}>
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
        <div ref={messagesEndRef} />
      </div>
    );
  }
  
  // 使用虚拟滚动渲染大量消息
  // react-window 2.x 使用统一的 List 组件，支持动态高度
  return (
    <div style={{ height: '100%', width: '100%' }}>
      <List
        listRef={listRef}
        rowCount={messages.length}
        rowHeight={estimateItemSize || (() => 100)}
        rowComponent={MessageItem}
        rowProps={rowProps}
        overscanCount={5} // 预渲染5个额外项目，提升滚动体验
        style={{ 
          height: `${height}px`,
          width: '100%',
          padding: 0,
        }}
      />
    </div>
  );
};

