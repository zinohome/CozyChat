import React from 'react';
import { Card } from 'antd';
import { RegisterForm } from '../components/RegisterForm';

/**
 * 注册页面
 */
export const RegisterPage: React.FC = () => {
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
        title="注册 CozyChat"
        style={{ width: 400 }}
        headStyle={{ textAlign: 'center', fontSize: '24px' }}
      >
        <RegisterForm />
      </Card>
    </div>
  );
};

