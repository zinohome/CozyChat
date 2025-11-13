import React from 'react';
import { Drawer, Menu } from 'antd';
import {
  MessageOutlined,
  UserOutlined,
  SettingOutlined,
  CloseOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useUIStore } from '@/store/slices/uiSlice';

/**
 * 移动端导航组件
 *
 * 使用Ant Design Drawer实现移动端导航菜单。
 */
export const MobileNav: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { mobileMenuOpen, setMobileMenuOpen } = useUIStore();

  const menuItems = [
    {
      key: '/chat',
      icon: <MessageOutlined />,
      label: '聊天',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '偏好设置',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
    setMobileMenuOpen(false);
  };

  return (
    <Drawer
      title="导航"
      placement="left"
      open={mobileMenuOpen}
      onClose={() => setMobileMenuOpen(false)}
      closeIcon={<CloseOutlined />}
      width={250}
    >
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
      />
    </Drawer>
  );
};

