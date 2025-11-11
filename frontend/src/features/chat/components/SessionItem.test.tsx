import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SessionItem } from './SessionItem';
import { render as customRender } from '@/test/utils';

// Mock sessionApi
vi.mock('@/services/session', () => ({
  sessionApi: {
    updateSession: vi.fn(),
  },
}));

describe('SessionItem', () => {
  const mockSession = {
    id: 'session-1',
    title: '测试会话',
    created_at: new Date('2024-01-01T10:00:00Z'),
    last_message_at: new Date('2024-01-02T10:00:00Z'),
  };

  const mockOnSelect = vi.fn();
  const mockOnDelete = vi.fn();
  const mockOnUpdate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该渲染会话信息', () => {
    customRender(
      <SessionItem
        session={mockSession}
        onSelect={mockOnSelect}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText('测试会话')).toBeInTheDocument();
  });

  it('应该显示未命名会话', () => {
    const sessionWithoutTitle = {
      ...mockSession,
      title: undefined,
    };

    customRender(<SessionItem session={sessionWithoutTitle} />);
    expect(screen.getByText('未命名会话')).toBeInTheDocument();
  });

  it('应该调用选择回调', async () => {
    const user = userEvent.setup();
    customRender(
      <SessionItem session={mockSession} onSelect={mockOnSelect} />
    );

    // 查找可点击的会话项容器
    const sessionItem = screen.getByText('测试会话').closest('[style*="cursor: pointer"]') || 
                       screen.getByText('测试会话').closest('div');
    if (sessionItem) {
      await user.click(sessionItem);
      expect(mockOnSelect).toHaveBeenCalled();
    }
  });

  it('应该显示编辑和删除按钮', () => {
    customRender(
      <SessionItem
        session={mockSession}
        onDelete={mockOnDelete}
        onUpdate={mockOnUpdate}
      />
    );

    expect(screen.getByRole('button', { name: 'edit' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'delete' })).toBeInTheDocument();
  });

  it('应该打开编辑对话框', async () => {
    const user = userEvent.setup();
    const { sessionApi } = await import('@/services/session');
    vi.mocked(sessionApi.updateSession).mockResolvedValue({
      ...mockSession,
      title: '更新后的标题',
    });

    customRender(
      <SessionItem
        session={mockSession}
        onUpdate={mockOnUpdate}
      />
    );

    const editButton = screen.getByRole('button', { name: 'edit' });
    await user.click(editButton);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
  });

  it('应该删除会话', async () => {
    const user = userEvent.setup();
    customRender(
      <SessionItem session={mockSession} onDelete={mockOnDelete} />
    );

    const deleteButton = screen.getByRole('button', { name: 'delete' });
    await user.click(deleteButton);

    expect(mockOnDelete).toHaveBeenCalled();
  });
});

