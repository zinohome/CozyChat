import React from 'react';
import { Drawer, Form, Switch, Select, Space, Button } from 'antd';
import { SettingOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/store/slices/authSlice';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from '@/services/user';
import { useUIStore } from '@/store/slices/uiSlice';
import type { UserPreferences } from '@/types/user';

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
  const { theme, setTheme, language, setLanguage } = useUIStore();
  const queryClient = useQueryClient();
  const [form] = Form.useForm<UserPreferences>();

  // 获取用户偏好
  const { data: preferences, isLoading } = useQuery({
    queryKey: ['user', 'preferences', user?.id],
    queryFn: () => userApi.getUserPreferences(user!.id),
    enabled: !!user?.id,
  });

  // 更新偏好Mutation
  const updateMutation = useMutation({
    mutationFn: (prefs: UserPreferences) =>
      userApi.updateUserPreferences(user!.id, prefs),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'preferences', user?.id] });
    },
  });

  // 初始化表单
  React.useEffect(() => {
    if (preferences) {
      form.setFieldsValue(preferences);
    }
  }, [preferences, form]);

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
      onClose();
    } catch (error) {
      console.error('Failed to update preferences:', error);
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
          <Select>
            <Select.Option value="light">亮色</Select.Option>
            <Select.Option value="dark">暗色</Select.Option>
            <Select.Option value="auto">跟随系统</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item name="language" label="语言">
          <Select>
            <Select.Option value="zh-CN">中文</Select.Option>
            <Select.Option value="en-US">English</Select.Option>
          </Select>
        </Form.Item>

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

        <Form.Item>
          <Button type="primary" htmlType="submit" block loading={updateMutation.isPending}>
            保存
          </Button>
        </Form.Item>
      </Form>
    </Drawer>
  );
};

