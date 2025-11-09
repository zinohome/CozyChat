import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@/store/slices/authSlice';

/**
 * 公开路由组件
 *
 * 已登录用户访问公开路由时重定向到聊天页。
 */
interface PublicRouteProps {
  children: React.ReactNode;
}

export const PublicRoute: React.FC<PublicRouteProps> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();

  if (isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }

  return <>{children}</>;
};

