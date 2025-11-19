import React, { useState } from 'react';
import { Button, Popover, Space } from 'antd';
import { HistoryOutlined, PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { SessionList } from './SessionList';
import { useSessions } from '../hooks/useSessions';
import { useIsMobile } from '@/hooks/useMediaQuery';
import './ChatSessionHeader.css';

/**
 * 聊天会话头部组件属性
 */
interface ChatSessionHeaderProps {
  /** 当前会话ID */
  currentSessionId?: string;
  /** 人格ID（用于创建新会话） */
  personalityId: string;
}

/**
 * 聊天会话头部组件
 * 
 * 在聊天页面顶部显示会话管理按钮（历史图标和新建按钮）。
 * 点击历史图标会弹出会话列表Popover。
 */
export const ChatSessionHeader: React.FC<ChatSessionHeaderProps> = ({
  currentSessionId,
  personalityId,
}) => {
  const navigate = useNavigate();
  const { createSession } = useSessions();
  const isMobile = useIsMobile();
  const [popoverOpen, setPopoverOpen] = useState(false);

  /**
   * 处理会话选择
   */
  const handleSessionSelect = (sessionId: string) => {
    if (sessionId) {
      navigate(`/chat/${sessionId}`);
    } else {
      navigate('/chat');
    }
    // 关闭Popover
    setPopoverOpen(false);
  };

  /**
   * 处理新建会话
   */
  const handleCreateSession = async () => {
    try {
      const newSession = await createSession({
        title: '新会话',
        personality_id: personalityId,
      });
      const newSessionId = newSession.id || newSession.session_id;
      if (newSessionId) {
        navigate(`/chat/${newSessionId}`);
      }
      // 关闭Popover
      setPopoverOpen(false);
    } catch (error) {
      console.error('创建会话失败:', error);
    }
  };

  /**
   * Popover内容
   */
  const popoverContent = (
    <div
      style={{
        width: isMobile ? '280px' : '300px',
        maxHeight: '400px',
        minHeight: '200px',
      }}
    >
      <SessionList
        currentSessionId={currentSessionId}
        onSessionSelect={handleSessionSelect}
        inPopover={true}
      />
    </div>
  );

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'flex-end',
        alignItems: 'center',
        padding: isMobile ? '8px 12px' : '12px 16px',
        borderBottom: '1px solid var(--border-color)',
        background: 'transparent', // 继承父容器的渐变背景
        transition: 'border-color 0.3s ease',
        flexShrink: 0,
      }}
    >
      <Space size="small">
        {/* 会话列表Popover */}
        <Popover
          content={popoverContent}
          title="会话列表"
          placement="bottomRight"
          trigger="click"
          open={popoverOpen}
          onOpenChange={setPopoverOpen}
        >
          <Button
            type="text"
            icon={<HistoryOutlined />}
            size={isMobile ? 'small' : 'middle'}
            style={{
              color: 'var(--text-primary)',
            }}
            styles={{
              icon: {
                color: 'var(--text-primary)',
              }
            }}
            className="session-header-button"
          />
        </Popover>

        {/* 新建会话按钮 */}
        <Button
          type="text"
          icon={<PlusOutlined />}
          size={isMobile ? 'small' : 'middle'}
          onClick={handleCreateSession}
          style={{
            color: 'var(--text-primary)',
          }}
          styles={{
            icon: {
              color: 'var(--text-primary)',
            }
          }}
          className="session-header-button"
        />
      </Space>
    </div>
  );
};

