/**
 * useTheme Hook测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTheme } from './useTheme';
import { useUIStore } from '@/store/slices/uiSlice';

// Mock useUIStore
const mockSetTheme = vi.fn();
const mockUseUIStore = vi.fn(() => ({
  theme: 'light',
  setTheme: mockSetTheme,
}));

vi.mock('@/store/slices/uiSlice', () => ({
  useUIStore: () => mockUseUIStore(),
}));

describe('useTheme', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseUIStore.mockReturnValue({
      theme: 'light',
      setTheme: mockSetTheme,
    });
    // 清除document.documentElement的data-theme属性
    document.documentElement.removeAttribute('data-theme');
  });

  it('应该应用主题到document', () => {
    renderHook(() => useTheme());
    
    // useTheme应该在document.documentElement上设置data-theme属性
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('应该支持主题切换', () => {
    mockUseUIStore.mockReturnValue({
      theme: 'dark',
      setTheme: mockSetTheme,
    });

    renderHook(() => useTheme());
    
    // 验证主题被应用到document
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });
});
