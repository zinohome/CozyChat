import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useStreamChat } from './useStreamChat';
import { chatApi } from '@/services/chat';
import { useChatStore } from '@/store/slices/chatSlice';

// Mock dependencies
vi.mock('@/services/chat');
vi.mock('@/store/slices/chatSlice');

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

describe('useStreamChat', () => {
  const mockAddMessage = vi.fn();
  const mockUpdateMessage = vi.fn();
  const mockSetLoading = vi.fn();
  const mockSetError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    (useChatStore as any).mockReturnValue({
      addMessage: mockAddMessage,
      updateMessage: mockUpdateMessage,
      setLoading: mockSetLoading,
      setError: mockSetError,
    });
  });

  it('应该初始化Hook', () => {
    const { result } = renderHook(
      () => useStreamChat('session-1', 'personality-1'),
      { wrapper: createWrapper() }
    );

    expect(result.current).toBeDefined();
    expect(result.current.sendStreamMessage).toBeDefined();
    expect(typeof result.current.sendStreamMessage).toBe('function');
  });

  it('应该发送流式消息', async () => {
    const mockStream = async function* () {
      yield {
        choices: [
          {
            delta: { content: 'Hello' },
          },
        ],
      };
      yield {
        choices: [
          {
            delta: { content: ' World' },
          },
        ],
      };
      yield {
        choices: [
          {
            finish_reason: 'stop',
          },
        ],
      };
    };

    (chatApi.streamChat as any).mockReturnValue(mockStream());

    const { result } = renderHook(
      () => useStreamChat('session-1', 'personality-1'),
      { wrapper: createWrapper() }
    );

    await result.current.sendStreamMessage('Test message');

    await waitFor(() => {
      expect(mockAddMessage).toHaveBeenCalled();
      expect(mockUpdateMessage).toHaveBeenCalled();
    });
  });

  it('应该处理流式错误', async () => {
    const error = new Error('Stream error');
    (chatApi.streamChat as any).mockRejectedValue(error);

    const { result } = renderHook(
      () => useStreamChat('session-1', 'personality-1'),
      { wrapper: createWrapper() }
    );

    await result.current.sendStreamMessage('Test message');

    await waitFor(() => {
      expect(mockSetError).toHaveBeenCalled();
    });
  });

  it('应该在发送时设置加载状态', async () => {
    const mockStream = async function* () {
      yield {
        choices: [
          {
            delta: { content: 'Hello' },
          },
        ],
      };
    };

    (chatApi.streamChat as any).mockReturnValue(mockStream());

    const { result } = renderHook(
      () => useStreamChat('session-1', 'personality-1'),
      { wrapper: createWrapper() }
    );

    const sendPromise = result.current.sendStreamMessage('Test');

    expect(mockSetLoading).toHaveBeenCalledWith(true);

    await sendPromise;

    await waitFor(() => {
      expect(mockSetLoading).toHaveBeenCalledWith(false);
    });
  });
});

