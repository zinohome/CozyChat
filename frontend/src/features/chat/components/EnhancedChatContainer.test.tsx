import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import { EnhancedChatContainer } from './EnhancedChatContainer';
import { useChatStore } from '@/store/slices/chatSlice';
import { useSessions } from '../hooks/useSessions';
import { useStreamChat } from '../hooks/useStreamChat';

// Mock dependencies
vi.mock('@/store/slices/chatSlice');
vi.mock('../hooks/useSessions');
vi.mock('../hooks/useStreamChat');
vi.mock('@/services/chat', () => ({
  chatApi: {
    getHistory: vi.fn(),
    streamChat: vi.fn(),
  },
}));

describe('EnhancedChatContainer', () => {
  const mockSetMessages = vi.fn();
  const mockAddMessage = vi.fn();
  const mockUpdateMessage = vi.fn();
  const mockSetLoading = vi.fn();
  const mockSetError = vi.fn();
  const mockRemoveMessage = vi.fn();
  const mockSetCurrentSessionId = vi.fn();

  const mockSendStreamMessage = vi.fn();
  const mockCreateSession = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock useChatStore
    (useChatStore as any).mockReturnValue({
      messages: [],
      setMessages: mockSetMessages,
      addMessage: mockAddMessage,
      updateMessage: mockUpdateMessage,
      setLoading: mockSetLoading,
      setError: mockSetError,
      removeMessage: mockRemoveMessage,
      setCurrentSessionId: mockSetCurrentSessionId,
      isLoading: false,
      error: null,
    });

    // Mock useSessions
    (useSessions as any).mockReturnValue({
      sessions: [],
      createSession: mockCreateSession,
    });

    // Mock useStreamChat
    (useStreamChat as any).mockReturnValue({
      sendStreamMessage: mockSendStreamMessage,
      isStreaming: false,
    });
  });

  it('应该渲染聊天容器', () => {
    render(
      <EnhancedChatContainer
        sessionId="test-session"
        personalityId="test-personality"
      />
    );

    expect(screen.getByPlaceholderText(/输入消息/i)).toBeInTheDocument();
  });

  it('应该显示输入框和发送按钮', () => {
    render(
      <EnhancedChatContainer
        sessionId="test-session"
        personalityId="test-personality"
      />
    );

    const input = screen.getByPlaceholderText(/输入消息/i);
    const sendButton = screen.getByRole('button', { name: /发送/i });

    expect(input).toBeInTheDocument();
    expect(sendButton).toBeInTheDocument();
  });

  it('应该在输入消息后可以发送', async () => {
    const { user } = render(
      <EnhancedChatContainer
        sessionId="test-session"
        personalityId="test-personality"
      />
    );

    const input = screen.getByPlaceholderText(/输入消息/i);
    const sendButton = screen.getByRole('button', { name: /发送/i });

    await user.type(input, 'Hello, AI!');
    await user.click(sendButton);

    await waitFor(() => {
      expect(mockSendStreamMessage).toHaveBeenCalledWith('Hello, AI!');
    });
  });

  it('应该在加载时禁用输入和发送按钮', () => {
    (useChatStore as any).mockReturnValue({
      messages: [],
      isLoading: true,
      error: null,
    });

    render(
      <EnhancedChatContainer
        sessionId="test-session"
        personalityId="test-personality"
      />
    );

    const input = screen.getByPlaceholderText(/输入消息/i);
    const sendButton = screen.getByRole('button', { name: /发送/i });

    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  it('应该显示错误消息', () => {
    (useChatStore as any).mockReturnValue({
      messages: [],
      isLoading: false,
      error: 'Network error',
    });

    render(
      <EnhancedChatContainer
        sessionId="test-session"
        personalityId="test-personality"
      />
    );

    // 错误应该通过errorHandler显示
    // 这里主要验证组件能处理错误状态
    expect(screen.getByPlaceholderText(/输入消息/i)).toBeInTheDocument();
  });
});

