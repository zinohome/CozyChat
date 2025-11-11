import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from './chatSlice';
import type { Message } from '@/types/chat';

describe('chatSlice', () => {
  beforeEach(() => {
    // 重置store状态
    useChatStore.setState({
      messages: [],
      loading: false,
      error: null,
      currentSessionId: null,
    });
  });

  it('应该初始化空状态', () => {
    const state = useChatStore.getState();
    expect(state.messages).toHaveLength(0);
    expect(state.loading).toBe(false);
    expect(state.error).toBe(null);
  });

  it('应该添加消息', () => {
    const message: Message = {
      id: 'msg-1',
      role: 'user',
      content: 'Hello',
      timestamp: new Date(),
    };

    useChatStore.getState().addMessage(message);
    const state = useChatStore.getState();

    expect(state.messages).toHaveLength(1);
    expect(state.messages[0].id).toBe('msg-1');
  });

  it('应该更新消息', () => {
    const message: Message = {
      id: 'msg-1',
      role: 'user',
      content: 'Hello',
      timestamp: new Date(),
    };

    useChatStore.getState().addMessage(message);
    useChatStore.getState().updateMessage('msg-1', { content: 'Updated' });

    const state = useChatStore.getState();
    expect(state.messages[0].content).toBe('Updated');
  });

  it('应该删除消息', () => {
    const message: Message = {
      id: 'msg-1',
      role: 'user',
      content: 'Hello',
      timestamp: new Date(),
    };

    useChatStore.getState().addMessage(message);
    useChatStore.getState().removeMessage('msg-1');

    const state = useChatStore.getState();
    expect(state.messages).toHaveLength(0);
  });

  it('应该设置加载状态', () => {
    useChatStore.getState().setLoading(true);
    const state = useChatStore.getState();
    expect(state.isLoading).toBe(true);
  });

  it('应该设置错误', () => {
    useChatStore.getState().setError('Test error');
    expect(useChatStore.getState().error).toBe('Test error');
  });

  it('应该清除消息', () => {
    const message: Message = {
      id: 'msg-1',
      role: 'user',
      content: 'Hello',
      timestamp: new Date(),
    };

    useChatStore.getState().addMessage(message);
    useChatStore.getState().clearMessages();

    const state = useChatStore.getState();
    expect(state.messages).toHaveLength(0);
    expect(state.error).toBe(null);
  });
});

