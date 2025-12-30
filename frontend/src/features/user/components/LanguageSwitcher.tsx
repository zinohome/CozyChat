import React from 'react';
import { Select } from 'antd';
import { useUIStore } from '@/store/slices/uiSlice';

const { Option } = Select;

/**
 * 语言切换组件
 *
 * 切换应用语言。
 */
export const LanguageSwitcher: React.FC = () => {
  const { language, setLanguage } = useUIStore();

  return (
    <Select
      value={language}
      onChange={setLanguage}
      style={{ width: 120 }}
    >
      <Option value="zh-CN">中文</Option>
      <Option value="en-US">English</Option>
    </Select>
  );
};

