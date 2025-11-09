import React, { useState, useMemo } from 'react';
import { Input } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import type { Session } from '@/types/session';

/**
 * 会话搜索组件属性
 */
interface SessionSearchProps {
  /** 会话列表 */
  sessions: Session[];
  /** 搜索回调 */
  onSearch?: (filteredSessions: Session[]) => void;
}

/**
 * 会话搜索组件
 *
 * 提供会话搜索功能。
 */
export const SessionSearch: React.FC<SessionSearchProps> = ({
  sessions,
  onSearch,
}) => {
  const [searchText, setSearchText] = useState('');

  /**
   * 过滤会话
   */
  const filteredSessions = useMemo(() => {
    if (!searchText.trim()) {
      return sessions;
    }

    const lowerSearchText = searchText.toLowerCase();
    return sessions.filter(
      (session) =>
        session.title?.toLowerCase().includes(lowerSearchText) ||
        session.personality_name?.toLowerCase().includes(lowerSearchText)
    );
  }, [sessions, searchText]);

  /**
   * 处理搜索文本变化
   */
  const handleSearchChange = (value: string) => {
    setSearchText(value);
    onSearch?.(filteredSessions);
  };

  return (
    <Input
      prefix={<SearchOutlined />}
      placeholder="搜索会话..."
      value={searchText}
      onChange={(e) => handleSearchChange(e.target.value)}
      allowClear
      style={{ marginBottom: '16px' }}
    />
  );
};

