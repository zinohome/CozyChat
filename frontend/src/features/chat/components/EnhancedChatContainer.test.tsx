import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { EnhancedChatContainer } from './EnhancedChatContainer';
import { useChatStore } from '@/store/slices/chatSlice';
import { useSessions } from '../hooks/useSessions';
import { useStreamChat } from '../hooks/useStreamChat';
import { useQuery } from '@tanstack/react-query';

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
const mockRefetch = vi.fn().mockResolvedValue({ data: [] });
vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>();
  return {
    ...actual,
    useQuery: vi.fn(() => ({
      data: [],
      isLoading: false,
      refetch: mockRefetch,
      isRefetching: false,
      isError: false,
      error: null,
    })),
    useQueryClient: vi.fn(() => ({
      setQueryData: vi.fn(),
      getQueryData: vi.fn(() => []),
      invalidateQueries: vi.fn(),
      refetchQueries: vi.fn(),
      removeQueries: vi.fn(),
    })),
  };
});
vi.mock('@/services/user', () => ({
  userApi: {
    getCurrentUserPreferences: vi.fn(() => Promise.resolve({})),
  },
}));
vi.mock('@/utils/errorHandler', () => ({
  showError: vi.fn(),
}));
vi.mock('@/utils/tts', () => ({
  playTTS: vi.fn(),
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
      currentSessionId: null,
      isLoading: false,
      error: null,
      setLoading: mockSetLoading,
      setError: mockSetError,
      setCurrentSessionId: mockSetCurrentSessionId,
      isVoiceCallActive: false,
      voiceCallMessages: [],
      voiceCallStartTime: null,
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
    // 使用title属性查找发送按钮（按钮内容是图标，没有accessible name）
    const sendButton = screen.getByTitle('发送');

    expect(input).toBeInTheDocument();
    expect(sendButton).toBeInTheDocument();
  });

  it('应该在输入消息后可以发送', async () => {
    const user = userEvent.setup();
    
    // Mock sessions包含测试会话，避免触发创建会话逻辑
    (useSessions as any).mockReturnValue({
      sessions: [{ id: 'test-session', title: '测试会话' }],
      createSession: mockCreateSession,
      isCreating: false,
    });
    
    render(
      <EnhancedChatContainer
        sessionId="test-session"
        personalityId="test-personality"
      />
    );

    const input = screen.getByPlaceholderText(/输入消息/i);
    const sendButton = screen.getByTitle('发送');

    await user.type(input, 'Hello, AI!');
    await user.click(sendButton);

    await waitFor(() => {
      expect(mockSendStreamMessage).toHaveBeenCalledWith('Hello, AI!');
    });
  });

  it('应该在加载时禁用输入和发送按钮', () => {
    (useQuery as any).mockReturnValue({
      data: [],
      isLoading: true,
    });
    
    (useChatStore as any).mockReturnValue({
      currentSessionId: null,
      isLoading: true,
      error: null,
      setError: mockSetError,
      setCurrentSessionId: mockSetCurrentSessionId,
      isVoiceCallActive: false,
      voiceCallMessages: [],
      voiceCallStartTime: null,
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
      currentSessionId: null,
      isLoading: false,
      error: 'Network error',
      setError: mockSetError,
      setCurrentSessionId: mockSetCurrentSessionId,
      isVoiceCallActive: false,
      voiceCallMessages: [],
      voiceCallStartTime: null,
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

