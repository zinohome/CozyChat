import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useMessageSearch } from './useMessageSearch';
import type { Message } from '@/types/chat';

describe('useMessageSearch', () => {
  const mockMessages: Message[] = [
    {
      id: 'msg-1',
      role: 'user',
      content: 'Hello, world!',
      timestamp: new Date(),
    },
    {
      id: 'msg-2',
      role: 'assistant',
      content: 'Hi there!',
      timestamp: new Date(),
    },
    {
      id: 'msg-3',
      role: 'user',
      content: 'How are you?',
      timestamp: new Date(),
    },
  ];

  it('应该初始化为空搜索', () => {
    const { result } = renderHook(() => useMessageSearch(mockMessages));
    expect(result.current.keyword).toBe('');
    expect(result.current.results).toHaveLength(0);
    expect(result.current.isSearching).toBe(false);
  });

  it('应该搜索匹配的消息', () => {
    const { result } = renderHook(() => useMessageSearch(mockMessages));

    act(() => {
      result.current.setKeyword('Hello');
    });

    expect(result.current.results).toHaveLength(1);
    expect(result.current.results[0].id).toBe('msg-1');
    expect(result.current.isSearching).toBe(true);
  });

  it('应该不区分大小写搜索', () => {
    const { result } = renderHook(() => useMessageSearch(mockMessages));

    act(() => {
      result.current.setKeyword('hello');
    });

    expect(result.current.results).toHaveLength(1);
  });

  it('应该导航到下一个结果', () => {
    const { result } = renderHook(() => useMessageSearch(mockMessages));

    act(() => {
      result.current.setKeyword('o');
    });

    expect(result.current.results.length).toBeGreaterThan(0);

    act(() => {
      result.current.next();
    });

    expect(result.current.currentIndex).toBe(0);
  });

  it('应该导航到上一个结果', () => {
    const { result } = renderHook(() => useMessageSearch(mockMessages));

    act(() => {
      result.current.setKeyword('o');
    });

    expect(result.current.results.length).toBeGreaterThan(0);

    act(() => {
      result.current.next();
      result.current.previous();
    });

    // previous应该循环到最后一个
    expect(result.current.currentIndex).toBeGreaterThanOrEqual(0);
    expect(result.current.currentIndex).toBeLessThan(result.current.results.length);
  });

  it('应该清除搜索', () => {
    const { result } = renderHook(() => useMessageSearch(mockMessages));

    act(() => {
      result.current.setKeyword('Hello');
      result.current.clear();
    });

    expect(result.current.keyword).toBe('');
    expect(result.current.results).toHaveLength(0);
    expect(result.current.currentIndex).toBe(-1);
  });
});

