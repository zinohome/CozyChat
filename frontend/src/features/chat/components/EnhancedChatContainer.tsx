import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Input, Button, Spin } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useChatStore } from '@/store/slices/chatSlice';
import { useStreamChat } from '../hooks/useStreamChat';
import { useSessions } from '../hooks/useSessions';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { useUIStore } from '@/store/slices/uiSlice';
import { chatApi } from '@/services/chat';
import { MessageBubble } from './MessageBubble';
import { showError } from '@/utils/errorHandler';
import { userApi } from '@/services/user';
import { playTTS } from '@/utils/tts';
import { useVoiceRecorder } from '@/hooks/useVoiceRecorder';
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
  const { messages: storeMessages, setMessages, isLoading, error, setError, removeMessage, setCurrentSessionId, addMessage, updateMessage, setLoading } = useChatStore();
  
  // 确保 messages 始终是数组
  const messages = Array.isArray(storeMessages) ? storeMessages : [];
  const { sessions, createSession } = useSessions();
  const queryClient = useQueryClient();
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<any>(null);
  const isMobile = useIsMobile();
  const [currentSessionId, setCurrentSessionIdLocal] = useState(sessionId);
  const { chatBackgroundStyle } = useUIStore();
  const lastAutoPlayedMessageIdRef = useRef<string | null>(null);
  const isAutoPlayingRef = useRef<boolean>(false); // 防止重复播放
  
  // 语音输入模式状态（仅在小屏幕下可用）
  const [isVoiceInputMode, setIsVoiceInputMode] = useState(false);
  const { isRecording, isTranscribing, startRecording, stopRecording, transcribe } = useVoiceRecorder();
  
  // 跟踪用户是否已经有过交互（发送过消息）
  const hasUserInteractedRef = useRef(false);
  
  // 获取用户偏好（用于自动播放语音）
  const { data: preferences } = useQuery({
    queryKey: ['user', 'preferences'],
    queryFn: () => userApi.getCurrentUserPreferences(),
  });
  
  // 使用动态的 sessionId 创建 sendStreamMessage
  const { sendStreamMessage, isStreaming } = useStreamChat(currentSessionId, personalityId);

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
  }, [messages]);

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
      const currentMessages = useChatStore.getState().messages;
      const currentAssistantMessages = currentMessages.filter(
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

      // 自动播放语音
      playTTS(content, personalityId).then((audio) => {
        if (audio) {
          // 监听播放结束，重置播放状态
          audio.addEventListener('ended', () => {
            isAutoPlayingRef.current = false;
          });
          audio.addEventListener('error', () => {
            isAutoPlayingRef.current = false;
          });
        } else {
          isAutoPlayingRef.current = false;
        }
      }).catch((error) => {
        // 播放失败，重置状态
        isAutoPlayingRef.current = false;
        // 静默失败，不显示错误提示（因为是自动播放）
        // 浏览器可能阻止自动播放，这是正常的
        if (error.name !== 'NotAllowedError') {
          console.warn('自动播放语音失败:', error);
        }
      });
    }, 1500); // 延迟1.5秒，确保消息完成

    return () => {
      clearTimeout(timer);
    };
  }, [messages, preferences?.auto_tts, personalityId, isStreaming, isLoading]);

  // 同步 currentSessionId 状态
  useEffect(() => {
    setCurrentSessionIdLocal(sessionId);
  }, [sessionId]);

  // 获取历史消息
  const { isLoading: isLoadingHistory } = useQuery({
    queryKey: ['chat', 'messages', currentSessionId],
    queryFn: async () => {
      if (!currentSessionId || currentSessionId === 'default') return [];
      try {
        const response = await chatApi.getHistory(currentSessionId);
        // 确保 response 是数组
        const responseArray = Array.isArray(response) ? response : [];
        // 使用 getState() 获取最新消息，避免依赖项导致的重建
        const currentMessages = useChatStore.getState().messages;
        const localMessages = currentMessages.filter(m => m.session_id === currentSessionId);
        if (localMessages.length > 0 && responseArray.length === 0) {
          // 如果后端返回空但本地有消息，保留本地消息
          return localMessages;
        }
        // 只在有实际变化时才更新
        if (responseArray.length > 0) {
        setMessages(responseArray);
        }
        return responseArray.length > 0 ? responseArray : localMessages;
      } catch (error) {
        // 如果查询失败，保留本地消息
        const currentMessages = useChatStore.getState().messages;
        const localMessages = currentMessages.filter(m => m.session_id === currentSessionId);
        if (localMessages.length > 0) {
          return localMessages;
        }
        showError(error, '加载历史消息失败');
        return [];
      }
    },
    enabled: !!currentSessionId && currentSessionId !== 'default',
    staleTime: 5 * 60 * 1000, // 5分钟
  });

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
        // 先清空当前消息，避免消息混乱
        setMessages([]);
        setCurrentSessionIdLocal(actualSessionId);
        setCurrentSessionId(actualSessionId);
        // 更新 URL
        if (window.history && window.history.replaceState) {
          window.history.replaceState(null, '', `/chat/${actualSessionId}`);
        }
        // 使查询失效，但不立即重新查询（避免覆盖即将添加的消息）
        queryClient.invalidateQueries({ queryKey: ['chat', 'messages', actualSessionId] });
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
    
    // 如果会话ID已更改，直接使用 chatApi 发送消息（因为不能在回调中调用 hook）
    if (actualSessionId !== currentSessionId) {
      // 直接调用流式聊天 API
      setLoading(true);
      setError(null);

      try {
        // 添加用户消息
        const userMessage: Message = {
          id: `user-${Date.now()}`,
          role: 'user',
          content,
          timestamp: new Date(),
          session_id: actualSessionId,
        };
        addMessage(userMessage);

        // 创建AI消息占位符
        const aiMessageId = `assistant-${Date.now()}`;
        const aiMessage: Message = {
          id: aiMessageId,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          session_id: actualSessionId,
        };
        addMessage(aiMessage);

        // 构建请求（不传model，让后端根据personality_id自动选择）
        const request = {
          messages: [{ role: 'user' as const, content }],
          personality_id: personalityId,
          session_id: actualSessionId,
          stream: true,
          use_memory: true,
        };

        // 处理流式响应
        let accumulatedContent = '';
        for await (const chunk of chatApi.streamChat(request)) {
          const deltaContent = chunk.choices?.[0]?.delta?.content || '';
          if (deltaContent) {
            accumulatedContent += deltaContent;
            updateMessage(aiMessageId, {
              content: accumulatedContent,
            });
          }

          if (chunk.choices?.[0]?.finish_reason) {
            break;
          }
        }

        // 更新最终消息时间戳
        updateMessage(aiMessageId, {
          timestamp: new Date(),
        });

        // 更新React Query缓存，确保用户消息和AI消息都在缓存中
        queryClient.setQueryData(
          ['chat', 'messages', actualSessionId],
          (old: Message[] = []) => {
            // 检查是否已有用户消息
            const hasUserMessage = old.some((msg) => msg.id === userMessage.id);
            // 检查是否已有AI消息
            const hasAiMessage = old.some((msg) => msg.id === aiMessageId);
            
            let updated = [...old];
            
            // 添加用户消息（如果不存在）
            if (!hasUserMessage) {
              updated.push(userMessage);
            }
            
            // 更新或添加AI消息
            if (hasAiMessage) {
              updated = updated.map((msg) => 
                msg.id === aiMessageId 
                  ? { ...msg, content: accumulatedContent, timestamp: new Date() }
                  : msg
              );
            } else {
              updated.push({
                ...aiMessage,
                content: accumulatedContent,
                timestamp: new Date(),
              });
            }
            
            return updated;
          }
        );
        
        // 使用 getState() 获取最新消息，避免依赖项导致的重建
        const currentMessages = useChatStore.getState().messages;
        const hasUserMessage = currentMessages.some((msg) => msg.id === userMessage.id);
        const hasAiMessage = currentMessages.some((msg) => msg.id === aiMessageId);
        
        let updated = [...currentMessages];
        
        if (!hasUserMessage) {
          updated.push(userMessage);
        }
        
        if (hasAiMessage) {
          updated = updated.map((msg) => 
            msg.id === aiMessageId 
              ? { ...msg, content: accumulatedContent, timestamp: new Date() }
              : msg
          );
        } else {
          updated.push({
            ...aiMessage,
            content: accumulatedContent,
            timestamp: new Date(),
          });
        }
        
        setMessages(updated);
        
        // 标记用户已经交互过（发送了消息）
        hasUserInteractedRef.current = true;
        
        // 触发自动播放（如果启用）
        // 使用 setTimeout 确保消息状态已更新
        setTimeout(() => {
          const prefs = queryClient.getQueryData<UserPreferences>(['user', 'preferences']);
          if (prefs?.auto_tts) {
            playTTS(accumulatedContent, personalityId).catch((error) => {
              // 静默失败，浏览器可能阻止自动播放
              if (error.name !== 'NotAllowedError') {
                console.warn('自动播放语音失败:', error);
              }
            });
          }
        }, 500);

        setLoading(false);
      } catch (error: any) {
        setError(error.message || '发送消息失败');
        setLoading(false);
        showError(error, '发送消息失败');
      }
    } else {
      await sendStreamMessage(content);
    }
    
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
      // 使用 getState() 获取最新消息，保存被删除的消息以便恢复
      const currentMessages = useChatStore.getState().messages;
      const deletedMessage = currentMessages.find((msg) => msg.id === messageId);
      
      // 先更新UI
      removeMessage(messageId);

      // 调用API删除后端消息
      if (sessionId && sessionId !== 'default') {
        try {
          await chatApi.deleteMessage(sessionId, messageId);
        } catch (error) {
          // 如果删除失败，恢复消息
          if (deletedMessage) {
            const currentMessagesAfterDelete = useChatStore.getState().messages;
            setMessages([...currentMessagesAfterDelete, deletedMessage]);
          }
          showError(error, '删除消息失败');
        }
      }
    },
    [removeMessage, sessionId, setMessages]
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
        ) : messages.length === 0 ? (
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
            {messages.map((msg) => (
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
              />
            ))}
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
          {/* 语音输入切换按钮（仅在小屏幕下显示） */}
          {isMobile && (
            <button
              type="button"
              onClick={() => setIsVoiceInputMode(!isVoiceInputMode)}
              disabled={isLoading || isStreaming || isTranscribing}
              style={{
                flexShrink: 0,
                width: '32px',
                height: '32px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: 'none',
                background: 'transparent',
                cursor: (isLoading || isStreaming || isTranscribing) ? 'not-allowed' : 'pointer',
                color: isVoiceInputMode ? 'var(--primary-color)' : 'var(--text-secondary)',
                transition: 'color 0.2s ease',
                padding: 0,
                outline: 'none',
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
                  stroke="currentColor"
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
                  stroke="currentColor"
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
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={isLoading || isStreaming}
            disabled={!inputValue.trim() || isLoading || isStreaming || isTranscribing}
          >
            发送
          </Button>
        </div>
      </div>
    </div>
  );
};

