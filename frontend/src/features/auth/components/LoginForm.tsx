import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  const navigate = useNavigate();
  const [form] = Form.useForm<LoginRequest>();

  // Demo模式：自动填入用户名和密码
  useEffect(() => {
    const demoMode = import.meta.env.VITE_DEMO_MODE === 'true';
    if (demoMode) {
      const demoUsername = import.meta.env.VITE_DEMO_USERNAME || 'demo';
      const demoPassword = import.meta.env.VITE_DEMO_PASSWORD || 'demo123';
      form.setFieldsValue({
        username: demoUsername,
        password: demoPassword,
      });
    }
  }, [form]);

  const onSubmit = async (values: LoginRequest) => {
    try {
      const response = await login(values);
      
      // 验证登录是否真正成功（必须有user和access_token）
      if (!response || !response.user || !response.access_token) {
        throw new Error('登录失败：响应数据无效');
      }
      
      // 登录成功，显示提示并跳转
      showSuccess('登录成功');
      
      // 延迟跳转，确保状态已更新
      setTimeout(() => {
        navigate('/chat', { replace: true });
      }, 100);
    } catch (error: any) {
      // 登录失败，显示错误信息
      const errorMessage = error?.message || error?.response?.data?.detail || '登录失败，请检查用户名和密码';
      showError(errorMessage, '登录失败');
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

