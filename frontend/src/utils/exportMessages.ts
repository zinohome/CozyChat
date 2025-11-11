import type { Message } from '@/types/chat';

/**
 * 导出格式
 */
export type ExportFormat = 'txt' | 'json' | 'markdown' | 'csv';

/**
 * 导出消息选项
 */
export interface ExportOptions {
  /** 导出格式 */
  format: ExportFormat;
  /** 是否包含时间戳 */
  includeTimestamp?: boolean;
  /** 是否包含角色 */
  includeRole?: boolean;
  /** 文件名 */
  filename?: string;
}

/**
 * 导出消息为文本
 */
export const exportMessagesAsText = (
  messages: Message[],
  options: ExportOptions
): string => {
  const { includeTimestamp = true, includeRole = true } = options;

  return messages
    .map((msg) => {
      const content = typeof msg.content === 'string' ? msg.content : (msg.content as any)?.text || '';
      const timestamp = includeTimestamp
        ? new Date(msg.timestamp).toLocaleString('zh-CN')
        : '';
      const role = includeRole ? `[${msg.role}]` : '';

      return [timestamp, role, content].filter(Boolean).join(' ');
    })
    .join('\n\n');
};

/**
 * 导出消息为Markdown
 */
export const exportMessagesAsMarkdown = (
  messages: Message[],
  options: ExportOptions
): string => {
  const { includeTimestamp = true } = options;

  return messages
    .map((msg) => {
      const content = typeof msg.content === 'string' ? msg.content : (msg.content as any)?.text || '';
      const timestamp = includeTimestamp
        ? `*${new Date(msg.timestamp).toLocaleString('zh-CN')}*`
        : '';
      const role = msg.role === 'user' ? '**用户**' : '**AI**';

      return `### ${role} ${timestamp}\n\n${content}\n`;
    })
    .join('\n---\n\n');
};

/**
 * 导出消息为JSON
 */
export const exportMessagesAsJSON = (messages: Message[]): string => {
  return JSON.stringify(
    messages.map((msg) => ({
      id: msg.id,
      role: msg.role,
      content: typeof msg.content === 'string' ? msg.content : (msg.content as any)?.text || '',
      timestamp: msg.timestamp,
      session_id: msg.session_id,
    })),
    null,
    2
  );
};

/**
 * 导出消息为CSV
 */
export const exportMessagesAsCSV = (messages: Message[]): string => {
  const headers = ['ID', '角色', '内容', '时间戳', '会话ID'];
  const rows = messages.map((msg) => {
    const content = typeof msg.content === 'string' ? msg.content : (msg.content as any)?.text || '';
    return [
      msg.id,
      msg.role,
      `"${content.replace(/"/g, '""')}"`, // 转义引号
      new Date(msg.timestamp).toISOString(),
      msg.session_id || '',
    ].join(',');
  });

  return [headers.join(','), ...rows].join('\n');
};

/**
 * 导出消息
 */
export const exportMessages = (
  messages: Message[],
  options: ExportOptions
): void => {
  const { format, filename } = options;

  let content: string;
  let mimeType: string;
  let extension: string;

  switch (format) {
    case 'txt':
      content = exportMessagesAsText(messages, options);
      mimeType = 'text/plain';
      extension = 'txt';
      break;
    case 'markdown':
      content = exportMessagesAsMarkdown(messages, options);
      mimeType = 'text/markdown';
      extension = 'md';
      break;
    case 'json':
      content = exportMessagesAsJSON(messages);
      mimeType = 'application/json';
      extension = 'json';
      break;
    case 'csv':
      content = exportMessagesAsCSV(messages);
      mimeType = 'text/csv';
      extension = 'csv';
      break;
    default:
      throw new Error(`不支持的导出格式: ${format}`);
  }

  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename || `messages.${extension}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

