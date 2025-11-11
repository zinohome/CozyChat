import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useKeyboardShortcuts, commonShortcuts } from './useKeyboardShortcuts';

describe('useKeyboardShortcuts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该注册快捷键', () => {
    const handler = vi.fn();
    const shortcuts = [
      {
        key: 'Enter',
        handler,
        preventDefault: false,
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', { key: 'Enter' });
    window.dispatchEvent(event);

    expect(handler).toHaveBeenCalled();
  });

  it('应该阻止默认行为', () => {
    const handler = vi.fn();
    const shortcuts = [
      {
        key: 'Ctrl+S',
        handler,
        preventDefault: true,
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: 's',
      ctrlKey: true,
    });
    const preventDefaultSpy = vi.spyOn(event, 'preventDefault');
    window.dispatchEvent(event);

    expect(preventDefaultSpy).toHaveBeenCalled();
  });

  it('应该在输入框中禁用快捷键', () => {
    const handler = vi.fn();
    const shortcuts = [
      {
        key: 'Enter',
        handler,
        disabledInInput: true,
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    // 创建输入框并聚焦
    const input = document.createElement('input');
    document.body.appendChild(input);
    input.focus();

    const event = new KeyboardEvent('keydown', { 
      key: 'Enter',
      bubbles: true,
    });
    Object.defineProperty(event, 'target', {
      value: input,
      writable: false,
    });
    window.dispatchEvent(event);

    expect(handler).not.toHaveBeenCalled();

    document.body.removeChild(input);
  });

  it('应该支持组合键', () => {
    const handler = vi.fn();
    const shortcuts = [
      {
        key: 'Ctrl+K',
        handler,
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: 'k',
      ctrlKey: true,
    });
    window.dispatchEvent(event);

    expect(handler).toHaveBeenCalled();
  });
});

describe('commonShortcuts', () => {
  it('应该创建发送消息快捷键', () => {
    const handler = vi.fn();
    const shortcut = commonShortcuts.sendMessage(handler);
    expect(shortcut.key).toBe('Enter');
    expect(shortcut.handler).toBe(handler);
  });

  it('应该创建新建会话快捷键', () => {
    const handler = vi.fn();
    const shortcut = commonShortcuts.newSession(handler);
    expect(shortcut.key).toBe('Ctrl+N');
    expect(shortcut.preventDefault).toBe(true);
  });

  it('应该创建搜索消息快捷键', () => {
    const handler = vi.fn();
    const shortcut = commonShortcuts.searchMessages(handler);
    expect(shortcut.key).toBe('Ctrl+K');
    expect(shortcut.preventDefault).toBe(true);
  });
});

