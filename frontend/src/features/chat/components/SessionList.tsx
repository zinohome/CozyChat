import React from 'react';
import { List, Button, Space, Typography } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { useSessions } from '../hooks/useSessions';
import { SessionItem } from './SessionItem';
import type { Session } from '@/types/session';

const { Title } = Typography;

/**
 * 会话列表组件属性
 */
interface SessionListProps {
  /** 当前选中的会话ID */
  currentSessionId?: string;
  /** 会话选择回调 */
  onSessionSelect?: (sessionId: string) => void;
}

/**
 * 会话列表组件
 *
 * 显示会话列表，支持创建、删除、切换会话。
 */
export const SessionList: React.FC<SessionListProps> = ({
  currentSessionId,
  onSessionSelect,
}) => {
  const { sessions, isLoading, createSession, deleteSession } = useSessions();

  /**
   * 创建新会话
   */
  const handleCreateSession = async () => {
    try {
      const newSession = await createSession({
        title: '新会话',
      });
      if (onSessionSelect) {
        onSessionSelect(newSession.id);
      }
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

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
      console.error('Failed to delete session:', error);
    }
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '16px', borderBottom: '1px solid #e8e8e8' }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Title level={4} style={{ margin: 0 }}>
            会话列表
          </Title>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreateSession}
            size="small"
          >
            新建
          </Button>
        </Space>
      </div>

      <List
        dataSource={sessions}
        loading={isLoading}
        style={{ flex: 1, overflow: 'auto' }}
        renderItem={(session) => (
          <SessionItem
            key={session.id}
            session={session}
            isActive={session.id === currentSessionId}
            onSelect={() => onSessionSelect?.(session.id)}
            onDelete={() => handleDeleteSession(session.id)}
          />
        )}
      />
    </div>
  );
};

