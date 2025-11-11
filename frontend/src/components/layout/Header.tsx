import React from 'react';
import { Layout, Button, Space, Avatar, Dropdown } from 'antd';
import {
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  MenuOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/store/slices/authSlice';
import { useUIStore } from '@/store/slices/uiSlice';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { useNavigate } from 'react-router-dom';

const { Header: AntHeader } = Layout;

/**
 * 顶部导航组件
 *
 * 显示应用标题、用户信息和导航菜单。
 */
export const Header: React.FC = () => {
  const { user } = useAuthStore();
  const { toggleSidebar, toggleMobileMenu } = useUIStore();
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      // 错误已在useAuth Hook中处理
    }
  };

  const userMenu = {
    items: [
      {
        key: 'profile',
        icon: <UserOutlined />,
        label: '个人资料',
        onClick: () => navigate('/settings'),
      },
      {
        key: 'settings',
        icon: <SettingOutlined />,
        label: '设置',
        onClick: () => navigate('/settings'),
      },
      {
        type: 'divider' as const,
      },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '退出登录',
        onClick: handleLogout,
      },
    ],
  };

  return (
    <AntHeader
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        background: '#fff',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <Button
          type="text"
          icon={<MenuOutlined />}
          onClick={toggleSidebar}
        />
        <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 'bold' }}>
          CozyChat
        </h1>
      </div>

      <Space>
        {user ? (
          <Dropdown menu={userMenu} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <span>{user.username}</span>
            </Space>
          </Dropdown>
        ) : (
          <Button type="primary" onClick={() => navigate('/login')}>
            登录
          </Button>
        )}
      </Space>
    </AntHeader>
  );
};

