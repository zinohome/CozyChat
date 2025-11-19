import React, { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { ThemeSwitcher } from '../components/ThemeSwitcher';
import { LanguageSwitcher } from '../components/LanguageSwitcher';
import { Card, Space, Divider, Select, Switch, Tabs } from 'antd';
import { ArrowLeftOutlined, MessageOutlined, FileTextOutlined, MedicineBoxOutlined } from '@ant-design/icons';
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
  
  // 对话风格相关状态
  const [responseStyle, setResponseStyle] = useState<'brief' | 'chatgpt_like' | 'detailed'>('chatgpt_like');
  const [stylePreset, setStylePreset] = useState<'chatgpt_like' | 'elder_friendly' | 'medical_detail'>('chatgpt_like');
  const [outputFormat, setOutputFormat] = useState<'structured' | 'list' | 'paragraph'>('structured');
  const [preferList, setPreferList] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);

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
      
      // 初始化对话风格相关设置
      setResponseStyle(preferences.response_style || 'chatgpt_like');
      setStylePreset(preferences.style_preset || 'chatgpt_like');
      setOutputFormat(preferences.output_format || 'structured');
      setPreferList(preferences.prefer_list === true);
      setShowReasoning(preferences.show_reasoning === true);
      
      console.log('SettingsPage: 加载偏好设置, auto_tts:', autoTtsValue, 'always_show_voice_input:', alwaysShowVoiceInputValue, 'timezone:', timezoneValue, 'preferences:', preferences);
    } else {
      // 如果没有偏好设置，默认为 false
      setAutoTts(false);
      setAlwaysShowVoiceInput(false);
      setTimezone(DEFAULT_TIMEZONE);
      setResponseStyle('chatgpt_like');
      setStylePreset('chatgpt_like');
      setOutputFormat('structured');
      setPreferList(false);
      setShowReasoning(false);
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

  const handleShowReasoningChange = async (checked: boolean) => {
    setShowReasoning(checked);
    try {
      await updateMutation.mutateAsync({ show_reasoning: checked });
    } catch (error) {
      console.error('SettingsPage: 更新推理展示失败:', error);
      setShowReasoning(!checked);
    }
  };

  // Tab 内容组件
  const chatSettingsTab = (
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
  );

  // 预设模板配置
  const stylePresets = [
    {
      value: 'simple',
      label: '简洁模式',
      icon: MessageOutlined,
      description: '120字内简短回答，通俗易懂，快速获取关键信息',
      config: {
        response_style: 'brief',
        style_preset: 'elder_friendly',
        output_format: 'paragraph',
        prefer_list: false,
      }
    },
    {
      value: 'balanced',
      label: '标准模式（推荐）',
      icon: FileTextOutlined,
      description: 'ChatGPT风格，结构化呈现，分点说明，清晰易读',
      config: {
        response_style: 'chatgpt_like',
        style_preset: 'chatgpt_like',
        output_format: 'structured',
        prefer_list: true,
      }
    },
    {
      value: 'professional',
      label: '专业模式',
      icon: MedicineBoxOutlined,
      description: '详细解释背景机理，提供权威医学建议，内容全面深入',
      config: {
        response_style: 'detailed',
        style_preset: 'medical_detail',
        output_format: 'structured',
        prefer_list: true,
      }
    },
  ];

  // 获取当前选中的预设
  const getCurrentPreset = () => {
    for (const preset of stylePresets) {
      const { config } = preset;
      if (
        responseStyle === config.response_style &&
        stylePreset === config.style_preset &&
        outputFormat === config.output_format &&
        preferList === config.prefer_list
      ) {
        return preset.value;
      }
    }
    return 'balanced'; // 默认
  };

  // 应用预设
  const handlePresetChange = async (presetValue: string) => {
    const preset = stylePresets.find(p => p.value === presetValue);
    if (!preset) return;

    const { config } = preset;
    try {
      await updateMutation.mutateAsync({
        response_style: config.response_style as 'brief' | 'chatgpt_like' | 'detailed',
        style_preset: config.style_preset as 'chatgpt_like' | 'elder_friendly' | 'medical_detail',
        output_format: config.output_format as 'structured' | 'list' | 'paragraph',
        prefer_list: config.prefer_list,
      });
      
      // 更新本地状态
      setResponseStyle(config.response_style as 'brief' | 'chatgpt_like' | 'detailed');
      setStylePreset(config.style_preset as 'chatgpt_like' | 'elder_friendly' | 'medical_detail');
      setOutputFormat(config.output_format as 'structured' | 'list' | 'paragraph');
      setPreferList(config.prefer_list);
    } catch (error) {
      console.error('SettingsPage: 更新预设失败:', error);
    }
  };

  const [hoveredPreset, setHoveredPreset] = useState<string | null>(null);

  const conversationStyleTab = (
    <Space direction="vertical" style={{ width: '100%', gap: '20px' }}>
      <div>
        <div style={{ marginBottom: '16px', fontSize: '14px', fontWeight: 500 }}>
          选择回答风格
        </div>
        <Space direction="vertical" style={{ width: '100%', gap: '10px' }}>
          {stylePresets.map((preset) => {
            const IconComponent = preset.icon;
            const isSelected = getCurrentPreset() === preset.value;
            const isHovered = hoveredPreset === preset.value;
            
            return (
              <div
                key={preset.value}
                onClick={() => handlePresetChange(preset.value)}
                onMouseEnter={() => setHoveredPreset(preset.value)}
                onMouseLeave={() => setHoveredPreset(null)}
                style={{
                  padding: '14px',
                  border: `2px solid ${isSelected ? 'var(--primary-color)' : isHovered ? 'var(--primary-color)' : '#e8e8e8'}`,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  backgroundColor: isSelected ? 'var(--primary-color-light, #f0f7ff)' : isHovered ? '#fafafa' : '#fff',
                  transition: 'all 0.3s',
                }}
              >
                <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                  <Space>
                    <IconComponent style={{ fontSize: '20px', color: isSelected ? 'var(--primary-color)' : '#666' }} />
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: 500, marginBottom: '2px' }}>
                        {preset.label}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {preset.description}
                      </div>
                    </div>
                  </Space>
                  {isSelected && (
                    <span style={{ color: 'var(--primary-color)', fontSize: '18px' }}>✓</span>
                  )}
                </Space>
              </div>
            );
          })}
        </Space>
      </div>
      
      <Divider />
      
      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
        <div>
          <div style={{ marginBottom: '4px', fontSize: '14px' }}>显示判断依据</div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            在回答末尾说明AI的判断理由
          </div>
        </div>
        <Switch
          checked={showReasoning}
          onChange={handleShowReasoningChange}
          loading={updateMutation.isPending}
        />
      </Space>
    </Space>
  );

  const tabItems = [
    {
      key: 'chat',
      label: '聊天设置',
      children: chatSettingsTab,
    },
    {
      key: 'style',
      label: '对话风格',
      children: conversationStyleTab,
    },
  ];

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
          <Tabs defaultActiveKey="chat" items={tabItems} />
        </Card>
      </div>
    </MainLayout>
  );
};

export default SettingsPage;

