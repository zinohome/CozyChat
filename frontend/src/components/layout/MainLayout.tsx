import React, { useEffect } from 'react';
import { Layout } from 'antd';
import { useUIStore } from '@/store/slices/uiSlice';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { MobileNav } from './MobileNav';

const { Content } = Layout;

/**
 * 主布局组件属性
 */
interface MainLayoutProps {
  /** 子组件 */
  children: React.ReactNode;
}

/**
 * 主布局组件
 *
 * 提供应用的基础布局结构，支持响应式设计。
 */
export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { sidebarOpen, setSidebarOpen } = useUIStore();
  const isMobile = useIsMobile();

  // 响应式处理：移动端自动关闭侧边栏
  useEffect(() => {
    if (isMobile && sidebarOpen) {
      setSidebarOpen(false);
    }
  }, [isMobile, sidebarOpen, setSidebarOpen]);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header />
      <Layout style={{ position: 'relative' }}>
        {/* 桌面端侧边栏 */}
        {!isMobile && <Sidebar />}
        
        {/* 移动端侧边栏（抽屉式） */}
        {isMobile && sidebarOpen && (
          <div
            style={{
              position: 'fixed',
              top: 64,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: 1000,
              backgroundColor: 'rgba(0,0,0,0.5)',
            }}
            onClick={() => setSidebarOpen(false)}
          >
            <div
              style={{
                position: 'absolute',
                left: 0,
                top: 0,
                bottom: 0,
                width: '280px',
                backgroundColor: 'var(--bg-primary)',
                boxShadow: '2px 0 8px rgba(0,0,0,0.15)',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <Sidebar />
            </div>
          </div>
        )}

        <Content
          style={{
            padding: isMobile ? '12px' : '24px',
            background: 'var(--bg-primary)',
            minHeight: 'calc(100vh - 64px)',
            color: 'var(--text-primary)',
            transition: 'background-color 0.3s ease, color 0.3s ease',
            position: 'relative', // 允许子元素使用 absolute 定位
          }}
        >
          {children}
        </Content>
      </Layout>
      {/* 移动端底部导航 */}
      {isMobile && <MobileNav />}
    </Layout>
  );
};

