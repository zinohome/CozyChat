import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MessageBubble } from './MessageBubble';
import { render as customRender } from '@/test/utils';

// Mock useMediaQuery
vi.mock('@/hooks/useMediaQuery', () => ({
  useIsMobile: () => false,
}));

describe('MessageBubble', () => {
  const defaultProps = {
    id: 'msg-1',
    role: 'user' as const,
    content: 'Hello, world!',
    timestamp: new Date('2024-01-01T10:00:00Z'),
  };

  it('应该渲染消息内容', () => {
    customRender(<MessageBubble {...defaultProps} />);
    expect(screen.getByText('Hello, world!')).toBeInTheDocument();
  });

  it('应该显示时间戳', () => {
    customRender(<MessageBubble {...defaultProps} />);
    // 时间格式可能因locale而异，这里只检查是否有时间显示
    const timeElement = screen.getByText(/\d{2}:\d{2}/);
    expect(timeElement).toBeInTheDocument();
  });

  it('应该显示复制按钮', () => {
    customRender(<MessageBubble {...defaultProps} showActions />);
    const copyButton = screen.getByRole('button', { name: 'copy' });
    expect(copyButton).toBeInTheDocument();
  });

  it('应该调用onDelete回调', async () => {
    const onDelete = vi.fn();
    const user = userEvent.setup();

    customRender(<MessageBubble {...defaultProps} onDelete={onDelete} />);
    const deleteButton = screen.getByRole('button', { name: 'delete' });
    await user.click(deleteButton);

    expect(onDelete).toHaveBeenCalledWith('msg-1');
  });

  it('应该支持编辑功能', async () => {
    const onEdit = vi.fn();
    const user = userEvent.setup();

    customRender(<MessageBubble {...defaultProps} onEdit={onEdit} />);
    const editButton = screen.getByRole('button', { name: 'edit' });
    await user.click(editButton);

    // 应该显示编辑输入框
    const textarea = screen.getByRole('textbox');
    expect(textarea).toBeInTheDocument();
  });

  it('应该只在用户消息显示编辑按钮', () => {
    const { rerender } = customRender(
      <MessageBubble {...defaultProps} role="user" onEdit={vi.fn()} />
    );
    expect(screen.queryByRole('button', { name: 'edit' })).toBeInTheDocument();

    rerender(
      <MessageBubble {...defaultProps} role="assistant" onEdit={vi.fn()} />
    );
    expect(screen.queryByRole('button', { name: 'edit' })).not.toBeInTheDocument();
  });
});

