import React from 'react';
import { Layout } from 'antd';
import { useUIStore } from '@/store/slices/uiSlice';
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
 * 提供应用的基础布局结构。
 */
export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { sidebarOpen } = useUIStore();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header />
      <Layout>
        <Sidebar />
        <Content style={{ padding: '24px', background: '#fff' }}>
          {children}
        </Content>
      </Layout>
      <MobileNav />
    </Layout>
  );
};

