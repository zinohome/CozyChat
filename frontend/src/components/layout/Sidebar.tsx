import React, { useState, useEffect } from 'react';
import { Layout, Button, Space } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';
import { useUIStore } from '@/store/slices/uiSlice';
import { SessionList } from '@/features/chat/components/SessionList';
import { useSessions } from '@/features/chat/hooks/useSessions';
import { personalityApi } from '@/services/personality';
import { showError } from '@/utils/errorHandler';

const { Sider } = Layout;

/**
 * 侧边栏组件
 *
 * 显示会话列表（已简化，移除重复菜单）。
 */
export const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { sidebarOpen } = useUIStore();
  const { createSession } = useSessions();
  
  // 从URL路径中提取sessionId
  const sessionId = location.pathname.startsWith('/chat/')
    ? location.pathname.split('/chat/')[1] || undefined
    : undefined;

  const [personalityId, setPersonalityId] = useState<string>('default');
  const [isLoadingPersonality, setIsLoadingPersonality] = useState(true);

  // 获取默认人格ID（优先使用 health_assistant）
  useEffect(() => {
    const loadDefaultPersonality = async () => {
      try {
        setIsLoadingPersonality(true);
        const personalities = await personalityApi.getPersonalities();
        if (personalities.length > 0) {
          const healthAssistant = personalities.find(p => p.id === 'health_assistant');
          setPersonalityId(healthAssistant?.id || personalities[0].id);
        } else {
          setPersonalityId('default');
        }
      } catch (error) {
        console.warn('Failed to load personalities, using default:', error);
        setPersonalityId('default');
      } finally {
        setIsLoadingPersonality(false);
      }
    };
    loadDefaultPersonality();
  }, []);

  const handleSessionSelect = (selectedSessionId: string) => {
    if (selectedSessionId) {
      navigate(`/chat/${selectedSessionId}`);
    } else {
      navigate('/chat');
    }
  };

  /**
   * 创建新会话
   */
  const handleCreateSession = async () => {
    if (isLoadingPersonality) {
      showError(new Error('正在加载人格信息，请稍候...'), '创建会话失败');
      return;
    }

    if (!personalityId) {
      showError(new Error('未找到可用的人格，无法创建会话'), '创建会话失败');
      return;
    }

    try {
      const newSession = await createSession({
        title: '新会话',
        personality_id: personalityId,
      });
      if (newSession.id) {
        handleSessionSelect(newSession.id);
      }
    } catch (error) {
      showError(error, '创建会话失败');
    }
  };

  if (!sidebarOpen) {
    return null;
  }

  return (
    <Sider
      width={280}
      style={{
        background: 'var(--bg-primary)',
        borderRight: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        transition: 'background-color 0.3s ease, border-color 0.3s ease',
      }}
    >
      <div
        style={{
          padding: '16px',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          transition: 'border-color 0.3s ease',
        }}
      >
        <span
          style={{
            fontWeight: 'bold',
            fontSize: '16px',
            color: 'var(--text-primary)',
            transition: 'color 0.3s ease',
          }}
        >
          会话列表
        </span>
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
      </div>
      <div style={{ flex: 1, overflow: 'auto' }}>
        <SessionList
          currentSessionId={sessionId}
          onSessionSelect={handleSessionSelect}
        />
      </div>
    </Sider>
  );
};

