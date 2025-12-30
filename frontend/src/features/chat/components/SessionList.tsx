import React from 'react';
import { List } from 'antd';
import { useSessions } from '../hooks/useSessions';
import { SessionItem } from './SessionItem';
import type { Session } from '@/types/session';

/**
 * 会话列表组件属性
 */
interface SessionListProps {
  /** 当前选中的会话ID */
  currentSessionId?: string;
  /** 会话选择回调 */
  onSessionSelect?: (sessionId: string) => void;
  /** 是否在Popover中显示（影响样式） */
  inPopover?: boolean;
}

/**
 * 会话列表组件
 *
 * 显示会话列表，支持创建、删除、切换会话。
 */
export const SessionList: React.FC<SessionListProps> = ({
  currentSessionId,
  onSessionSelect,
  inPopover = false,
}) => {
  const { sessions, isLoading, deleteSession, updateSession } = useSessions();

  /**
   * 删除会话
   */
  const handleDeleteSession = async (sessionId: string) => {
    try {
      await deleteSession(sessionId);
      if (currentSessionId === sessionId && onSessionSelect) {
        onSessionSelect('');
      }
    } catch (error) {
      // 错误已在useSessions Hook中处理
    }
  };

  /**
   * 更新会话
   */
  const handleUpdateSession = async (_session: Session) => {
    // useSessions Hook已经处理了缓存更新，这里不需要额外操作
    // 但可以触发重新获取以确保数据同步
  };

  return (
    <div 
      style={{ 
        height: inPopover ? 'auto' : '100%', 
        display: 'flex', 
        flexDirection: 'column',
        maxHeight: inPopover ? '400px' : 'none',
      }}
    >
      <List
        dataSource={sessions}
        loading={isLoading}
        style={{ 
          flex: 1, 
          overflow: inPopover ? 'auto' : 'auto',
          maxHeight: inPopover ? '400px' : 'none',
        }}
        renderItem={(session: Session) => (
          <SessionItem
            key={session.id || session.session_id}
            session={session}
            isActive={(session.id || session.session_id) === currentSessionId}
            onSelect={() => onSessionSelect?.(session.id || session.session_id || '')}
            onDelete={() => handleDeleteSession(session.id || session.session_id || '')}
            onUpdate={handleUpdateSession}
          />
        )}
      />
    </div>
  );
};

