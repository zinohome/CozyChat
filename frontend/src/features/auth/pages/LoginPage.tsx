import React from 'react';
import { Card } from 'antd';
import { LoginForm } from '../components/LoginForm';

/**
 * 登录页面
 */
export const LoginPage: React.FC = () => {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card
        title="登录 CozyChat"
        style={{ width: 400 }}
        headStyle={{ textAlign: 'center', fontSize: '24px' }}
      >
        <LoginForm />
      </Card>
    </div>
  );
};

