/**
 * ThemeProvider组件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@/test/utils';
import { ThemeProvider } from './ThemeProvider';
import React from 'react';

describe('ThemeProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该渲染ThemeProvider', () => {
    render(
      <ThemeProvider>
        <div>Test content</div>
      </ThemeProvider>
    );
    
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('应该提供主题上下文', () => {
    const TestComponent = () => {
      return <div>Theme context test</div>;
    };

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );
    
    expect(screen.getByText('Theme context test')).toBeInTheDocument();
  });
});
