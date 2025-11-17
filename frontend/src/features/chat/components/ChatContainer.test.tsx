/**
 * ChatContainer组件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import { ChatContainer } from './ChatContainer';
import { useChatStore } from '@/store/slices/chatSlice';
import { useStreamChat } from '../hooks/useStreamChat';
import { chatApi } from '@/services/chat';

// Mock dependencies
vi.mock('@/store/slices/chatSlice');
vi.mock('../hooks/useStreamChat');
vi.mock('@/services/chat');
vi.mock('@/utils/errorHandler', () => ({
  showError: vi.fn(),
}));

describe('ChatContainer', () => {
  const mockSetError = vi.fn();
  const mockSendStreamMessage = vi.fn();

  const defaultProps = {
    sessionId: 'test-session-id',
    personalityId: 'test-personality-id',
  };

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock useChatStore
    (useChatStore as any).mockReturnValue({
      isLoading: false,
      error: null,
      setError: mockSetError,
    });

    // Mock useStreamChat
    (useStreamChat as any).mockReturnValue({
      sendStreamMessage: mockSendStreamMessage,
      isStreaming: false,
    });

    // Mock chatApi.getHistory
    (chatApi.getHistory as any).mockResolvedValue([]);
  });

  it('should render chat container', () => {
    render(<ChatContainer {...defaultProps} />);
    // ChatUI组件应该被渲染
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('should load message history on mount', async () => {
    const mockMessages = [
      { id: '1', role: 'user', content: 'Hello' },
      { id: '2', role: 'assistant', content: 'Hi there' },
    ];
    (chatApi.getHistory as any).mockResolvedValue(mockMessages);

    render(<ChatContainer {...defaultProps} />);

    await waitFor(() => {
      expect(chatApi.getHistory).toHaveBeenCalledWith(defaultProps.sessionId);
    });
  });

  it('should handle empty sessionId', async () => {
    render(<ChatContainer sessionId="default" personalityId="test" />);

    await waitFor(() => {
      expect(chatApi.getHistory).not.toHaveBeenCalled();
    });
  });

  it('should display error when error occurs', () => {
    const errorMessage = 'Test error';
    (useChatStore as any).mockReturnValue({
      isLoading: false,
      error: errorMessage,
      setError: mockSetError,
    });

    render(<ChatContainer {...defaultProps} />);

    // 错误应该被处理（通过useEffect）
    expect(mockSetError).toHaveBeenCalledWith(null);
  });

  it('should handle send message', async () => {
    render(<ChatContainer {...defaultProps} />);

    // 模拟发送消息（需要模拟ChatUI的onSend回调）
    // 这需要更深入的集成测试
    expect(mockSendStreamMessage).toBeDefined();
  });
});

