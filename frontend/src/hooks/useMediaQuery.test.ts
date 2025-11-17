import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
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

  it('应该响应窗口大小变化', () => {
    let matches = false;
    const listeners: Array<() => void> = [];
    
    const mockMediaQuery = {
      get matches() {
        return matches;
      },
      media: '(max-width: 767px)',
      addEventListener: (_event: string, listener: () => void) => {
        listeners.push(listener);
      },
      removeEventListener: vi.fn(),
    };
    
    mockMatchMedia.mockImplementation((query: string) => ({
      ...mockMediaQuery,
      media: query,
    }));

    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(false);

    act(() => {
      matches = true;
      listeners.forEach(listener => listener());
    });

    // 等待状态更新
    expect(result.current).toBe(true);
  });
});

