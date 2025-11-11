import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTypewriter } from './useTypewriter';

describe('useTypewriter', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('应该初始化为空状态', () => {
    const { result } = renderHook(() => useTypewriter());
    expect(result.current.text).toBe('');
    expect(result.current.isTyping).toBe(false);
    expect(result.current.isComplete).toBe(false);
  });

  it('应该开始打字', () => {
    const { result } = renderHook(() => useTypewriter());

    act(() => {
      result.current.start('Hello', { speed: 10 });
    });

    expect(result.current.isTyping).toBe(true);
    expect(result.current.text).toBe('|');
  });

  it('应该逐字符显示文本', () => {
    const { result } = renderHook(() => useTypewriter());

    act(() => {
      result.current.start('Hi', { speed: 10 });
    });

    expect(result.current.text).toBe('|');

    act(() => {
      vi.advanceTimersByTime(10);
    });

    expect(result.current.text).toBe('H|');

    act(() => {
      vi.advanceTimersByTime(10);
    });

    expect(result.current.isComplete).toBe(true);
  });

  it('应该支持暂停', () => {
    const { result } = renderHook(() => useTypewriter());

    act(() => {
      result.current.start('Hello', { speed: 10 });
      result.current.pause();
    });

    expect(result.current.isTyping).toBe(false);
  });

  it('应该支持恢复', () => {
    const { result } = renderHook(() => useTypewriter());

    act(() => {
      result.current.start('Hello', { speed: 10 });
      result.current.pause();
      result.current.resume();
    });

    expect(result.current.isTyping).toBe(true);
  });

  it('应该支持停止', () => {
    const { result } = renderHook(() => useTypewriter());

    act(() => {
      result.current.start('Hello', { speed: 10 });
      result.current.stop();
    });

    expect(result.current.text).toBe('');
    expect(result.current.isTyping).toBe(false);
    expect(result.current.isComplete).toBe(false);
  });

  it('应该支持立即完成', () => {
    const { result } = renderHook(() => useTypewriter());

    act(() => {
      result.current.start('Hello', { speed: 10 });
      result.current.complete();
    });

    expect(result.current.text).toBe('Hello|');
    expect(result.current.isTyping).toBe(false);
    expect(result.current.isComplete).toBe(true);
  });

  it('应该调用完成回调', () => {
    const onComplete = vi.fn();
    const { result } = renderHook(() => useTypewriter());

    act(() => {
      result.current.start('Hi', { speed: 10, onComplete });
    });

    act(() => {
      vi.advanceTimersByTime(30);
    });

    expect(onComplete).toHaveBeenCalled();
  });
});

