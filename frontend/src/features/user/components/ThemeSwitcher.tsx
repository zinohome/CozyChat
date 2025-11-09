import React from 'react';
import { Switch, Space } from 'antd';
import { SunOutlined, MoonOutlined } from '@ant-design/icons';
import { useUIStore } from '@/store/slices/uiSlice';

/**
 * 主题切换组件
 *
 * 切换亮色/暗色主题。
 */
export const ThemeSwitcher: React.FC = () => {
  const { theme, setTheme } = useUIStore();

  const handleChange = (checked: boolean) => {
    setTheme(checked ? 'dark' : 'light');
  };

  const isDark = theme === 'dark';

  return (
    <Space>
      <SunOutlined />
      <Switch checked={isDark} onChange={handleChange} />
      <MoonOutlined />
    </Space>
  );
};

