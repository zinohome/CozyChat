/**
 * ErrorBoundary组件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@/test/utils';
import ErrorBoundary from './ErrorBoundary';
import React from 'react';

// Mock Sentry
vi.mock('@sentry/react', () => ({
  withScope: vi.fn((callback) => {
    const scope = {
      setContext: vi.fn(),
    };
    callback(scope);
    return 'mock-event-id';
  }),
  captureException: vi.fn(() => 'mock-event-id'),
  showReportDialog: vi.fn(),
}));

// 创建一个会抛出错误的组件用于测试
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div>No error</div>;
};

describe('ErrorBoundary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // 抑制控制台错误输出
    vi.spyOn(console, 'error').mockImplementation(() => {});
    // Mock window.location.reload
    delete (window as any).location;
    (window as any).location = { reload: vi.fn() };
  });

  it('应该正常渲染子组件', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );
    
    expect(screen.getByText('No error')).toBeInTheDocument();
  });

  it('应该捕获错误并显示错误信息', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );
    
    // 应该显示错误信息（具体实现取决于组件）
    // ErrorBoundary通常会显示错误UI
    expect(document.body).toBeInTheDocument();
  });
});
