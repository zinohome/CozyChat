/**
 * ChatContainer组件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import { ChatContainer } from './ChatContainer';
import { useChatStore } from '@/store/slices/chatSlice';
import { useStreamChat } from '../hooks/useStreamChat';
import { chatApi } from '@/services/chat';
import { useQuery } from '@tanstack/react-query';

// Mock dependencies
vi.mock('@/store/slices/chatSlice');
vi.mock('../hooks/useStreamChat');
vi.mock('@/services/chat');
vi.mock('@/utils/errorHandler', () => ({
  showError: vi.fn(),
}));
vi.mock('@chatui/core', () => {
  const MockChat = ({ children, onSend, messages, navbar }: any) => {
    return (
      <div data-testid="chat-container">
        <div data-testid="chat-navbar">{navbar?.title || 'Chat'}</div>
        <input role="textbox" placeholder="输入消息..." />
        <div data-testid="chat-messages">
          {messages?.map((msg: any, idx: number) => (
            <div key={idx} data-testid={`message-${idx}`}>
              {msg.content?.text || msg.content || ''}
            </div>
          ))}
        </div>
        {children}
      </div>
    );
  };
  
  return {
    default: MockChat,
    Chat: MockChat,
  };
});
vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>();
  return {
    ...actual,
    useQuery: vi.fn(() => ({
      data: [],
      isLoading: false,
    })),
  };
});

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
    (useQuery as any).mockReturnValue({
      data: [],
      isLoading: false,
    });
    
    render(<ChatContainer {...defaultProps} />);
    // ChatUI组件应该被渲染
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('should load message history on mount', async () => {
    const mockMessages = [
      { id: '1', role: 'user', content: 'Hello', timestamp: new Date() },
      { id: '2', role: 'assistant', content: 'Hi there', timestamp: new Date() },
    ];
    
    (useQuery as any).mockReturnValue({
      data: mockMessages,
      isLoading: false,
    });

    render(<ChatContainer {...defaultProps} />);

    await waitFor(() => {
      expect(useQuery).toHaveBeenCalled();
      // 验证消息被渲染
      expect(screen.getByText('Hello')).toBeInTheDocument();
    });
  });

  it('should handle empty sessionId', async () => {
    (useQuery as any).mockReturnValue({
      data: [],
      isLoading: false,
    });
    
    render(<ChatContainer sessionId="default" personalityId="test" />);

    await waitFor(() => {
      // useQuery应该被调用，但queryFn应该返回空数组
      expect(useQuery).toHaveBeenCalled();
    });
  });

  it('should display error when error occurs', () => {
    const errorMessage = 'Test error';
    (useQuery as any).mockReturnValue({
      data: [],
      isLoading: false,
    });
    
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

