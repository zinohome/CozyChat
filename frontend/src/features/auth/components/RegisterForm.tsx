import React from 'react';
import { Form, Input, Button } from 'antd';
import { UserOutlined, MailOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '../hooks/useAuth';
import { showError, showSuccess } from '@/utils/errorHandler';
import type { RegisterRequest } from '@/types/user';

/**
 * 注册表单组件
 */
export const RegisterForm: React.FC = () => {
  const { register: registerUser, isRegistering } = useAuth();
  const [form] = Form.useForm<RegisterRequest & { confirmPassword: string }>();

  const onSubmit = async (values: RegisterRequest & { confirmPassword: string }) => {
    try {
      const { confirmPassword, ...registerData } = values;
      await registerUser(registerData);
      showSuccess('注册成功');
    } catch (error: any) {
      showError(error, '注册失败');
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
        label="用户名"
        rules={[
          { required: true, message: '请输入用户名' },
          { min: 3, message: '用户名至少3位' },
          { max: 20, message: '用户名最多20位' },
        ]}
      >
        <Input
          prefix={<UserOutlined />}
          placeholder="请输入用户名"
        />
      </Form.Item>

      <Form.Item
        name="email"
        label="邮箱"
        rules={[
          { required: true, message: '请输入邮箱' },
          { type: 'email', message: '请输入有效的邮箱地址' },
        ]}
      >
        <Input
          prefix={<MailOutlined />}
          placeholder="请输入邮箱"
          type="email"
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

      <Form.Item
        name="confirmPassword"
        label="确认密码"
        dependencies={['password']}
        rules={[
          { required: true, message: '请再次输入密码' },
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (!value || getFieldValue('password') === value) {
                return Promise.resolve();
              }
              return Promise.reject(new Error('两次输入的密码不一致'));
            },
          }),
        ]}
      >
        <Input.Password
          prefix={<LockOutlined />}
          placeholder="请再次输入密码"
        />
      </Form.Item>

      <Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          block
          loading={isRegistering}
        >
          注册
        </Button>
      </Form.Item>
    </Form>
  );
};

