import React from 'react';
import { Drawer, Form, Switch, Select, Space, Button, Divider } from 'antd';
import { SettingOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/store/slices/authSlice';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from '@/services/user';
import { useUIStore } from '@/store/slices/uiSlice';
import { showError, showSuccess } from '@/utils/errorHandler';
import { ThemeSwitcher } from './ThemeSwitcher';
import type { UserPreferences } from '@/types/user';
import type { ChatBackgroundStyle } from '@/store/slices/uiSlice';

/**
 * 偏好设置抽屉组件属性
 */
interface PreferenceDrawerProps {
  /** 是否可见 */
  open: boolean;
  /** 关闭回调 */
  onClose: () => void;
}

/**
 * 偏好设置抽屉组件
 *
 * 使用Ant Design的Drawer组件实现偏好设置侧边栏。
 */
export const PreferenceDrawer: React.FC<PreferenceDrawerProps> = ({
  open,
  onClose,
}) => {
  const { user } = useAuthStore();
  const { theme, setTheme, language, setLanguage, chatBackgroundStyle, setChatBackgroundStyle } = useUIStore();
  const queryClient = useQueryClient();
  const [form] = Form.useForm<UserPreferences>();

  // 获取用户偏好
  const { data: preferences, isLoading } = useQuery({
    queryKey: ['user', 'preferences'],
    queryFn: () => userApi.getCurrentUserPreferences(),
    enabled: !!user?.id,
  });

  // 更新偏好Mutation
  const updateMutation = useMutation({
    mutationFn: (prefs: UserPreferences) =>
      userApi.updateCurrentUserPreferences(prefs),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'preferences'] });
    },
  });

  // 初始化表单
  React.useEffect(() => {
    if (preferences) {
      form.setFieldsValue({
        ...preferences,
        chatBackgroundStyle: preferences.chatBackgroundStyle || chatBackgroundStyle,
        auto_tts: preferences.auto_tts || false,
      });
    } else {
      // 如果没有偏好设置，使用当前UI状态
      form.setFieldsValue({
        chatBackgroundStyle,
        auto_tts: false,
      });
    }
  }, [preferences, form, chatBackgroundStyle]);

  /**
   * 提交表单
   */
  const handleSubmit = async (values: UserPreferences) => {
    try {
      await updateMutation.mutateAsync(values);
      // 更新UI状态
      if (values.theme) {
        setTheme(values.theme);
      }
      if (values.language) {
        setLanguage(values.language);
      }
      if (values.chatBackgroundStyle) {
        setChatBackgroundStyle(values.chatBackgroundStyle);
      }
      showSuccess('偏好设置已保存');
      onClose();
    } catch (error) {
      showError(error, '保存偏好设置失败');
    }
  };

  return (
    <Drawer
      title={
        <Space>
          <SettingOutlined />
          偏好设置
        </Space>
      }
      placement="right"
      width={500}
      open={open}
      onClose={onClose}
      maskClosable={false}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={preferences}
        loading={isLoading}
      >
        <Form.Item name="theme" label="主题">
          <ThemeSwitcher />
        </Form.Item>

        <Form.Item name="language" label="语言">
          <Select>
            <Select.Option value="zh-CN">中文</Select.Option>
            <Select.Option value="en-US">English</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item name="chatBackgroundStyle" label="聊天背景">
          <Select value={chatBackgroundStyle} onChange={(value: ChatBackgroundStyle) => setChatBackgroundStyle(value)}>
            <Select.Option value="gradient">渐变色</Select.Option>
            <Select.Option value="solid">纯色</Select.Option>
          </Select>
        </Form.Item>

        <Divider orientation="left">对话风格</Divider>

        <Form.Item
          name="response_style"
          label="回答风格"
          tooltip="控制整体回答长度和结构偏好"
        >
          <Select placeholder="选择回答风格">
            <Select.Option value="brief">简洁模式（100字以内）</Select.Option>
            <Select.Option value="chatgpt_like">ChatGPT 风格（结构化）</Select.Option>
            <Select.Option value="detailed">详细模式（背景/原因/建议）</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="style_preset"
          label="风格预设"
          tooltip="根据受众调整语气，例如老年人更口语、医疗模式更专业"
        >
          <Select placeholder="选择风格预设">
            <Select.Option value="chatgpt_like">标准专业</Select.Option>
            <Select.Option value="elder_friendly">老年友好</Select.Option>
            <Select.Option value="medical_detail">医疗细节模式</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="output_format"
          label="输出格式"
          tooltip="控制默认的内容排版方式"
        >
          <Select placeholder="选择输出格式">
            <Select.Option value="structured">结构化段落</Select.Option>
            <Select.Option value="list">列表形式</Select.Option>
            <Select.Option value="paragraph">纯段落</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="prefer_list"
          label="偏好列表呈现"
          valuePropName="checked"
          tooltip="勾选后，系统会尽量用列表列出步骤/建议"
        >
          <Switch />
        </Form.Item>

        <Form.Item
          name="show_reasoning"
          label="展示判断依据"
          valuePropName="checked"
          tooltip="开启后，回答结尾会用2-3句话解释推理过程"
        >
          <Switch />
        </Form.Item>

        <Divider orientation="left">通知与语音</Divider>

        <Form.Item
          name={['notifications', 'email']}
          label="邮件通知"
          valuePropName="checked"
        >
          <Switch />
        </Form.Item>

        <Form.Item
          name={['notifications', 'push']}
          label="推送通知"
          valuePropName="checked"
        >
          <Switch />
        </Form.Item>

        <Form.Item
          name={['notifications', 'sound']}
          label="声音提示"
          valuePropName="checked"
        >
          <Switch />
        </Form.Item>

        <Form.Item
          name="auto_tts"
          label="自动播放语音"
          valuePropName="checked"
          tooltip="开启后，收到助手回复时自动播放语音"
        >
          <Switch />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" block loading={updateMutation.isPending}>
            保存
          </Button>
        </Form.Item>
      </Form>
    </Drawer>
  );
};

