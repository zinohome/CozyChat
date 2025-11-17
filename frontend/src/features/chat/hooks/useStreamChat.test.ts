/**
 * useStreamChat Hook测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useStreamChat } from './useStreamChat';
import { chatApi } from '@/services/chat';
import { useChatStore } from '@/store/slices/chatSlice';
import { useAuthStore } from '@/store/slices/authSlice';

// Mock dependencies
vi.mock('@/services/chat');
vi.mock('@/store/slices/chatSlice');
vi.mock('@/store/slices/authSlice');

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
  const mockSetLoading = vi.fn();
  const mockSetError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    (useChatStore as any).mockReturnValue({
      setLoading: mockSetLoading,
      setError: mockSetError,
    });

    (useAuthStore as any).mockReturnValue({
      user: { id: 'user-1' },
    });
  });

  it('should initialize with correct state', () => {
    const { result } = renderHook(
      () => useStreamChat('session-1', 'personality-1'),
      { wrapper: createWrapper() }
    );

    expect(result.current.isStreaming).toBe(false);
    expect(typeof result.current.sendStreamMessage).toBe('function');
  });

  it('should send stream message', async () => {
    // Mock stream response
    const mockStream = async function* () {
      yield { data: '{"content":"Hello"}' };
      yield { data: '{"content":" World"}' };
      yield { data: '[DONE]' };
    };

    (chatApi.streamChat as any).mockReturnValue(mockStream());

    const { result } = renderHook(
      () => useStreamChat('session-1', 'personality-1'),
      { wrapper: createWrapper() }
    );

    await result.current.sendStreamMessage('Test message');

    expect(chatApi.streamChat).toHaveBeenCalled();
    expect(mockSetLoading).toHaveBeenCalled();
  });

  it('should handle stream error', async () => {
    const error = new Error('Stream failed');
    (chatApi.streamChat as any).mockRejectedValue(error);

    const { result } = renderHook(
      () => useStreamChat('session-1', 'personality-1'),
      { wrapper: createWrapper() }
    );

    try {
    await result.current.sendStreamMessage('Test message');
    } catch (e) {
      // Expected error
    }

      expect(mockSetError).toHaveBeenCalled();
    });

  it('should handle empty content', async () => {
    const { result } = renderHook(
      () => useStreamChat('session-1', 'personality-1'),
      { wrapper: createWrapper() }
    );

    // 空内容应该被处理
    await result.current.sendStreamMessage('');

    // 不应该调用API
    expect(chatApi.streamChat).not.toHaveBeenCalled();
  });
});
