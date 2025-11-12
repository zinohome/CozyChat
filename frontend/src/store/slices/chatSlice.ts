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
  removeMessage: (messageId: string) => void;
  clearMessages: () => void;
  clearMessagesBySessionId: (sessionId: string) => void;
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
            messages: Array.isArray(messages) ? messages : [],
            error: null,
          }),

        addMessage: (message) =>
          set((state) => ({
            messages: [...state.messages, message],
            error: null,
          })),

        updateMessage: (messageId, updates) =>
          set((state) => {
            // 检查消息是否存在
            const messageIndex = state.messages.findIndex((msg) => msg.id === messageId);
            if (messageIndex === -1) {
              // 消息不存在，返回原状态，避免触发重新渲染
              return state;
            }
            
            const currentMessage = state.messages[messageIndex];
            
            // 检查是否有实际变化（深度比较关键字段）
            let hasChanges = false;
            for (const key in updates) {
              const currentValue = currentMessage[key as keyof Message];
              const newValue = updates[key as keyof Message];
              
              // 对于 content 字段，进行字符串比较
              if (key === 'content') {
                const currentContent = typeof currentValue === 'string' ? currentValue : String(currentValue || '');
                const newContent = typeof newValue === 'string' ? newValue : String(newValue || '');
                if (currentContent !== newContent) {
                  hasChanges = true;
                  break;
                }
              } else if (key === 'timestamp') {
                // 对于 timestamp，比较时间戳值（忽略毫秒级差异）
                const currentTs = currentValue instanceof Date 
                  ? Math.floor(currentValue.getTime() / 1000) 
                  : (typeof currentValue === 'string' ? Math.floor(new Date(currentValue).getTime() / 1000) : currentValue);
                const newTs = newValue instanceof Date 
                  ? Math.floor(newValue.getTime() / 1000) 
                  : (typeof newValue === 'string' ? Math.floor(new Date(newValue).getTime() / 1000) : newValue);
                if (currentTs !== newTs) {
                  hasChanges = true;
                  break;
                }
              } else if (currentValue !== newValue) {
                hasChanges = true;
                break;
              }
            }
            
            if (!hasChanges) {
              // 没有变化，返回原状态对象（相同的引用），避免触发重新渲染
              return state;
            }
            
            // 有变化，创建新的消息数组
            const updatedMessage = { ...currentMessage, ...updates };
            const newMessages = [...state.messages];
            newMessages[messageIndex] = updatedMessage;
            
            return {
              messages: newMessages,
            };
          }),

        removeMessage: (messageId) =>
          set((state) => ({
            messages: state.messages.filter((msg) => msg.id !== messageId),
          })),

        clearMessages: () =>
          set({
            messages: [],
            error: null,
          }),

        clearMessagesBySessionId: (sessionId) =>
          set((state) => ({
            messages: state.messages.filter(
              (msg) => msg.session_id !== sessionId
            ),
          })),

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
          messages: Array.isArray(state.messages) ? state.messages : [],
        }),
      }
    ),
    { name: 'ChatStore' }
  )
);

