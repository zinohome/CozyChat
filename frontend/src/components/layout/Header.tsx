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
import { useIsMobile } from '@/hooks/useMediaQuery';
import { Logo } from './Logo';

const { Header: AntHeader } = Layout;

/**
 * 顶部导航组件
 *
 * 显示应用标题、Logo、用户信息和导航菜单。
 */
export const Header: React.FC = () => {
  const { user } = useAuthStore();
  const { toggleSidebar, sidebarOpen } = useUIStore();
  const { logout } = useAuth();
  const navigate = useNavigate();
  const isMobile = useIsMobile();
  
  // 在窄屏幕下，只有当侧边栏打开时才显示切换按钮
  const shouldShowMenuButton = !isMobile || (isMobile && sidebarOpen);

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
        padding: '0 16px 0 12px',
        background: 'var(--header-gradient)',
        boxShadow: 'var(--shadow-md)',
        height: '64px',
        lineHeight: '64px',
        backdropFilter: 'blur(10px)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        {shouldShowMenuButton && (
        <Button
          type="text"
          icon={<MenuOutlined />}
          onClick={toggleSidebar}
            style={{
              color: '#fff',
              fontSize: '18px',
            }}
        />
        )}
        <div style={{ marginRight: '4px' }}>
          <Logo size={40} />
        </div>
        <h1
          style={{
            margin: 0,
            fontSize: '20px',
            fontWeight: 'bold',
            color: '#fff',
            textShadow: '0 1px 2px rgba(0,0,0,0.1)',
          }}
        >
          CozyChat
        </h1>
      </div>

      <Space>
        {user ? (
          <Dropdown menu={userMenu} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar
                icon={<UserOutlined />}
                style={{
                  backgroundColor: 'rgba(255,255,255,0.2)',
                  border: '2px solid rgba(255,255,255,0.3)',
                }}
              />
              <span style={{ color: '#fff', fontWeight: 500 }}>
                {user.username}
              </span>
            </Space>
          </Dropdown>
        ) : (
          <Button
            type="primary"
            onClick={() => navigate('/login')}
            style={{
              backgroundColor: 'rgba(255,255,255,0.2)',
              borderColor: 'rgba(255,255,255,0.3)',
              color: '#fff',
            }}
          >
            登录
          </Button>
        )}
      </Space>
    </AntHeader>
  );
};

