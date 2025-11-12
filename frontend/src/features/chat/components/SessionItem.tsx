import React, { useState } from 'react';
import { List, Button, Space, Typography, Modal, Input, message } from 'antd';
import { DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { useSessions } from '../hooks/useSessions';
import { showError, showSuccess } from '@/utils/errorHandler';
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
  /** 更新回调 */
  onUpdate?: (session: Session) => void;
}

/**
 * 会话项组件
 *
 * 显示单个会话项，支持选择、编辑和删除。
 */
export const SessionItem: React.FC<SessionItemProps> = ({
  session,
  isActive = false,
  onSelect,
  onDelete,
  onUpdate,
}) => {
  const { updateSession } = useSessions();
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editTitle, setEditTitle] = useState(session.title || '');
  const [isUpdating, setIsUpdating] = useState(false);

  // 格式化时间，处理可能的无效日期
  const formatTime = (dateValue: Date | string | undefined): string => {
    if (!dateValue) {
      return '--';
    }
    
    try {
      const date = typeof dateValue === 'string' ? new Date(dateValue) : dateValue;
      // 检查日期是否有效
      if (isNaN(date.getTime())) {
        return '--';
      }
      return format(date, 'MM-dd HH:mm');
    } catch (error) {
      console.warn('Failed to format date:', dateValue, error);
      return '--';
    }
  };

  const formattedTime = session.last_message_at
    ? formatTime(session.last_message_at)
    : formatTime(session.created_at);

  /**
   * 处理编辑
   */
  const handleEdit = async () => {
    if (!editTitle.trim()) {
      message.warning('会话标题不能为空');
      return;
    }

    setIsUpdating(true);
    try {
      const sessionId = session.id || session.session_id;
      if (!sessionId) {
        message.error('会话ID不存在');
        return;
      }
      // 使用 useSessions hook 的 updateSession 方法，会自动更新缓存
      const updatedSession = await updateSession(sessionId, {
        title: editTitle.trim(),
      });
      showSuccess('会话已改名');
      setIsEditModalOpen(false);
      onUpdate?.(updatedSession);
    } catch (error: any) {
      showError(error, '更新会话失败');
    } finally {
      setIsUpdating(false);
    }
  };

  /**
   * 打开编辑对话框
   */
  const handleOpenEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditTitle(session.title || '');
    setIsEditModalOpen(true);
  };

  /**
   * 关闭编辑对话框
   */
  const handleCloseEdit = () => {
    setIsEditModalOpen(false);
    setEditTitle(session.title || '');
  };

  return (
    <>
      <List.Item
        style={{
          padding: '12px 16px',
          cursor: 'pointer',
          backgroundColor: isActive ? 'var(--bg-secondary)' : 'transparent',
          borderLeft: isActive ? '3px solid var(--primary-color)' : '3px solid transparent',
          transition: 'background-color 0.2s ease, border-color 0.2s ease',
        }}
        onClick={onSelect}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = isActive ? 'var(--bg-secondary)' : 'transparent';
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
                onClick={handleOpenEdit}
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

      {/* 编辑对话框 */}
      <Modal
        title="编辑会话"
        open={isEditModalOpen}
        onOk={handleEdit}
        onCancel={handleCloseEdit}
        confirmLoading={isUpdating}
        okText="保存"
        cancelText="取消"
      >
        <Input
          placeholder="请输入会话标题"
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onPressEnter={handleEdit}
          maxLength={100}
          showCount
        />
      </Modal>
    </>
  );
};

