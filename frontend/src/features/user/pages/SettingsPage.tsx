import React from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { UserSettings } from '../components/UserSettings';
import { ThemeSwitcher } from '../components/ThemeSwitcher';
import { LanguageSwitcher } from '../components/LanguageSwitcher';
import { Card, Space, Divider, Button } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

/**
 * 设置页面
 *
 * 用户设置和偏好配置页面。
 */
export const SettingsPage: React.FC = () => {
  const navigate = useNavigate();

  const handleClose = () => {
    navigate('/chat');
  };

  return (
    <MainLayout>
      <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
        {/* 页面头部：标题和关闭按钮 */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '24px',
          }}
        >
          <h2 style={{ margin: 0, fontSize: '24px', fontWeight: 'bold' }}>
            设置
          </h2>
          <Button
            type="primary"
            icon={<ArrowLeftOutlined />}
            onClick={handleClose}
          >
            返回
          </Button>
        </div>

        <Card title="个人设置" style={{ marginBottom: '24px' }}>
          <UserSettings />
        </Card>

        <Card title="偏好设置">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <span>主题</span>
              <ThemeSwitcher />
            </Space>
            <Divider />
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <span>语言</span>
              <LanguageSwitcher />
            </Space>
          </Space>
        </Card>
      </div>
    </MainLayout>
  );
};

export default SettingsPage;

