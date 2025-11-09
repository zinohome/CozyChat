import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { Message } from '@/types/chat';

/**
 * 聊天状态
 */
interface ChatState {
  currentSessionId: string | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

/**
 * 聊天Actions
 */
interface ChatActions {
  setCurrentSessionId: (sessionId: string | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateMessage: (messageId: string, updates: Partial<Message>) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

/**
 * 聊天Store
 */
type ChatStore = ChatState & ChatActions;

/**
 * 初始状态
 */
const initialState: ChatState = {
  currentSessionId: null,
  messages: [],
  isLoading: false,
  error: null,
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

        setMessages: (messages) =>
          set({
            messages,
            error: null,
          }),

        addMessage: (message) =>
          set((state) => ({
            messages: [...state.messages, message],
            error: null,
          })),

        updateMessage: (messageId, updates) =>
          set((state) => ({
            messages: state.messages.map((msg) =>
              msg.id === messageId ? { ...msg, ...updates } : msg
            ),
          })),

        clearMessages: () =>
          set({
            messages: [],
            error: null,
          }),

        setLoading: (loading) =>
          set({
            isLoading: loading,
          }),

        setError: (error) =>
          set({
            error,
          }),
      }),
      {
        name: 'chat-storage',
        partialize: (state) => ({
          currentSessionId: state.currentSessionId,
          messages: state.messages,
        }),
      }
    ),
    { name: 'ChatStore' }
  )
);

