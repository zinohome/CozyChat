import React from 'react';
import { Button, Space } from 'antd';
import { HeartOutlined, UserOutlined, SettingOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useIsMobile } from '@/hooks/useMediaQuery';
import styles from './ChatToolbar.module.css';

/**
 * 聊天工具栏组件属性
 */
interface ChatToolbarProps {
  /** 是否为移动端 */
  isMobile?: boolean;
}

/**
 * 聊天工具栏组件
 * 
 * 提供健康档案、个人资料、偏好设置的快速入口
 */
export const ChatToolbar: React.FC<ChatToolbarProps> = ({ isMobile: isMobileProp }) => {
  const navigate = useNavigate();
  const isMobileHook = useIsMobile();
  const isMobile = isMobileProp ?? isMobileHook;

  const handleHealthRecord = () => {
    navigate('/health-record');
  };

  const handleProfile = () => {
    navigate('/profile');
  };

  const handleSettings = () => {
    navigate('/settings');
  };

  return (
    <div className={styles.toolbar}>
      <Space size={isMobile ? 'small' : 'middle'} className={styles.buttonGroup}>
        <Button
          type="text"
          icon={<HeartOutlined />}
          onClick={handleHealthRecord}
          className={styles.toolbarButton}
        >
          健康档案
        </Button>
        <Button
          type="text"
          icon={<UserOutlined />}
          onClick={handleProfile}
          className={styles.toolbarButton}
        >
          个人资料
        </Button>
        <Button
          type="text"
          icon={<SettingOutlined />}
          onClick={handleSettings}
          className={styles.toolbarButton}
        >
          偏好设置
        </Button>
      </Space>
    </div>
  );
};

