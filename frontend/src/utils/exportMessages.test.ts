import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  exportMessages,
  exportMessagesAsText,
  exportMessagesAsMarkdown,
  exportMessagesAsJSON,
  exportMessagesAsCSV,
} from './exportMessages';
import type { Message } from '@/types/chat';

// Mock URL.createObjectURL and URL.revokeObjectURL
global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
global.URL.revokeObjectURL = vi.fn();

// Mock document.createElement
const mockClick = vi.fn();
const mockAppendChild = vi.fn();
const mockRemoveChild = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  global.document.createElement = vi.fn(() => ({
    click: mockClick,
    href: '',
    download: '',
  })) as any;
  global.document.body.appendChild = mockAppendChild;
  global.document.body.removeChild = mockRemoveChild;
});

describe('exportMessages', () => {
  const mockMessages: Message[] = [
    {
      id: 'msg-1',
      role: 'user',
      content: 'Hello',
      timestamp: new Date('2024-01-01T10:00:00Z'),
      session_id: 'session-1',
    },
    {
      id: 'msg-2',
      role: 'assistant',
      content: 'Hi there!',
      timestamp: new Date('2024-01-01T10:01:00Z'),
      session_id: 'session-1',
    },
  ];

  it('应该导出为TXT格式', () => {
    exportMessages(mockMessages, { format: 'txt' });
    expect(global.URL.createObjectURL).toHaveBeenCalled();
    expect(mockClick).toHaveBeenCalled();
  });

  it('应该导出为Markdown格式', () => {
    exportMessages(mockMessages, { format: 'markdown' });
    expect(global.URL.createObjectURL).toHaveBeenCalled();
  });

  it('应该导出为JSON格式', () => {
    exportMessages(mockMessages, { format: 'json' });
    expect(global.URL.createObjectURL).toHaveBeenCalled();
  });

  it('应该导出为CSV格式', () => {
    exportMessages(mockMessages, { format: 'csv' });
    expect(global.URL.createObjectURL).toHaveBeenCalled();
  });
});

describe('exportMessagesAsText', () => {
  const messages: Message[] = [
    {
      id: 'msg-1',
      role: 'user',
      content: 'Hello',
      timestamp: new Date('2024-01-01T10:00:00Z'),
    },
  ];

  it('应该导出为文本格式', () => {
    const result = exportMessagesAsText(messages, {
      format: 'txt',
      includeTimestamp: true,
      includeRole: true,
    });
    expect(result).toContain('Hello');
    expect(result).toContain('user');
  });

  it('应该排除时间戳', () => {
    const result = exportMessagesAsText(messages, {
      format: 'txt',
      includeTimestamp: false,
      includeRole: true,
    });
    expect(result).not.toMatch(/\d{4}-\d{2}-\d{2}/);
  });
});

describe('exportMessagesAsMarkdown', () => {
  const messages: Message[] = [
    {
      id: 'msg-1',
      role: 'user',
      content: 'Hello',
      timestamp: new Date('2024-01-01T10:00:00Z'),
    },
  ];

  it('应该导出为Markdown格式', () => {
    const result = exportMessagesAsMarkdown(messages, {
      format: 'markdown',
    });
    expect(result).toContain('###');
    expect(result).toContain('**用户**');
    expect(result).toContain('Hello');
  });
});

describe('exportMessagesAsJSON', () => {
  const messages: Message[] = [
    {
      id: 'msg-1',
      role: 'user',
      content: 'Hello',
      timestamp: new Date('2024-01-01T10:00:00Z'),
    },
  ];

  it('应该导出为JSON格式', () => {
    const result = exportMessagesAsJSON(messages);
    const parsed = JSON.parse(result);
    expect(parsed).toHaveLength(1);
    expect(parsed[0].id).toBe('msg-1');
  });
});

describe('exportMessagesAsCSV', () => {
  const messages: Message[] = [
    {
      id: 'msg-1',
      role: 'user',
      content: 'Hello',
      timestamp: new Date('2024-01-01T10:00:00Z'),
      session_id: 'session-1',
    },
  ];

  it('应该导出为CSV格式', () => {
    const result = exportMessagesAsCSV(messages);
    expect(result).toContain('ID,角色,内容,时间戳,会话ID');
    expect(result).toContain('msg-1');
    expect(result).toContain('user');
  });
});
