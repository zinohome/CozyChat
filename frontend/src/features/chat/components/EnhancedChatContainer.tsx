import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Input, Spin } from 'antd';
import { SendOutlined, PhoneOutlined } from '@ant-design/icons';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useChatStore } from '@/store/slices/chatSlice';
import { useAuthStore } from '@/store/slices/authSlice';
import { useStreamChat } from '../hooks/useStreamChat';
import { useSessions } from '../hooks/useSessions';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { useUIStore } from '@/store/slices/uiSlice';
import { chatApi } from '@/services/chat';
import { MessageBubble } from './MessageBubble';
import { VoiceCallIndicator } from './VoiceCallIndicator';
import { showError } from '@/utils/errorHandler';
import { userApi } from '@/services/user';
import { playTTS } from '@/utils/tts';
import { useVoiceRecorder } from '@/hooks/useVoiceRecorder';
import { useVoiceAgent } from '@/hooks/useVoiceAgent';
import type { Message } from '@/types/chat';

const { TextArea } = Input;

/**
 * 增强聊天容器组件属性
 */
interface EnhancedChatContainerProps {
  /** 会话ID */
  sessionId: string;
  /** 人格ID */
  personalityId: string;
}

/**
 * 增强聊天容器组件
 *
 * 使用自定义消息渲染，支持Markdown、代码高亮和消息操作。
 */
export const EnhancedChatContainer: React.FC<EnhancedChatContainerProps> = ({
  sessionId,
  personalityId,
}) => {
  const { 
    isLoading: isLoadingStore, 
    error, 
    setError, 
    setCurrentSessionId,
    isVoiceCallActive,
    voiceCallMessages,
    startVoiceCall,
    endVoiceCall,
    addVoiceCallMessage,
    clearVoiceCallMessages,
  } = useChatStore();
  const { sessions, createSession } = useSessions();
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const userId = user?.id || null;
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<any>(null);
  const isMobile = useIsMobile();
  // 使用 sessionId prop 作为当前会话ID（确保切换时立即更新）
  const currentSessionId = sessionId === 'default' ? null : sessionId;
  const { chatBackgroundStyle } = useUIStore();
  const lastAutoPlayedMessageIdRef = useRef<string | null>(null);
  const isAutoPlayingRef = useRef<boolean>(false); // 防止重复播放
  const autoPlayingAudioRef = useRef<HTMLAudioElement | null>(null); // 当前自动播放的音频对象
  const [autoPlayingMessageId, setAutoPlayingMessageId] = React.useState<string | null>(null); // 当前正在自动播放的消息ID
  
  // 语音输入模式状态（仅在小屏幕下可用）
  const [isVoiceInputMode, setIsVoiceInputMode] = useState(false);
  const { isRecording, isTranscribing, startRecording, stopRecording, transcribe } = useVoiceRecorder();
  
  // 语音通话Hook
  const {
    isCalling,
    error: voiceCallError,
    userFrequencyData,
    assistantFrequencyData,
    startCall,
    endCall,
  } = useVoiceAgent(
    currentSessionId || undefined,
    personalityId,
    {
      // 用户语音转文本回调
      onUserTranscript: (text: string) => {
        if (text.trim()) {
          const message: Message = {
            id: `voice-user-${Date.now()}`,
            role: 'user',
            content: text,
            timestamp: new Date(),
            session_id: currentSessionId || undefined,
            user_id: userId || undefined,
          };
          addVoiceCallMessage(message);
        }
      },
      // 助手回复文本回调
      onAssistantTranscript: (text: string) => {
        if (text.trim()) {
          const message: Message = {
            id: `voice-assistant-${Date.now()}`,
            role: 'assistant',
            content: text,
            timestamp: new Date(),
            session_id: currentSessionId || undefined,
            user_id: userId || undefined,
          };
          addVoiceCallMessage(message);
        }
      },
    }
  );
  
  // 跟踪用户是否已经有过交互（发送过消息）
  const hasUserInteractedRef = useRef(false);
  
  // 获取用户偏好（用于自动播放语音）
  const { data: preferences } = useQuery({
    queryKey: ['user', 'preferences'],
    queryFn: () => userApi.getCurrentUserPreferences(),
  });
  
  // 使用动态的 sessionId 创建 sendStreamMessage
  const { sendStreamMessage, isStreaming } = useStreamChat(currentSessionId || '', personalityId);

  // 从 React Query 获取消息（自动按 sessionId 隔离）
  // 直接使用 sessionId prop，确保切换时立即查询
  const { data: messages = [], isLoading: isLoadingHistory, refetch: refetchMessages } = useQuery({
    queryKey: ['chat', 'messages', currentSessionId],
    queryFn: async () => {
      if (!currentSessionId || currentSessionId === 'default') {
        return [];
      }
      try {
        console.log('Loading messages for session:', currentSessionId);
        const response = await chatApi.getHistory(currentSessionId);
        // 确保 response 是数组
        const responseArray = Array.isArray(response) ? response : [];
        console.log('Loaded messages:', responseArray.length, 'for session:', currentSessionId);
        return responseArray;
      } catch (error) {
        console.error('Failed to load messages for session:', currentSessionId, error);
        showError(error, '加载历史消息失败');
        return [];
      }
    },
    enabled: !!currentSessionId && currentSessionId !== 'default',
    staleTime: 0, // 设置为0，确保每次组件挂载时都重新查询（解决刷新页面后消息丢失的问题）
    gcTime: 10 * 60 * 1000, // 10分钟（缓存保留时间，原 cacheTime）
    refetchOnMount: 'always', // 组件挂载时总是重新查询（确保刷新页面后能获取最新数据）
    refetchOnWindowFocus: false, // 窗口聚焦时不重新查询（避免不必要的请求）
  });
  
  // 当 currentSessionId 变化时，显式触发重新查询（确保切换会话时能获取最新数据）
  // 使用 useRef 避免重复查询
  const lastSessionIdRef = useRef<string | null>(null);
  useEffect(() => {
    if (currentSessionId && currentSessionId !== 'default' && currentSessionId !== lastSessionIdRef.current) {
      console.log('Session ID changed, refetching messages:', currentSessionId);
      lastSessionIdRef.current = currentSessionId;
      refetchMessages();
    }
  }, [currentSessionId, refetchMessages]);
  
  // 合并加载状态
  const isLoading = isLoadingStore || isLoadingHistory;
  
  // 合并普通消息和语音通话消息
  const allMessages = React.useMemo(() => {
    const normalMessages = messages || [];
    const voiceMessages = isVoiceCallActive ? voiceCallMessages : [];
    // 合并并排序（按时间戳）
    const combined = [...normalMessages, ...voiceMessages];
    return combined.sort((a, b) => {
      const timeA = typeof a.timestamp === 'string' ? new Date(a.timestamp).getTime() : 
                     typeof a.timestamp === 'number' ? a.timestamp : 
                     a.timestamp instanceof Date ? a.timestamp.getTime() : 0;
      const timeB = typeof b.timestamp === 'string' ? new Date(b.timestamp).getTime() : 
                     typeof b.timestamp === 'number' ? b.timestamp : 
                     b.timestamp instanceof Date ? b.timestamp.getTime() : 0;
      return timeA - timeB;
    });
  }, [messages, voiceCallMessages, isVoiceCallActive]);

  // 显示错误提示
  useEffect(() => {
    if (error) {
      showError(error);
      setError(null);
    }
  }, [error, setError]);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [allMessages]);

  // 自动播放语音（当收到新的助手消息时）
  // 注意：只在用户发送消息后才自动播放，避免页面加载时触发
  useEffect(() => {
    // 检查是否启用了自动播放
    if (!preferences?.auto_tts) {
      return;
    }

    // 如果用户还没有交互过（发送过消息），不自动播放
    if (!hasUserInteractedRef.current) {
      return;
    }

    // 如果还在流式传输中，等待完成
    if (isStreaming || isLoading) {
      return;
    }

    // 找到最新的助手消息
    const assistantMessages = messages.filter(
      (msg) => msg.role === 'assistant' && msg.content
    );
    if (assistantMessages.length === 0) {
      return;
    }

    // 获取最新的助手消息
    const latestMessage = assistantMessages[assistantMessages.length - 1];
    
    // 如果这条消息已经自动播放过，跳过
    if (lastAutoPlayedMessageIdRef.current === latestMessage.id) {
      return;
    }

    // 如果正在播放，跳过（防止重复播放）
    if (isAutoPlayingRef.current) {
      return;
    }

    // 检查消息内容是否完整（不是空字符串）
    const content = typeof latestMessage.content === 'string'
      ? latestMessage.content
      : (latestMessage.content as any)?.text || '';
    
    if (!content.trim() || content.length < 3) {
      // 内容太短，可能是占位符，跳过
      return;
    }

    // 延迟一小段时间，确保消息已经完全更新
    const timer = setTimeout(() => {
      // 再次检查是否还在流式传输中或加载中
      const currentState = useChatStore.getState();
      if (currentState.isLoading || isStreaming) {
        return;
      }

      // 再次检查消息ID，防止在延迟期间消息已变化
      // 从 React Query 缓存获取最新消息
      const cachedMessages = queryClient.getQueryData<Message[]>(['chat', 'messages', currentSessionId]) || [];
      const currentAssistantMessages = cachedMessages.filter(
        (msg) => msg.role === 'assistant' && msg.content
      );
      if (currentAssistantMessages.length === 0) {
        return;
      }
      const currentLatestMessage = currentAssistantMessages[currentAssistantMessages.length - 1];
      
      // 如果消息ID已变化或已播放过，跳过
      if (currentLatestMessage.id !== latestMessage.id || 
          lastAutoPlayedMessageIdRef.current === currentLatestMessage.id) {
        return;
      }

      // 如果正在播放，跳过
      if (isAutoPlayingRef.current) {
        return;
      }

      // 标记正在播放
      isAutoPlayingRef.current = true;
      lastAutoPlayedMessageIdRef.current = currentLatestMessage.id;
      setAutoPlayingMessageId(currentLatestMessage.id); // 设置正在播放的消息ID

      // 自动播放语音
      playTTS(content, personalityId).then((audio) => {
        if (audio) {
          autoPlayingAudioRef.current = audio; // 保存音频对象引用
          // 监听播放结束，重置播放状态
          audio.addEventListener('ended', () => {
            isAutoPlayingRef.current = false;
            setAutoPlayingMessageId(null); // 清除正在播放的消息ID
            autoPlayingAudioRef.current = null;
          });
          audio.addEventListener('error', () => {
            isAutoPlayingRef.current = false;
            setAutoPlayingMessageId(null); // 清除正在播放的消息ID
            autoPlayingAudioRef.current = null;
          });
        } else {
          isAutoPlayingRef.current = false;
          setAutoPlayingMessageId(null); // 清除正在播放的消息ID
        }
      }).catch((error) => {
        // 播放失败，重置状态
        isAutoPlayingRef.current = false;
        setAutoPlayingMessageId(null); // 清除正在播放的消息ID
        // 静默失败，不显示错误提示（因为是自动播放）
        // 浏览器可能阻止自动播放，这是正常的
        if (error.name !== 'NotAllowedError') {
          console.warn('自动播放语音失败:', error);
        }
      });
      
      // 延迟刷新会话列表，等待后端标题生成完成（标题生成是异步的，通常需要2-3秒）
      setTimeout(() => {
        if (userId) {
          queryClient.invalidateQueries({ queryKey: ['sessions', userId] });
        }
      }, 3000); // 延迟3秒，确保标题生成完成
    }, 1500); // 延迟1.5秒，确保消息完成

    return () => {
      clearTimeout(timer);
    };
  }, [messages, preferences?.auto_tts, personalityId, isStreaming, isLoading]);

  // 同步 currentSessionId 到 Zustand，并重置自动播放状态
  useEffect(() => {
    // 更新 Zustand 中的 currentSessionId
    const actualSessionId = sessionId === 'default' ? null : sessionId;
    setCurrentSessionId(actualSessionId);
    
    // 重置自动播放相关状态（切换会话时）
    hasUserInteractedRef.current = false;
    isAutoPlayingRef.current = false;
    lastAutoPlayedMessageIdRef.current = null;
    setAutoPlayingMessageId(null);
  }, [sessionId, setCurrentSessionId]);

  /**
   * 处理发送消息
   */
  const handleSend = useCallback(async () => {
    if (!inputValue.trim() || isLoading || isStreaming) return;

    // 标记用户已经交互过（发送了消息）
    hasUserInteractedRef.current = true;

    let actualSessionId: string | undefined = currentSessionId;

    // 如果没有有效会话（sessionId 为 'default' 或会话列表为空），自动创建新会话
    if (!actualSessionId || actualSessionId === 'default' || sessions.length === 0) {
      try {
        const newSession = await createSession({
          title: '新会话', // 使用默认标题
          personality_id: personalityId,
        });
        actualSessionId = newSession.id || newSession.session_id;
        if (!actualSessionId) {
          showError(new Error('创建会话失败：未返回会话ID'), '创建会话失败');
          return;
        }
        // 移除消息缓存，然后显式触发重新查询（确保获取到欢迎消息）
        queryClient.removeQueries({ queryKey: ['chat', 'messages', actualSessionId] });
        setCurrentSessionId(actualSessionId);
        
        // 显式触发消息查询（确保欢迎消息能够显示）
        await queryClient.refetchQueries({ 
          queryKey: ['chat', 'messages', actualSessionId],
          exact: true 
        });
        
        // 更新 URL
        if (window.history && window.history.replaceState) {
          window.history.replaceState(null, '', `/chat/${actualSessionId}`);
        }
        // 重置自动播放相关状态
        hasUserInteractedRef.current = false;
        isAutoPlayingRef.current = false;
        lastAutoPlayedMessageIdRef.current = null;
        setAutoPlayingMessageId(null);
      } catch (error) {
        showError(error, '创建会话失败');
        return;
      }
    }
    
    // 确保 actualSessionId 不为 undefined
    if (!actualSessionId) {
      showError(new Error('会话ID不存在'), '发送消息失败');
      return;
    }

    const content = inputValue.trim();
    setInputValue('');
    
    // 如果会话ID已更改，更新 Zustand 中的 currentSessionId
    if (actualSessionId !== currentSessionId) {
      setCurrentSessionId(actualSessionId);
      // 更新 URL（如果不同）
      if (window.history && window.history.replaceState && actualSessionId) {
        window.history.replaceState(null, '', `/chat/${actualSessionId}`);
      }
    }
    
    // 使用 sendStreamMessage 发送消息
    await sendStreamMessage(content);
    
    // 聚焦输入框
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  }, [inputValue, isLoading, isStreaming, sendStreamMessage, currentSessionId, sessions, createSession, personalityId, setCurrentSessionId, queryClient]);

  /**
   * 处理键盘事件
   */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );


  /**
   * 处理删除消息
   */
  const handleDeleteMessage = useCallback(
    async (messageId: string) => {
      // 从 React Query 缓存获取消息，保存被删除的消息以便恢复
      const currentMessages = queryClient.getQueryData<Message[]>(['chat', 'messages', currentSessionId]) || [];
      const deletedMessage = currentMessages.find((msg) => msg.id === messageId);
      
      // 先更新UI（从 React Query 缓存移除）
      queryClient.setQueryData(
        ['chat', 'messages', currentSessionId],
        (old: Message[] = []) => old.filter((msg) => msg.id !== messageId)
      );

      // 调用API删除后端消息
      if (currentSessionId && currentSessionId !== 'default') {
        try {
          await chatApi.deleteMessage(currentSessionId, messageId);
        } catch (error) {
          // 如果删除失败，恢复消息到 React Query 缓存
          if (deletedMessage) {
            queryClient.setQueryData(
              ['chat', 'messages', currentSessionId],
              (old: Message[] = []) => [...old, deletedMessage]
            );
          }
          showError(error, '删除消息失败');
        }
      }
    },
    [currentSessionId, queryClient]
  );


  return (
    <div
      style={{
        height: '100%',
        width: '100%',
        maxWidth: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'var(--bg-primary)',
        overflow: 'hidden',
        transition: 'background-color 0.3s ease',
      }}
    >
      {/* 语音通话指示器 */}
      {isVoiceCallActive && (
        <VoiceCallIndicator
          sessionId={currentSessionId || undefined}
          personalityId={personalityId}
          userFrequencyData={userFrequencyData}
          assistantFrequencyData={assistantFrequencyData}
          onEndCall={async () => {
            // 结束通话逻辑
            try {
              // 结束通话
              await endCall();
              
              // 保存语音通话消息到数据库
              if (voiceCallMessages.length > 0 && currentSessionId) {
                try {
                  await chatApi.saveVoiceCallMessages(
                    currentSessionId,
                    voiceCallMessages.map((msg) => ({
                      role: msg.role as 'user' | 'assistant',
                      content: typeof msg.content === 'string' ? msg.content : (msg.content as any)?.text || '',
                      timestamp: typeof msg.timestamp === 'string' 
                        ? msg.timestamp 
                        : msg.timestamp instanceof Date 
                          ? msg.timestamp.toISOString()
                          : new Date(msg.timestamp).toISOString(),
                    }))
                  );
                  console.log('语音通话消息已保存到数据库');
                } catch (error) {
                  console.error('保存语音通话消息失败:', error);
                  showError(error, '保存语音通话消息失败');
                }
              }
              
              // 清空状态
              clearVoiceCallMessages();
              endVoiceCall();
            } catch (error) {
              console.error('结束通话失败:', error);
              showError(error, '结束通话失败');
            }
          }}
        />
      )}
      
      {/* 消息列表 */}
      <div
        style={{
          flex: 1,
          minHeight: 0, // 关键：允许 flex 子元素缩小
          overflowY: 'auto',
          overflowX: 'hidden',
          padding: isMobile ? '12px' : '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          background:
            chatBackgroundStyle === 'gradient'
              ? 'var(--chat-bg-gradient)'
              : 'var(--bg-primary)',
          transition: 'background 0.3s ease',
          width: '100%',
          maxWidth: '100%',
          boxSizing: 'border-box',
        }}
        className="chat-messages-container"
      >
        {isLoadingHistory ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" />
          </div>
        ) : allMessages.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              padding: '40px',
              color: 'var(--text-tertiary)',
            }}
          >
            开始对话吧！
          </div>
        ) : (
          <>
            {allMessages.map((msg) => {
              // 判断是否为语音通话消息
              const isVoiceCallMsg = isVoiceCallActive && voiceCallMessages.some(vm => vm.id === msg.id);
              return (
                <MessageBubble
                  key={msg.id}
                  id={msg.id}
                  role={msg.role === 'user' || msg.role === 'assistant' ? msg.role : 'user'}
                  content={
                    typeof msg.content === 'string'
                      ? msg.content
                      : (msg.content as any)?.text || ''
                  }
                  timestamp={msg.timestamp}
                  onDelete={handleDeleteMessage}
                  personalityId={personalityId}
                  isAutoPlaying={autoPlayingMessageId === msg.id}
                  onStopAutoPlay={() => {
                    // 停止自动播放
                    if (autoPlayingAudioRef.current) {
                      autoPlayingAudioRef.current.pause();
                      autoPlayingAudioRef.current = null;
                    }
                    isAutoPlayingRef.current = false;
                    setAutoPlayingMessageId(null);
                  }}
                  isVoiceCall={isVoiceCallMsg}
                />
              );
            })}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* 输入区域 */}
      <div
        style={{
          borderTop: '1px solid var(--border-color)',
          padding: isMobile ? '8px 12px' : '12px 16px',
          backgroundColor: 'var(--bg-secondary)',
          transition: 'background-color 0.3s ease, border-color 0.3s ease',
          flexShrink: 0,
          width: '100%',
          maxWidth: '100%',
          boxSizing: 'border-box',
        }}
      >
        <div 
          style={{ 
            display: 'flex', 
            gap: '8px', 
            alignItems: 'flex-end',
            width: '100%',
            maxWidth: '100%',
            boxSizing: 'border-box',
          }}
        >
          {/* 语音输入切换按钮（小屏幕下总是显示，宽屏幕下根据用户偏好显示） */}
          {(isMobile || preferences?.always_show_voice_input) && (
            <button
              type="button"
              onClick={() => setIsVoiceInputMode(!isVoiceInputMode)}
              disabled={isLoading || isStreaming || isTranscribing}
              style={{
                flexShrink: 0,
                width: '36px',
                height: '36px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: 'none',
                borderRadius: '8px',
                backgroundColor: 'var(--primary-color)',
                cursor: (isLoading || isStreaming || isTranscribing) ? 'not-allowed' : 'pointer',
                color: 'white',
                transition: 'background-color 0.2s ease, opacity 0.2s ease',
                padding: 0,
                outline: 'none',
                opacity: (isLoading || isStreaming || isTranscribing) ? 0.5 : 1,
              }}
              onMouseEnter={(e) => {
                if (!isLoading && !isStreaming && !isTranscribing) {
                  e.currentTarget.style.backgroundColor = 'var(--primary-hover)';
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--primary-color)';
              }}
              title={isVoiceInputMode ? '切换到文本输入' : '切换到语音输入'}
            >
              {isVoiceInputMode ? (
                // 键盘图标（切换到文本输入）
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="white"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <rect x="2" y="4" width="20" height="16" rx="2" ry="2" />
                  <line x1="6" y1="8" x2="6" y2="8" />
                  <line x1="10" y1="8" x2="10" y2="8" />
                  <line x1="14" y1="8" x2="14" y2="8" />
                  <line x1="18" y1="8" x2="18" y2="8" />
                  <line x1="6" y1="12" x2="18" y2="12" />
                  <line x1="6" y1="16" x2="16" y2="16" />
                </svg>
              ) : (
                // 麦克风图标（切换到语音输入）
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="white"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="23" />
                  <line x1="8" y1="23" x2="16" y2="23" />
                </svg>
              )}
            </button>
          )}

          {/* 文本输入模式 */}
          {!isVoiceInputMode && (
            <TextArea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入消息... (Shift+Enter换行)"
              autoSize={{ minRows: 1, maxRows: 4 }}
              disabled={isLoading || isStreaming}
              style={{ 
                flex: 1,
                minWidth: 0,
                maxWidth: '100%',
                minHeight: '36px',
                height: '36px',
                lineHeight: '24px',
                paddingTop: '6px',
                paddingBottom: '6px',
                boxSizing: 'border-box',
              }}
            />
          )}

          {/* 语音输入模式 */}
          {isVoiceInputMode && (
            <TextArea
              ref={inputRef}
              value={isRecording ? '正在录音...' : isTranscribing ? '识别中...' : '点击说话'}
              readOnly
              onClick={async () => {
                if (isRecording) {
                  // 如果正在录音，停止并转录
                  stopRecording();
                  // 等待一小段时间确保录音数据已收集
                  setTimeout(async () => {
                    try {
                      const text = await transcribe({
                        personality_id: personalityId,
                        language: 'zh-CN',
                      });
                      console.log('STT识别结果:', text);
                      if (text && text.trim()) {
                        // 直接发送识别后的文本，不切换回文本输入模式
                        // 标记用户已经交互过（发送了消息）
                        hasUserInteractedRef.current = true;
                        // 直接调用 sendStreamMessage 发送
                        await sendStreamMessage(text.trim());
                        // 保持语音输入模式，方便继续语音输入
                        // setIsVoiceInputMode(false); // 不切换回文本输入模式
                      } else {
                        console.warn('STT返回空文本或无效文本:', text);
                        // 如果识别结果为空，保持语音输入模式，显示提示
                        showError(new Error('未识别到有效语音，请重试'), '识别失败');
                      }
                    } catch (error) {
                      console.error('STT转录错误:', error);
                      showError(error, '语音识别失败');
                    }
                  }, 100);
                } else if (!isTranscribing) {
                  // 如果未在录音且未在识别，开始录音
                  await startRecording();
                }
              }}
              disabled={isLoading || isStreaming || isTranscribing}
              style={{
                flex: 1,
                minWidth: 0,
                maxWidth: '100%',
                minHeight: '36px',
                height: '36px',
                lineHeight: '24px',
                paddingTop: '6px',
                paddingBottom: '6px',
                boxSizing: 'border-box',
                cursor: (isLoading || isStreaming || isTranscribing) ? 'not-allowed' : 'pointer',
                backgroundColor: isRecording 
                  ? 'var(--error-color)' 
                  : isTranscribing
                    ? 'var(--bg-tertiary)'
                    : 'var(--bg-primary)',
                color: isRecording 
                  ? 'var(--text-inverse)' 
                  : 'var(--text-primary)',
                borderColor: isRecording 
                  ? 'var(--error-color)' 
                  : 'var(--border-color)',
                textAlign: 'center',
              }}
              autoSize={{ minRows: 1, maxRows: 1 }}
            />
          )}

          {/* 发送按钮 */}
          <button
            type="button"
            onClick={handleSend}
            disabled={!inputValue.trim() || isLoading || isStreaming || isTranscribing}
            style={{
              flexShrink: 0,
              width: '36px',
              height: '36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: 'none',
              borderRadius: '8px',
              backgroundColor: (!inputValue.trim() || isLoading || isStreaming || isTranscribing)
                ? 'var(--text-tertiary)'
                : 'var(--primary-color)',
              cursor: (!inputValue.trim() || isLoading || isStreaming || isTranscribing)
                ? 'not-allowed'
                : 'pointer',
              color: 'white',
              transition: 'background-color 0.2s ease, opacity 0.2s ease',
              padding: 0,
              outline: 'none',
              opacity: (!inputValue.trim() || isLoading || isStreaming || isTranscribing) ? 0.5 : 1,
            }}
            onMouseEnter={(e) => {
              if (inputValue.trim() && !isLoading && !isStreaming && !isTranscribing) {
                e.currentTarget.style.backgroundColor = 'var(--primary-hover)';
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 
                (!inputValue.trim() || isLoading || isStreaming || isTranscribing)
                  ? 'var(--text-tertiary)'
                  : 'var(--primary-color)';
            }}
            title="发送"
          >
            {isLoading || isStreaming ? (
              <Spin size="small" style={{ color: 'white' }} />
            ) : (
              <SendOutlined style={{ fontSize: '18px', color: 'white' }} />
            )}
          </button>

          {/* 语音通话按钮 */}
          <button
            type="button"
            onClick={async () => {
              if (isVoiceCallActive) {
                // 如果正在通话，结束通话
                try {
                  await endCall();
                  
                  // 保存语音通话消息到数据库
                  if (voiceCallMessages.length > 0 && currentSessionId) {
                    try {
                      await chatApi.saveVoiceCallMessages(
                        currentSessionId,
                        voiceCallMessages.map((msg) => ({
                          role: msg.role as 'user' | 'assistant',
                          content: typeof msg.content === 'string' ? msg.content : (msg.content as any)?.text || '',
                          timestamp: typeof msg.timestamp === 'string' 
                            ? msg.timestamp 
                            : msg.timestamp instanceof Date 
                              ? msg.timestamp.toISOString()
                              : new Date(msg.timestamp).toISOString(),
                        }))
                      );
                      console.log('语音通话消息已保存到数据库');
                    } catch (error) {
                      console.error('保存语音通话消息失败:', error);
                      showError(error, '保存语音通话消息失败');
                    }
                  }
                  
                  clearVoiceCallMessages();
                  endVoiceCall();
                } catch (error) {
                  console.error('结束通话失败:', error);
                  showError(error, '结束通话失败');
                }
              } else {
                // 开始语音通话
                try {
                  // 启动语音通话状态
                  startVoiceCall();
                  
                  // 开始通话（内部会自动连接）
                  await startCall();
                } catch (error) {
                  console.error('开始语音通话失败:', error);
                  showError(error, '开始语音通话失败');
                  endVoiceCall();
                }
              }
            }}
            disabled={isLoading || isStreaming || isTranscribing}
            style={{
              flexShrink: 0,
              width: '36px',
              height: '36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: 'none',
              borderRadius: '8px',
              backgroundColor: isVoiceCallActive ? '#ff4d4f' : 'var(--primary-color)',
              cursor: (isLoading || isStreaming || isTranscribing) ? 'not-allowed' : 'pointer',
              color: 'white',
              transition: 'background-color 0.2s ease',
              padding: 0,
              outline: 'none',
              opacity: (isLoading || isStreaming || isTranscribing) ? 0.5 : 1,
            }}
            onMouseEnter={(e) => {
              if (!(isLoading || isStreaming || isTranscribing)) {
                e.currentTarget.style.backgroundColor = isVoiceCallActive ? '#ff7875' : 'var(--primary-hover)';
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = isVoiceCallActive ? '#ff4d4f' : 'var(--primary-color)';
            }}
            title={isVoiceCallActive ? '结束通话' : '语音通话'}
          >
            <PhoneOutlined style={{ fontSize: '18px', color: 'white', transform: 'rotate(-90deg)' }} />
          </button>
        </div>
      </div>
    </div>
  );
};

