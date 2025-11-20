import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useIsMobile } from './useMediaQuery';

describe('useIsMobile', () => {
  let mockMatchMedia: any;

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock matchMedia
    mockMatchMedia = vi.fn((query: string) => ({
      matches: query === '(max-width: 767px)',
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));
    
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      configurable: true,
      value: mockMatchMedia,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('应该检测移动设备', () => {
    mockMatchMedia.mockImplementation((query: string) => ({
      matches: query === '(max-width: 767px)',
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }));

    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(true);
  });

  it('应该检测桌面设备', () => {
    mockMatchMedia.mockImplementation((query: string) => ({
      matches: false, // 桌面设备不匹配移动端查询
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }));

    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(false);
  });

  it('应该响应窗口大小变化', async () => {
    let matches = false;
    const listeners: Array<() => void> = [];
    
    // 创建一个单一的mockMediaQuery实例，确保所有调用返回同一个对象
    const mockMediaQuery = {
      get matches() {
        return matches;
      },
      media: '(max-width: 767px)',
      addEventListener: (_event: string, listener: () => void) => {
        listeners.push(listener);
      },
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    };
    
    // 确保matchMedia总是返回同一个实例
    mockMatchMedia.mockReturnValue(mockMediaQuery as any);

    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(false);

    // 触发窗口大小变化
    await act(async () => {
      matches = true;
      // 调用所有注册的listeners，它们会读取最新的matches值
      listeners.forEach(listener => listener());
    });

    // 等待状态更新
    await waitFor(() => {
    expect(result.current).toBe(true);
    });
  });
});

