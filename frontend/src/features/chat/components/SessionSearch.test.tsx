import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SessionSearch } from './SessionSearch';
import { render as customRender } from '@/test/utils';

// Mock useSessions
const mockSessions = [
  {
    id: 'session-1',
    title: '测试会话1',
    created_at: new Date(),
  },
  {
    id: 'session-2',
    title: '测试会话2',
    created_at: new Date(),
  },
];

vi.mock('@/features/chat/hooks/useSessions', () => ({
  useSessions: () => ({
    sessions: mockSessions,
    isLoading: false,
  }),
}));

describe('SessionSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该渲染搜索输入框', () => {
    customRender(<SessionSearch />);
    expect(screen.getByPlaceholderText(/搜索会话/i)).toBeInTheDocument();
  });

  it('应该过滤会话', async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn();

    customRender(<SessionSearch onSearch={onSearch} />);

    const searchInput = screen.getByPlaceholderText(/搜索会话/i);
    await user.type(searchInput, '测试会话1');

    await new Promise((resolve) => setTimeout(resolve, 300)); // 等待防抖

    expect(onSearch).toHaveBeenCalled();
  });
});

