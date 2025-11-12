import React from 'react';
import { Form, Input, Button } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '../hooks/useAuth';
import { showError, showSuccess } from '@/utils/errorHandler';
import type { LoginRequest } from '@/types/user';

/**
 * 登录表单组件
 */
export const LoginForm: React.FC = () => {
  const { login, isLoggingIn } = useAuth();
  const [form] = Form.useForm<LoginRequest>();

  const onSubmit = async (values: LoginRequest) => {
    try {
      await login(values);
      showSuccess('登录成功');
    } catch (error: any) {
      showError(error, '登录失败');
    }
  };

  return (
    <Form
      form={form}
      onFinish={onSubmit}
      layout="vertical"
      requiredMark={false}
    >
      <Form.Item
        name="username"
        label="用户名或邮箱"
        rules={[
          { required: true, message: '请输入用户名或邮箱' },
          { min: 1, message: '用户名或邮箱不能为空' },
        ]}
      >
        <Input
          prefix={<UserOutlined />}
          placeholder="请输入用户名或邮箱"
        />
      </Form.Item>

      <Form.Item
        name="password"
        label="密码"
        rules={[
          { required: true, message: '请输入密码' },
          { min: 6, message: '密码至少6位' },
        ]}
      >
        <Input.Password
          prefix={<LockOutlined />}
          placeholder="请输入密码"
        />
      </Form.Item>

      <Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          block
          loading={isLoggingIn}
        >
          登录
        </Button>
      </Form.Item>
    </Form>
  );
};

