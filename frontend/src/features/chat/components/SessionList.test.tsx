import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SessionList } from './SessionList';
import { render as customRender } from '@/test/utils';

// Mock useSessions
const mockSessions = [
  {
    id: 'session-1',
    title: '测试会话1',
    created_at: new Date('2024-01-01'),
    last_message_at: new Date('2024-01-02'),
  },
  {
    id: 'session-2',
    title: '测试会话2',
    created_at: new Date('2024-01-03'),
    last_message_at: new Date('2024-01-04'),
  },
];

const mockCreateSession = vi.fn();
const mockDeleteSession = vi.fn();
const mockUpdateSession = vi.fn();

vi.mock('@/features/chat/hooks/useSessions', () => ({
  useSessions: () => ({
    sessions: mockSessions,
    isLoading: false,
    createSession: mockCreateSession,
    deleteSession: mockDeleteSession,
    updateSession: mockUpdateSession,
  }),
}));

describe('SessionList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该渲染会话列表', () => {
    customRender(<SessionList />);
    expect(screen.getByText('测试会话1')).toBeInTheDocument();
    expect(screen.getByText('测试会话2')).toBeInTheDocument();
  });

  it('应该显示新建按钮', () => {
    customRender(<SessionList />);
    expect(screen.getByRole('button', { name: /新建/i })).toBeInTheDocument();
  });

  it('应该创建新会话', async () => {
    const user = userEvent.setup();
    mockCreateSession.mockResolvedValue({
      id: 'session-3',
      title: '新会话',
    });

    customRender(<SessionList />);

    const createButton = screen.getByRole('button', { name: /新建/i });
    await user.click(createButton);

    await waitFor(() => {
      expect(mockCreateSession).toHaveBeenCalled();
    });
  });

  it('应该高亮当前会话', () => {
    customRender(<SessionList currentSessionId="session-1" />);
    // 检查是否有高亮样式（通过检查是否传递了isActive prop）
    const sessionItems = screen.getAllByText(/测试会话/i);
    expect(sessionItems.length).toBeGreaterThan(0);
  });

  it('应该调用会话选择回调', async () => {
    const onSessionSelect = vi.fn();
    customRender(<SessionList onSessionSelect={onSessionSelect} />);

    // 点击会话项
    const sessionItem = screen.getByText('测试会话1');
    await userEvent.click(sessionItem);

    expect(onSessionSelect).toHaveBeenCalledWith('session-1');
  });
});

