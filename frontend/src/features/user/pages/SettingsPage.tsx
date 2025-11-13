import React, { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
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
import { TIMEZONES, DEFAULT_TIMEZONE } from '@/utils/timezone';
import './SettingsPage.css';

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
  const [alwaysShowVoiceInput, setAlwaysShowVoiceInput] = useState(false);
  const [timezone, setTimezone] = useState(DEFAULT_TIMEZONE);

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

  // 初始化偏好状态
  useEffect(() => {
    if (preferences) {
      // 确保正确处理 auto_tts 值（可能是 undefined、null 或 false）
      const autoTtsValue = preferences.auto_tts === true;
      setAutoTts(autoTtsValue);
      
      // 初始化 always_show_voice_input
      const alwaysShowVoiceInputValue = preferences.always_show_voice_input === true;
      setAlwaysShowVoiceInput(alwaysShowVoiceInputValue);
      
      // 初始化时区
      const timezoneValue = preferences.timezone || DEFAULT_TIMEZONE;
      setTimezone(timezoneValue);
      
      console.log('SettingsPage: 加载偏好设置, auto_tts:', autoTtsValue, 'always_show_voice_input:', alwaysShowVoiceInputValue, 'timezone:', timezoneValue, 'preferences:', preferences);
    } else {
      // 如果没有偏好设置，默认为 false
      setAutoTts(false);
      setAlwaysShowVoiceInput(false);
      setTimezone(DEFAULT_TIMEZONE);
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

  const handleAlwaysShowVoiceInputChange = async (checked: boolean) => {
    setAlwaysShowVoiceInput(checked);
    console.log('SettingsPage: 更新 always_show_voice_input 为:', checked);
    try {
      const updated = await updateMutation.mutateAsync({ always_show_voice_input: checked });
      console.log('SettingsPage: 更新成功, 返回的偏好设置:', updated);
      // 确保状态同步
      if (updated?.always_show_voice_input !== undefined) {
        setAlwaysShowVoiceInput(updated.always_show_voice_input === true);
      }
    } catch (error) {
      console.error('SettingsPage: 更新失败:', error);
      // 恢复原状态
      setAlwaysShowVoiceInput(!checked);
    }
  };

  const handleTimezoneChange = async (value: string) => {
    const oldTimezone = timezone;
    setTimezone(value);
    console.log('SettingsPage: 更新 timezone 为:', value);
    try {
      const updated = await updateMutation.mutateAsync({ timezone: value });
      console.log('SettingsPage: 更新成功, 返回的偏好设置:', updated);
      // 确保状态同步
      if (updated?.timezone !== undefined) {
        setTimezone(updated.timezone);
      }
    } catch (error) {
      console.error('SettingsPage: 更新失败:', error);
      // 恢复原状态
      setTimezone(oldTimezone);
    }
  };

  return (
    <MainLayout>
      <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
        <Card 
          className="preferences-card"
          title={
            <Space>
              <ArrowLeftOutlined
                onClick={handleClose}
                className="preferences-back-button"
                style={{ cursor: 'pointer', fontSize: '16px' }}
              />
              <span>偏好设置</span>
            </Space>
          }
          styles={{
            header: {
              backgroundColor: 'var(--primary-color)',
              borderBottomColor: 'var(--primary-color)',
            },
          }}
          style={{
            borderColor: 'var(--primary-color)',
          }}
        >
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
            <Divider />
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <div>
                <div style={{ marginBottom: '4px' }}>总是显示语音输入</div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  开启后，在宽屏幕下也会显示语音输入按钮
                </div>
              </div>
              <Switch
                checked={alwaysShowVoiceInput}
                onChange={handleAlwaysShowVoiceInputChange}
                loading={updateMutation.isPending}
              />
            </Space>
            <Divider />
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <div>
                <div style={{ marginBottom: '4px' }}>时区</div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  设置时间显示时区，影响会话和消息的时间显示
                </div>
              </div>
              <Select
                value={timezone}
                onChange={handleTimezoneChange}
                style={{ width: 200 }}
                loading={updateMutation.isPending}
              >
                {TIMEZONES.map((tz) => (
                  <Select.Option key={tz.value} value={tz.value}>
                    {tz.label}
                  </Select.Option>
                ))}
              </Select>
            </Space>
          </Space>
        </Card>
      </div>
    </MainLayout>
  );
};

export default SettingsPage;

