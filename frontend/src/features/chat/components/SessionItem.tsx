import React from 'react';
import { List, Button, Space, Typography } from 'antd';
import { DeleteOutlined, EditOutlined } from '@ant-design/icons';
import type { Session } from '@/types/session';
import { format } from 'date-fns';

const { Text } = Typography;

/**
 * 会话项组件属性
 */
interface SessionItemProps {
  /** 会话数据 */
  session: Session;
  /** 是否选中 */
  isActive?: boolean;
  /** 选择回调 */
  onSelect?: () => void;
  /** 删除回调 */
  onDelete?: () => void;
}

/**
 * 会话项组件
 *
 * 显示单个会话项，支持选择和删除。
 */
export const SessionItem: React.FC<SessionItemProps> = ({
  session,
  isActive = false,
  onSelect,
  onDelete,
}) => {
  const formattedTime = session.last_message_at
    ? format(
        typeof session.last_message_at === 'string'
          ? new Date(session.last_message_at)
          : session.last_message_at,
        'MM-dd HH:mm'
      )
    : format(
        typeof session.created_at === 'string'
          ? new Date(session.created_at)
          : session.created_at,
        'MM-dd HH:mm'
      );

  return (
    <List.Item
      style={{
        padding: '12px 16px',
        cursor: 'pointer',
        backgroundColor: isActive ? '#f0f0f0' : 'transparent',
        borderLeft: isActive ? '3px solid #1890ff' : '3px solid transparent',
      }}
      onClick={onSelect}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = '#f5f5f5';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = isActive ? '#f0f0f0' : 'transparent';
      }}
    >
      <div style={{ width: '100%' }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <Text strong style={{ display: 'block', marginBottom: '4px' }}>
              {session.title || '未命名会话'}
            </Text>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {formattedTime}
            </Text>
          </div>
          <Space>
            <Button
              type="text"
              icon={<EditOutlined />}
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                // TODO: 实现编辑功能
              }}
            />
            <Button
              type="text"
              icon={<DeleteOutlined />}
              size="small"
              danger
              onClick={(e) => {
                e.stopPropagation();
                onDelete?.();
              }}
            />
          </Space>
        </Space>
      </div>
    </List.Item>
  );
};

