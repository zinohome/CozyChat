/**
 * useChat Hook测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useChat } from './useChat';
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

describe('useChat', () => {
  const mockSetLoading = vi.fn();
  const mockSetError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    (useChatStore as any).mockReturnValue({
      isLoading: false,
      setLoading: mockSetLoading,
      setError: mockSetError,
      error: null,
    });
  });

  it('should load message history', async () => {
    const mockMessages = [
      { id: '1', role: 'user', content: 'Hello', timestamp: new Date() },
      { id: '2', role: 'assistant', content: 'Hi', timestamp: new Date() },
    ];
    (chatApi.getHistory as any).mockResolvedValue(mockMessages);

    const { result } = renderHook(
      () => useChat('session-1', 'personality-1'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(chatApi.getHistory).toHaveBeenCalledWith('session-1');
    expect(result.current.messages).toEqual(mockMessages);
  });

  it('should handle empty sessionId', async () => {
    const { result } = renderHook(
      () => useChat('', 'personality-1'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(chatApi.getHistory).not.toHaveBeenCalled();
    expect(result.current.messages).toEqual([]);
  });

  it('should send message successfully', async () => {
    const mockResponse = {
      id: 'response-1',
      created: Date.now() / 1000,
      choices: [
        {
          message: {
            role: 'assistant',
            content: 'Response message',
          },
        },
      ],
    };

    (chatApi.getHistory as any).mockResolvedValue([]);
    (chatApi.send as any).mockResolvedValue(mockResponse);

    const { result } = renderHook(
      () => useChat('session-1', 'personality-1'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await result.current.sendMessage('Hello');

    expect(chatApi.send).toHaveBeenCalled();
    expect(mockSetLoading).toHaveBeenCalled();
  });

  it('should handle send message error', async () => {
    const error = new Error('Send failed');
    (chatApi.getHistory as any).mockResolvedValue([]);
    (chatApi.send as any).mockRejectedValue(error);

    const { result } = renderHook(
      () => useChat('session-1', 'personality-1'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    try {
      await result.current.sendMessage('Hello');
    } catch (e) {
      // Expected error
    }

    expect(mockSetError).toHaveBeenCalled();
    expect(mockSetLoading).toHaveBeenCalledWith(false);
  });

  it('should return loading state', () => {
    (useChatStore as any).mockReturnValue({
      isLoading: true,
      setLoading: mockSetLoading,
      setError: mockSetError,
      error: null,
    });

    (chatApi.getHistory as any).mockResolvedValue([]);

    const { result } = renderHook(
      () => useChat('session-1', 'personality-1'),
      { wrapper: createWrapper() }
    );

    expect(result.current.isLoading).toBe(true);
  });
});

