import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { Message } from '@/types/chat';

/**
 * 聊天状态（客户端UI状态）
 * 
 * 注意：不存储服务端数据（sessions、messages），这些数据通过 React Query 管理
 */
interface ChatState {
  currentSessionId: string | null;
  isLoading: boolean;
  error: string | null;
  // 语音通话状态
  isVoiceCallActive: boolean;
  voiceCallMessages: Message[];
  voiceCallStartTime: number | null;
}

/**
 * 聊天Actions
 */
interface ChatActions {
  setCurrentSessionId: (sessionId: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  // 语音通话Actions
  startVoiceCall: () => void;
  endVoiceCall: () => void;
  addVoiceCallMessage: (message: Message) => void;
  clearVoiceCallMessages: () => void;
}

/**
 * 聊天Store
 */
type ChatStore = ChatState & ChatActions;

/**
 * 获取语音通话时长（秒）
 */
export const getVoiceCallDuration = (startTime: number | null): number => {
  if (!startTime) return 0;
  return Math.floor((Date.now() - startTime) / 1000);
};

/**
 * 初始状态
 */
const initialState: ChatState = {
  currentSessionId: null,
  isLoading: false,
  error: null,
  // 语音通话初始状态
  isVoiceCallActive: false,
  voiceCallMessages: [],
  voiceCallStartTime: null,
};

/**
 * 聊天状态管理Store
 *
 * 使用Zustand管理聊天相关的全局状态。
 */
export const useChatStore = create<ChatStore>()(
  devtools(
    persist(
      (set) => ({
        ...initialState,

        setCurrentSessionId: (sessionId) =>
          set({
            currentSessionId: sessionId,
          }),

        setLoading: (loading) =>
          set({
            isLoading: loading,
          }),

        setError: (error) =>
          set({
            error,
          }),
        
        // 语音通话Actions
        startVoiceCall: () =>
          set({
            isVoiceCallActive: true,
            voiceCallStartTime: Date.now(),
            voiceCallMessages: [],
          }),
        
        endVoiceCall: () =>
          set({
            isVoiceCallActive: false,
            voiceCallStartTime: null,
          }),
        
        addVoiceCallMessage: (message) =>
          set((state) => ({
            voiceCallMessages: [...state.voiceCallMessages, message],
          })),
        
        clearVoiceCallMessages: () =>
          set({
            voiceCallMessages: [],
          }),
      }),
      {
        name: 'chat-storage',
        partialize: (state) => ({
          currentSessionId: state.currentSessionId,
          // 不再持久化 messages，因为消息通过 React Query 管理
          // 不持久化语音通话状态，每次刷新后重置
        }),
      }
    ),
    { name: 'ChatStore' }
  )
);

