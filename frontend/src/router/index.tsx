import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { ProtectedRoute } from './ProtectedRoute';
import { PublicRoute } from './PublicRoute';

// 懒加载页面组件
const LoginPage = lazy(() => import('@/features/auth/pages/LoginPage'));
const RegisterPage = lazy(() => import('@/features/auth/pages/RegisterPage'));
const ChatPage = lazy(() => import('@/features/chat/pages/ChatPage'));
const SettingsPage = lazy(() => import('@/features/user/pages/SettingsPage'));
const ProfilePage = lazy(() => import('@/features/user/pages/ProfilePage'));
const HealthRecordPage = lazy(() => import('@/pages/HealthRecord/HealthRecord'));
const HealthCirclePage = lazy(() => import('@/pages/HealthCircle/HealthCircle'));
const StressProfilePage = lazy(() => import('@/pages/StressProfile/StressProfile'));
const HealingTreeholePage = lazy(() => import('@/pages/HealingTreehole/HealingTreehole'));
const ZenPlayerPage = lazy(() => import('@/pages/ZenPlayer/ZenPlayer'));
const EnergyRhythmPage = lazy(() => import('@/pages/EnergyRhythm/EnergyRhythm'));

/**
 * 加载中组件
 */
const Loading: React.FC = () => (
  <div
    style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
    }}
  >
    <Spin size="large" />
  </div>
);

/**
 * 路由配置
 */
export const AppRouter: React.FC = () => {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Suspense fallback={<Loading />}>
        <Routes>
          {/* 公开路由 */}
          <Route
            path="/login"
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicRoute>
                <RegisterPage />
              </PublicRoute>
            }
          />

          {/* 受保护路由 */}
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/chat/:sessionId"
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/health-record"
            element={
              <ProtectedRoute>
                <HealthRecordPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/health-circle"
            element={
              <ProtectedRoute>
                <HealthCirclePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/stress-profile"
            element={
              <ProtectedRoute>
                <StressProfilePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/healing-treehole"
            element={
              <ProtectedRoute>
                <HealingTreeholePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/zen-player"
            element={
              <ProtectedRoute>
                <ZenPlayerPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/energy-rhythm"
            element={
              <ProtectedRoute>
                <EnergyRhythmPage />
              </ProtectedRoute>
            }
          />

          {/* 默认路由 */}
          <Route path="/" element={<Navigate to="/chat" replace />} />
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
};

