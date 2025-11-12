import React, { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { UserSettings } from '../components/UserSettings';
import { ThemeSwitcher } from '../components/ThemeSwitcher';
import { LanguageSwitcher } from '../components/LanguageSwitcher';
import { Card, Space, Divider, Button, Select, Switch } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useUIStore } from '@/store/slices/uiSlice';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from '@/services/user';
import { showError, showSuccess } from '@/utils/errorHandler';
import type { ChatBackgroundStyle } from '@/store/slices/uiSlice';
import type { UserPreferences } from '@/types/user';

/**
 * 设置页面
 *
 * 用户设置和偏好配置页面。
 */
export const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const { chatBackgroundStyle, setChatBackgroundStyle } = useUIStore();
  const queryClient = useQueryClient();
  const [autoTts, setAutoTts] = useState(false);

  // 获取用户偏好
  const { data: preferences } = useQuery({
    queryKey: ['user', 'preferences'],
    queryFn: () => userApi.getCurrentUserPreferences(),
  });

  // 更新偏好Mutation
  const updateMutation = useMutation({
    mutationFn: (prefs: UserPreferences) =>
      userApi.updateCurrentUserPreferences(prefs),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'preferences'] });
      showSuccess('设置已保存');
    },
    onError: (error) => {
      showError(error, '保存设置失败');
    },
  });

  // 初始化 auto_tts 状态
  useEffect(() => {
    if (preferences) {
      // 确保正确处理 auto_tts 值（可能是 undefined、null 或 false）
      const autoTtsValue = preferences.auto_tts === true;
      setAutoTts(autoTtsValue);
      console.log('SettingsPage: 加载偏好设置, auto_tts:', autoTtsValue, 'preferences:', preferences);
    } else {
      // 如果没有偏好设置，默认为 false
      setAutoTts(false);
    }
  }, [preferences]);

  const handleClose = () => {
    navigate('/chat');
  };

  const handleChatBackgroundStyleChange = (value: ChatBackgroundStyle) => {
    setChatBackgroundStyle(value);
  };

  const handleAutoTtsChange = async (checked: boolean) => {
    setAutoTts(checked);
    console.log('SettingsPage: 更新 auto_tts 为:', checked);
    try {
      const updated = await updateMutation.mutateAsync({ auto_tts: checked });
      console.log('SettingsPage: 更新成功, 返回的偏好设置:', updated);
      // 确保状态同步
      if (updated?.auto_tts !== undefined) {
        setAutoTts(updated.auto_tts === true);
      }
    } catch (error) {
      console.error('SettingsPage: 更新失败:', error);
      // 恢复原状态
      setAutoTts(!checked);
    }
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
            <Divider />
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <span>聊天背景</span>
              <Select
                value={chatBackgroundStyle}
                onChange={handleChatBackgroundStyleChange}
                style={{ width: 120 }}
              >
                <Select.Option value="gradient">渐变色</Select.Option>
                <Select.Option value="solid">纯色</Select.Option>
              </Select>
            </Space>
            <Divider />
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <div>
                <div style={{ marginBottom: '4px' }}>自动播放语音</div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  收到助手回复时自动播放语音
                </div>
              </div>
              <Switch
                checked={autoTts}
                onChange={handleAutoTtsChange}
                loading={updateMutation.isPending}
              />
            </Space>
          </Space>
        </Card>

        <Card title="个人设置" style={{ marginTop: '24px' }}>
          <UserSettings />
        </Card>
      </div>
    </MainLayout>
  );
};

export default SettingsPage;

