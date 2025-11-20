import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { MemoryRouter } from 'react-router-dom';

/**
 * 创建测试用的QueryClient
 */
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0, // 原 cacheTime，React Query v5 已重命名
      },
      mutations: {
        retry: false,
      },
    },
  });

/**
 * 测试包装器组件
 */
interface TestWrapperProps {
  children: React.ReactNode;
  queryClient?: QueryClient;
}

const TestWrapper: React.FC<TestWrapperProps> = ({
  children,
  queryClient = createTestQueryClient(),
}) => {
  return (
    <MemoryRouter>
    <QueryClientProvider client={queryClient as any}>
      <ConfigProvider locale={zhCN}>{children}</ConfigProvider>
    </QueryClientProvider>
    </MemoryRouter>
  );
};

/**
 * 自定义render函数
 */
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  return render(ui, {
    wrapper: (props) => <TestWrapper {...props} />,
    ...options,
  });
};

export * from '@testing-library/react';
export { customRender as render, createTestQueryClient };

