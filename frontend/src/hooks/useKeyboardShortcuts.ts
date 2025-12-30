import { useEffect, useCallback } from 'react';

/**
 * 快捷键配置
 */
export interface KeyboardShortcut {
  /** 按键组合（如 'Ctrl+K' 或 'Enter'） */
  key: string;
  /** 回调函数 */
  handler: (event: KeyboardEvent) => void;
  /** 是否阻止默认行为 */
  preventDefault?: boolean;
  /** 是否在输入框中禁用 */
  disabledInInput?: boolean;
}

/**
 * 解析按键组合
 */
const parseKey = (key: string): { key: string; ctrl?: boolean; shift?: boolean; alt?: boolean } => {
  const parts = key.toLowerCase().split('+').map((s) => s.trim());
  const result: { key: string; ctrl?: boolean; shift?: boolean; alt?: boolean } = {
    key: parts[parts.length - 1],
  };

  if (parts.includes('ctrl') || parts.includes('cmd')) {
    result.ctrl = true;
  }
  if (parts.includes('shift')) {
    result.shift = true;
  }
  if (parts.includes('alt')) {
    result.alt = true;
  }

  return result;
};

/**
 * 检查是否匹配按键
 */
const matchesKey = (event: KeyboardEvent, config: ReturnType<typeof parseKey>): boolean => {
  const eventKey = event.key.toLowerCase();
  const configKey = config.key.toLowerCase();

  // 特殊键映射
  const keyMap: Record<string, string> = {
    ' ': 'space',
    'arrowup': 'up',
    'arrowdown': 'down',
    'arrowleft': 'left',
    'arrowright': 'right',
  };

  const normalizedEventKey = keyMap[eventKey] || eventKey;
  const normalizedConfigKey = keyMap[configKey] || configKey;

  if (normalizedEventKey !== normalizedConfigKey) {
    return false;
  }

  if (config.ctrl && !(event.ctrlKey || event.metaKey)) {
    return false;
  }
  if (config.shift && !event.shiftKey) {
    return false;
  }
  if (config.alt && !event.altKey) {
    return false;
  }

  return true;
};

/**
 * 检查是否在输入框中
 */
const isInInput = (target: EventTarget | null): boolean => {
  if (!target) return false;
  const element = target as HTMLElement;
  return (
    element.tagName === 'INPUT' ||
    element.tagName === 'TEXTAREA' ||
    element.isContentEditable
  );
};

/**
 * 键盘快捷键Hook
 *
 * 提供键盘快捷键功能，支持组合键、条件禁用等。
 */
export const useKeyboardShortcuts = (shortcuts: KeyboardShortcut[]) => {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      for (const shortcut of shortcuts) {
        const config = parseKey(shortcut.key);

        // 检查是否在输入框中
        if (shortcut.disabledInInput && isInInput(event.target)) {
          continue;
        }

        // 检查是否匹配按键
        if (matchesKey(event, config)) {
          if (shortcut.preventDefault) {
            event.preventDefault();
          }
          shortcut.handler(event);
          break;
        }
      }
    },
    [shortcuts]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);
};

/**
 * 常用快捷键配置
 */
export const commonShortcuts = {
  /** 发送消息 (Enter) */
  sendMessage: (handler: () => void): KeyboardShortcut => ({
    key: 'Enter',
    handler: () => handler(),
    preventDefault: false,
    disabledInInput: false,
  }),

  /** 新建会话 (Ctrl+N / Cmd+N) */
  newSession: (handler: () => void): KeyboardShortcut => ({
    key: 'Ctrl+N',
    handler: () => handler(),
    preventDefault: true,
  }),

  /** 搜索消息 (Ctrl+K / Cmd+K) */
  searchMessages: (handler: () => void): KeyboardShortcut => ({
    key: 'Ctrl+K',
    handler: () => handler(),
    preventDefault: true,
  }),

  /** 导出消息 (Ctrl+E / Cmd+E) */
  exportMessages: (handler: () => void): KeyboardShortcut => ({
    key: 'Ctrl+E',
    handler: () => handler(),
    preventDefault: true,
  }),

  /** 清空消息 (Ctrl+L / Cmd+L) */
  clearMessages: (handler: () => void): KeyboardShortcut => ({
    key: 'Ctrl+L',
    handler: () => handler(),
    preventDefault: true,
  }),
};

