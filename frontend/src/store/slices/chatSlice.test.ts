import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from './chatSlice';
import type { Message } from '@/types/chat';

describe('chatSlice', () => {
  beforeEach(() => {
    // 重置store状态
    useChatStore.setState({
      currentSessionId: null,
      isLoading: false,
      error: null,
      isVoiceCallActive: false,
      voiceCallMessages: [],
      voiceCallStartTime: null,
    });
  });

  it('应该初始化空状态', () => {
    const state = useChatStore.getState();
    expect(state.currentSessionId).toBe(null);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe(null);
  });

  it('应该设置当前会话ID', () => {
    useChatStore.getState().setCurrentSessionId('session-1');
    const state = useChatStore.getState();
    expect(state.currentSessionId).toBe('session-1');
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

  it('应该清除错误', () => {
    useChatStore.getState().setError('Test error');
    useChatStore.getState().setError(null);
    expect(useChatStore.getState().error).toBe(null);
  });

  it('应该启动语音通话', () => {
    useChatStore.getState().startVoiceCall();
    const state = useChatStore.getState();
    expect(state.isVoiceCallActive).toBe(true);
    expect(state.voiceCallStartTime).not.toBe(null);
  });

  it('应该添加语音通话消息', () => {
    useChatStore.getState().startVoiceCall();
    const message: Message = {
      id: 'msg-1',
      role: 'user',
      content: 'Hello',
      timestamp: new Date(),
    };
    useChatStore.getState().addVoiceCallMessage(message);
    const state = useChatStore.getState();
    expect(state.voiceCallMessages).toHaveLength(1);
  });
});

