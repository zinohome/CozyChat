import React from 'react';
import { Card, Form, Input, Button, message } from 'antd';
import { useAuthStore } from '@/store/slices/authSlice';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from '@/services/user';
import type { UserProfile } from '@/types/user';

/**
 * 用户设置组件
 *
 * 允许用户编辑个人资料。
 */
export const UserSettings: React.FC = () => {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [form] = Form.useForm<Partial<UserProfile>>();

  // 更新用户资料Mutation
  const updateMutation = useMutation({
    mutationFn: (data: Partial<UserProfile>) =>
      userApi.updateUserProfile(user!.id, data),
    onSuccess: () => {
      message.success('更新成功');
      queryClient.invalidateQueries({ queryKey: ['user', 'profile', user?.id] });
    },
    onError: () => {
      message.error('更新失败');
    },
  });

  /**
   * 提交表单
   */
  const handleSubmit = async (values: Partial<UserProfile>) => {
    await updateMutation.mutateAsync(values);
  };

  return (
    <Card title="个人设置">
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
      >
        <Form.Item name="display_name" label="显示名称">
          <Input placeholder="请输入显示名称" />
        </Form.Item>

        <Form.Item name="bio" label="简介">
          <Input.TextArea
            rows={4}
            placeholder="请输入个人简介"
            maxLength={200}
            showCount
          />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={updateMutation.isPending}>
            保存
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

