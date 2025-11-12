import React, { useState, useEffect } from 'react';
import { List, Button, Space, Typography } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { useSessions } from '../hooks/useSessions';
import { SessionItem } from './SessionItem';
import { personalityApi } from '@/services/personality';
import { showError } from '@/utils/errorHandler';
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
  /** 默认人格ID（可选，如果不提供则自动获取） */
  defaultPersonalityId?: string;
}

/**
 * 会话列表组件
 *
 * 显示会话列表，支持创建、删除、切换会话。
 */
export const SessionList: React.FC<SessionListProps> = ({
  currentSessionId,
  onSessionSelect,
  defaultPersonalityId,
}) => {
  const { sessions, isLoading, createSession, deleteSession, updateSession } = useSessions();
  
  // 调试：输出会话列表状态
  useEffect(() => {
    console.log('SessionList - sessions:', sessions, 'isLoading:', isLoading);
  }, [sessions, isLoading]);
  const [personalityId, setPersonalityId] = useState<string>(defaultPersonalityId || 'default');
  const [isLoadingPersonality, setIsLoadingPersonality] = useState(!defaultPersonalityId);

  // 获取默认人格ID（优先使用 health_assistant）
  useEffect(() => {
    if (!defaultPersonalityId) {
      const loadDefaultPersonality = async () => {
        try {
          setIsLoadingPersonality(true);
          const personalities = await personalityApi.getPersonalities();
          if (personalities.length > 0) {
            // 优先选择 health_assistant，如果不存在则使用第一个
            const healthAssistant = personalities.find(p => p.id === 'health_assistant');
            setPersonalityId(healthAssistant?.id || personalities[0].id);
          } else {
            // 如果没有可用人格，使用 'default'
            setPersonalityId('default');
          }
        } catch (error) {
          // 如果获取失败，使用默认值 'default'
          console.warn('Failed to load personalities, using default:', error);
          setPersonalityId('default');
        } finally {
          setIsLoadingPersonality(false);
        }
      };
      loadDefaultPersonality();
    }
  }, [defaultPersonalityId]);

  /**
   * 创建新会话
   */
  const handleCreateSession = async () => {
    // 如果人格ID还在加载中，等待加载完成
    if (isLoadingPersonality) {
      showError(new Error('正在加载人格信息，请稍候...'), '创建会话失败');
      return;
    }

    // 确保有有效的 personality_id
    if (!personalityId) {
      showError(new Error('未找到可用的人格，无法创建会话'), '创建会话失败');
      return;
    }

    try {
      const newSession = await createSession({
        title: '新会话',
        personality_id: personalityId, // 必需字段
      });
      if (onSessionSelect && newSession.id) {
        onSessionSelect(newSession.id);
      }
    } catch (error) {
      showError(error, '创建会话失败');
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
      // 错误已在useSessions Hook中处理
    }
  };

  /**
   * 更新会话
   */
  const handleUpdateSession = async (session: Session) => {
    // useSessions Hook已经处理了缓存更新，这里不需要额外操作
    // 但可以触发重新获取以确保数据同步
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
            loading={isLoadingPersonality}
            disabled={isLoadingPersonality || !personalityId}
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
            onUpdate={handleUpdateSession}
          />
        )}
      />
    </div>
  );
};

