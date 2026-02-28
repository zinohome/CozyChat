import React from 'react';
import { Button, Space } from 'antd';
import { HeartOutlined, UserOutlined, SettingOutlined, TeamOutlined, ThunderboltOutlined } from '@ant-design/icons';
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
 * 提供状态档案、个人资料、偏好设置的快速入口
 */
export const ChatToolbar: React.FC<ChatToolbarProps> = ({ isMobile: isMobileProp }) => {
  const navigate = useNavigate();
  const isMobileHook = useIsMobile();
  const isMobile = isMobileProp ?? isMobileHook;

  const handleStressProfile = () => {
    navigate('/stress-profile');
  };

  const handleHealthRecord = () => {
    navigate('/health-record');
  };

  const handleEnergyRhythm = () => {
    navigate('/energy-rhythm');
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
          onClick={handleStressProfile}
          className={styles.toolbarButton}
        >
          情绪节律
        </Button>
        <Button
          type="text"
          icon={<TeamOutlined />}
          onClick={handleHealthRecord}
          className={styles.toolbarButton}
        >
          身体节律
        </Button>
        <Button
          type="text"
          icon={<ThunderboltOutlined />}
          onClick={handleEnergyRhythm}
          className={styles.toolbarButton}
        >
          能量节律
        </Button>
      </Space>
    </div>
  );
};

