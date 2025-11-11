import React, { useState } from 'react';
import { Layout, Menu, Tabs } from 'antd';
import {
  MessageOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useUIStore } from '@/store/slices/uiSlice';
import { SessionList } from '@/features/chat/components/SessionList';

const { Sider } = Layout;

/**
 * 侧边栏组件
 *
 * 显示导航菜单和会话列表。
 */
export const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { sidebarOpen } = useUIStore();
  const [activeTab, setActiveTab] = useState('sessions');
  
  // 从URL路径中提取sessionId
  const sessionId = location.pathname.startsWith('/chat/')
    ? location.pathname.split('/chat/')[1] || undefined
    : undefined;

  const menuItems = [
    {
      key: '/chat',
      icon: <MessageOutlined />,
      label: '聊天',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleSessionSelect = (selectedSessionId: string) => {
    if (selectedSessionId) {
      navigate(`/chat/${selectedSessionId}`);
    } else {
      navigate('/chat');
    }
  };

  if (!sidebarOpen) {
    return null;
  }

  const tabItems = [
    {
      key: 'sessions',
      label: '会话',
      children: (
        <SessionList
          currentSessionId={sessionId}
          onSessionSelect={handleSessionSelect}
        />
      ),
    },
    {
      key: 'menu',
      label: '菜单',
      children: (
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
        />
      ),
    },
  ];

  return (
    <Sider
      width={280}
      style={{
        background: '#fff',
        borderRight: '1px solid #e8e8e8',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
        tabBarStyle={{ margin: 0, padding: '0 16px' }}
      />
    </Sider>
  );
};

