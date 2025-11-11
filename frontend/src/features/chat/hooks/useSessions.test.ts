import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSessions } from './useSessions';
import * as sessionApiModule from '@/services/session';

// Mock sessionApi
const mockGetSessions = vi.fn();
const mockCreateSession = vi.fn();
const mockUpdateSession = vi.fn();
const mockDeleteSession = vi.fn();

vi.mock('@/services/session', () => ({
  sessionApi: {
    getSessions: () => mockGetSessions(),
    createSession: (...args: any[]) => mockCreateSession(...args),
    updateSession: (...args: any[]) => mockUpdateSession(...args),
    deleteSession: (...args: any[]) => mockDeleteSession(...args),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useSessions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该获取会话列表', async () => {
    const mockSessions = [
      {
        id: 'session-1',
        title: '测试会话',
        created_at: new Date(),
      },
    ];

    mockGetSessions.mockResolvedValue({
      items: mockSessions,
      total: 1,
    });

    const { result } = renderHook(() => useSessions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.sessions).toEqual(mockSessions);
  });

  it('应该创建会话', async () => {
    const newSession = {
      id: 'session-2',
      title: '新会话',
      created_at: new Date(),
    };

    mockCreateSession.mockResolvedValue(newSession);
    mockGetSessions.mockResolvedValue({
      items: [],
      total: 0,
    });

    const { result } = renderHook(() => useSessions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await result.current.createSession({ title: '新会话' });

    expect(mockCreateSession).toHaveBeenCalledWith({ title: '新会话' });
  });

  it('应该更新会话', async () => {
    mockGetSessions.mockResolvedValue({
      items: [],
      total: 0,
    });

    const updatedSession = {
      id: 'session-1',
      title: '更新后的标题',
      created_at: new Date(),
    };

    mockUpdateSession.mockResolvedValue(updatedSession);

    const { result } = renderHook(() => useSessions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await result.current.updateSession('session-1', { title: '更新后的标题' });

    expect(mockUpdateSession).toHaveBeenCalledWith('session-1', {
      title: '更新后的标题',
    });
  });

  it('应该删除会话', async () => {
    mockGetSessions.mockResolvedValue({
      items: [],
      total: 0,
    });

    mockDeleteSession.mockResolvedValue(undefined);

    const { result } = renderHook(() => useSessions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await result.current.deleteSession('session-1');

    expect(mockDeleteSession).toHaveBeenCalledWith('session-1');
  });
});

