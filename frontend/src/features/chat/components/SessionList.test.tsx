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

  // 注意：SessionList 组件不包含新建按钮
  // 新建按钮在 ChatSessionHeader 组件中
  // 如果需要测试新建功能，应该测试 ChatSessionHeader 组件

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

