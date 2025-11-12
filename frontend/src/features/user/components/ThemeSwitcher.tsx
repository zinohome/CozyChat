import React from 'react';
import { Select, Space } from 'antd';
import { 
  BgColorsOutlined,
} from '@ant-design/icons';
import { useUIStore, type ThemeName } from '@/store/slices/uiSlice';

/**
 * 主题配置
 */
const themes: Array<{
  value: ThemeName;
  label: string;
  color: string;
}> = [
  { value: 'blue', label: '蓝色', color: '#5e6ad2' },
  { value: 'green', label: '绿色', color: '#22c55e' },
  { value: 'purple', label: '紫色', color: '#a855f7' },
  { value: 'orange', label: '橙色', color: '#f97316' },
  { value: 'pink', label: '粉色', color: '#ec4899' },
  { value: 'cyan', label: '青色', color: '#06b6d4' },
];

/**
 * 主题切换组件
 *
 * 支持多个预设颜色主题切换。
 */
export const ThemeSwitcher: React.FC = () => {
  const { theme, setTheme } = useUIStore();

  return (
    <Select
      value={theme}
      onChange={(value) => setTheme(value)}
      style={{ width: 120 }}
      suffixIcon={<BgColorsOutlined />}
    >
      {themes.map((themeOption) => (
        <Select.Option key={themeOption.value} value={themeOption.value}>
    <Space>
            <span
              style={{
                display: 'inline-block',
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: themeOption.color,
                border: '1px solid var(--border-color)',
              }}
            />
            {themeOption.label}
    </Space>
        </Select.Option>
      ))}
    </Select>
  );
};

