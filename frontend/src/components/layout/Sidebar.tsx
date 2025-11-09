import React from 'react';
import { Layout, Menu } from 'antd';
import {
  MessageOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useUIStore } from '@/store/slices/uiSlice';

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

  if (!sidebarOpen) {
    return null;
  }

  return (
    <Sider
      width={250}
      style={{
        background: '#fff',
        borderRight: '1px solid #e8e8e8',
      }}
    >
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
        style={{ height: '100%', borderRight: 0 }}
      />
    </Sider>
  );
};

