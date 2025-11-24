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
import { sessionApi } from '@/services/session';
import { MessageBubble } from './MessageBubble';
import { VirtualizedMessageList } from './VirtualizedMessageList';
import { VoiceCallIndicator, VoiceWaveform } from './VoiceCallIndicator';
import { ChatSessionHeader } from './ChatSessionHeader';
import { ChatToolbar } from './ChatToolbar';
import { showError } from '@/utils/errorHandler';
import { userApi } from '@/services/user';
import { playTTS } from '@/utils/tts';
import { useVoiceRecorder } from '@/hooks/useVoiceRecorder';
import { useVoiceAgent } from '@/hooks/useVoiceAgent';
import type { Message } from '@/types/chat';
import { logger } from '@/utils/logger';

const log = logger.withTag('EnhancedChatContainer');

// 标题生成触发阈值（从环境变量读取，默认为10）
const TITLE_TRIGGER_LENGTH = parseInt(import.meta.env.VITE_SESSION_TITLE_TRIGGER_LENGTH || '10', 10);

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
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<any>(null);
  const isMobile = useIsMobile();
  const [messagesContainerHeight, setMessagesContainerHeight] = React.useState(600);
  // 使用 sessionId prop 作为当前会话ID（确保切换时立即更新）
  const currentSessionId = sessionId === 'default' ? null : sessionId;
  const { chatBackgroundStyle } = useUIStore();
  const lastAutoPlayedMessageIdRef = useRef<string | null>(null);
  const isAutoPlayingRef = useRef<boolean>(false); // 防止重复播放
  const autoPlayingAudioRef = useRef<HTMLAudioElement | null>(null); // 当前自动播放的音频对象
  const [autoPlayingMessageId, setAutoPlayingMessageId] = React.useState<string | null>(null); // 当前正在自动播放的消息ID
  
  // 语音输入模式状态（仅在小屏幕下可用）
  const [isVoiceInputMode, setIsVoiceInputMode] = useState(false);
  const { isRecording, isTranscribing, recordingDuration, startRecording, stopRecording, transcribe } = useVoiceRecorder();
  
  // 按住说话相关状态
  const [isPressing, setIsPressing] = useState(false); // 是否正在按下
  const isPressingRef = useRef(false); // 防止重复触发
  const recordingStartTimeRef = useRef<number | null>(null); // 录音开始时间（用于计算时长）
  const MIN_RECORDING_DURATION = 300; // 最小录音时长（毫秒），防止误触
  
  // 语音通话Hook
  const {
    isCalling,
    isConnecting,
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
          // 使用更唯一的ID生成方式：timestamp + random + content hash
          const timestamp = Date.now();
          const random = Math.random().toString(36).substring(2, 9);
          const textHash = text.slice(0, 15).replace(/\s/g, '_');
          const message: Message = {
            id: `voice-user-${timestamp}-${random}-${textHash}`,
            role: 'user',
            content: text,
            timestamp: new Date(),
            session_id: currentSessionId || undefined,
            user_id: userId || undefined,
            // 添加语音通话标记到 metadata
            metadata: {
              is_voice_call: true,
            },
          };
          addVoiceCallMessage(message);
        }
      },
      // 助手回复文本回调
      onAssistantTranscript: (text: string) => {
        if (text.trim()) {
          // 使用更唯一的ID生成方式：timestamp + random + content hash
          const timestamp = Date.now();
          const random = Math.random().toString(36).substring(2, 9);
          const textHash = text.slice(0, 15).replace(/\s/g, '_');
          const message: Message = {
            id: `voice-assistant-${timestamp}-${random}-${textHash}`,
            role: 'assistant',
            content: text,
            timestamp: new Date(),
            session_id: currentSessionId || undefined,
            user_id: userId || undefined,
            // 添加语音通话标记到 metadata
            metadata: {
              is_voice_call: true,
            },
          };
          addVoiceCallMessage(message);
        }
      },
    }
  );
  
  // 跟踪用户是否已经有过交互（发送过消息）
  const hasUserInteractedRef = useRef(false);
  
  // 获取用户偏好（用于自动播放语音和传递给子组件）
  const { data: preferences } = useQuery({
    queryKey: ['user', 'preferences'],
    queryFn: () => userApi.getCurrentUserPreferences(),
    staleTime: 5 * 60 * 1000, // 5分钟内认为数据是新鲜的
    gcTime: 10 * 60 * 1000, // 10分钟内保留缓存（原 cacheTime，React Query v5 已重命名）
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
        log.debug('Loading messages for session:', currentSessionId);
        const response = await chatApi.getHistory(currentSessionId);
        // 确保 response 是数组
        const responseArray = Array.isArray(response) ? response : [];
        log.debug('Loaded messages:', responseArray.length, 'for session:', currentSessionId);
        return responseArray;
      } catch (error) {
        log.error('Failed to load messages for session:', currentSessionId, error);
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
      log.debug('Session ID changed, refetching messages:', currentSessionId);
      lastSessionIdRef.current = currentSessionId;
      // 安全检查：确保refetchMessages是函数
      if (typeof refetchMessages === 'function') {
      refetchMessages();
      }
    }
  }, [currentSessionId, refetchMessages]);

  // 标题生成触发逻辑
  const titleGeneratedRef = useRef<Set<string>>(new Set()); // 记录已生成标题的会话ID
  useEffect(() => {
    // 检查是否需要触发标题生成
    const shouldGenerateTitle = async () => {
      // 必须有有效的会话ID
      if (!currentSessionId || currentSessionId === 'default') {
        return;
      }
      
      // 如果已经为这个会话生成过标题，不再重复触发
      if (titleGeneratedRef.current.has(currentSessionId)) {
        return;
      }
      
      // 检查消息数量是否达到阈值
      const messageCount = messages.length;
      if (messageCount >= TITLE_TRIGGER_LENGTH) {
        try {
          log.debug('Triggering title generation for session:', currentSessionId, 'with', messageCount, 'messages');
          
          // 调用标题生成API
          await sessionApi.generateTitle(currentSessionId);
          
          // 标记为已生成
          titleGeneratedRef.current.add(currentSessionId);
          
          // 刷新会话列表以显示新标题（使用正确的queryKey，包含userId）
          // 使用 refetchQueries 立即刷新，而不是 invalidateQueries（可能因为 staleTime 不会立即刷新）
          if (userId) {
            await queryClient.refetchQueries({ queryKey: ['sessions', userId] });
          } else {
            // 如果没有userId，使用通配符匹配所有sessions查询
            await queryClient.refetchQueries({ queryKey: ['sessions'] });
          }
          
          log.info('Session title generated successfully:', currentSessionId);
        } catch (error: any) {
          // 如果是400错误（消息数不足或已有标题），静默处理，不记录为错误
          if (error?.response?.status === 400) {
            const errorDetail = error?.response?.data?.detail || error.message;
            log.debug('Title generation skipped:', errorDetail);
            // 如果是消息数不足，标记为已处理，避免重复尝试
            if (errorDetail?.includes('below trigger threshold')) {
              titleGeneratedRef.current.add(currentSessionId);
            }
          } else {
            // 其他错误才记录为错误
            log.error('Failed to generate session title:', error);
          }
        }
      }
    };
    
    shouldGenerateTitle();
  }, [currentSessionId, messages.length, queryClient, userId]);
  
  // 合并加载状态
  const isLoading = isLoadingStore || isLoadingHistory;
  
  // 合并普通消息和语音通话消息（去重）
  const allMessages = React.useMemo(() => {
    const normalMessages = messages || [];
    const voiceMessages = isVoiceCallActive ? voiceCallMessages : [];
    
    // 使用 Map 去重，以消息 ID 为 key，保留最新的消息
    const messageMap = new Map<string, Message>();
    
    // 先添加普通消息
    normalMessages.forEach(msg => {
      messageMap.set(msg.id, msg);
    });
    
    // 再添加语音通话消息（如果 ID 已存在，会被覆盖，但语音通话消息通常更新）
    voiceMessages.forEach(msg => {
      messageMap.set(msg.id, msg);
    });
    
    // 转换为数组并排序（按时间戳）
    const combined = Array.from(messageMap.values());
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

  // 计算消息容器高度（用于虚拟滚动）
  useEffect(() => {
    const updateHeight = () => {
      if (messagesContainerRef.current) {
        const rect = messagesContainerRef.current.getBoundingClientRect();
        setMessagesContainerHeight(rect.height);
      }
    };
    
    updateHeight();
    window.addEventListener('resize', updateHeight);
    return () => window.removeEventListener('resize', updateHeight);
  }, []);
  
  // 停止自动播放回调（使用 useCallback 优化）
  const handleStopAutoPlay = useCallback(() => {
    if (autoPlayingAudioRef.current) {
      autoPlayingAudioRef.current.pause();
      autoPlayingAudioRef.current = null;
    }
    isAutoPlayingRef.current = false;
    setAutoPlayingMessageId(null);
  }, []);

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
          log.warn('自动播放语音失败:', error);
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

    let actualSessionId: string | undefined = currentSessionId ?? undefined;

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
   * 处理按住说话 - 按下开始
   */
  const handlePressStart = useCallback(async (e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    // 防止重复触发
    if (isPressingRef.current || isTranscribing || isLoading || isStreaming) {
      return;
    }
    
    isPressingRef.current = true;
    setIsPressing(true);
    recordingStartTimeRef.current = Date.now();
    
    try {
      await startRecording();
    } catch (error) {
      log.error('开始录音失败:', error);
      isPressingRef.current = false;
      setIsPressing(false);
      recordingStartTimeRef.current = null;
    }
  }, [isTranscribing, isLoading, isStreaming, startRecording]);

  /**
   * 处理按住说话 - 释放结束
   */
  const handlePressEnd = useCallback(async (e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!isPressingRef.current || !isRecording) {
      return;
    }
    
    isPressingRef.current = false;
    setIsPressing(false);
    
    // 检查最小录音时长
    const duration = recordingStartTimeRef.current 
      ? Date.now() - recordingStartTimeRef.current 
      : 0;
    
    if (duration < MIN_RECORDING_DURATION) {
      log.debug('录音时长太短，取消发送:', duration, 'ms');
      stopRecording();
      recordingStartTimeRef.current = null;
      showError(new Error('录音时间太短'), '录音失败');
      return;
    }
    
    // 停止录音
    stopRecording();
    recordingStartTimeRef.current = null;
    
    // 等待一小段时间确保录音数据已收集
    setTimeout(async () => {
      try {
        const text = await transcribe({
          personality_id: personalityId,
          language: 'zh-CN',
        });
        log.debug('STT识别结果:', text);
        if (text && text.trim()) {
          // 标记用户已经交互过（发送了消息）
          hasUserInteractedRef.current = true;
          // 直接调用 sendStreamMessage 发送
          await sendStreamMessage(text.trim());
        } else {
          log.warn('STT返回空文本或无效文本:', text);
          showError(new Error('未识别到有效语音，请重试'), '识别失败');
        }
      } catch (error) {
        log.error('STT转录错误:', error);
        showError(error, '语音识别失败');
      }
    }, 100);
  }, [isRecording, stopRecording, transcribe, personalityId, sendStreamMessage]);

  /**
   * 处理按住说话 - 取消（拖拽离开或失去焦点）
   */
  const handlePressCancel = useCallback(() => {
    if (isPressingRef.current && isRecording) {
      log.debug('取消录音');
      isPressingRef.current = false;
      setIsPressing(false);
      stopRecording();
      recordingStartTimeRef.current = null;
    }
  }, [isRecording, stopRecording]);

  /**
   * 处理点击说话（桌面端模式）
   */
  const handleClickToRecord = useCallback(async () => {
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
          log.debug('STT识别结果:', text);
          if (text && text.trim()) {
            // 直接发送识别后的文本，不切换回文本输入模式
            // 标记用户已经交互过（发送了消息）
            hasUserInteractedRef.current = true;
            // 直接调用 sendStreamMessage 发送
            await sendStreamMessage(text.trim());
            // 保持语音输入模式，方便继续语音输入
            // setIsVoiceInputMode(false); // 不切换回文本输入模式
          } else {
            log.warn('STT返回空文本或无效文本:', text);
            // 如果识别结果为空，保持语音输入模式，显示提示
            showError(new Error('未识别到有效语音，请重试'), '识别失败');
          }
        } catch (error) {
          log.error('STT转录错误:', error);
          showError(error, '语音识别失败');
        }
      }, 100);
    } else if (!isTranscribing) {
      // 如果未在录音且未在识别，开始录音
      await startRecording();
    }
  }, [isRecording, isTranscribing, stopRecording, startRecording, transcribe, personalityId, sendStreamMessage]);

  // 根据用户偏好和设备类型选择交互模式
  const getVoiceInputMode = useCallback((): 'press' | 'click' => {
    // 1. 优先使用用户偏好
    const userPreference = preferences?.voice_input_mode;
    
    if (userPreference === 'press') {
      return 'press';
    }
    if (userPreference === 'click') {
      return 'click';
    }
    
    // 2. 自动模式或未设置：根据设备类型
    // 'auto' 或 undefined/null 都使用自动模式
    return isMobile ? 'press' : 'click';
  }, [preferences?.voice_input_mode, isMobile]);
  
  const usePressMode = getVoiceInputMode() === 'press';

  // 处理页面失去焦点时取消录音
  useEffect(() => {
    const handleBlur = () => {
      if (isPressingRef.current && isRecording) {
        log.debug('页面失去焦点，取消录音');
        handlePressCancel();
      }
    };
    
    window.addEventListener('blur', handleBlur);
    return () => {
      window.removeEventListener('blur', handleBlur);
    };
  }, [isRecording, handlePressCancel]);


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
        background:
          chatBackgroundStyle === 'gradient'
            ? 'var(--chat-bg-gradient)'
            : 'var(--bg-primary)',
        overflow: 'hidden',
        transition: 'background 0.3s ease',
      }}
    >

      {/* 语音通话指示器 */}
      {isVoiceCallActive && (
        <VoiceCallIndicator
          userFrequencyData={userFrequencyData}
          assistantFrequencyData={assistantFrequencyData}
        />
      )}

      {/* 会话管理头部（移动端显示） */}
      {isMobile && (
        <ChatSessionHeader
          currentSessionId={currentSessionId || undefined}
          personalityId={personalityId}
        />
      )}
      
      {/* 消息列表 */}
      <div
        ref={messagesContainerRef}
        style={{
          flex: 1,
          minHeight: 0, // 关键：允许 flex 子元素缩小
          overflow: 'hidden', // 虚拟滚动组件内部处理滚动
          padding: isMobile ? '12px' : '16px',
          display: 'flex',
          flexDirection: 'column',
          background: 'transparent', // 继承父容器的渐变背景
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
          <VirtualizedMessageList
            messages={allMessages}
            isVoiceCallActive={isVoiceCallActive}
            voiceCallMessages={voiceCallMessages}
            onDeleteMessage={handleDeleteMessage}
            personalityId={personalityId}
            autoPlayingMessageId={autoPlayingMessageId}
            onStopAutoPlay={handleStopAutoPlay}
            preferences={preferences}
            height={Math.max(messagesContainerHeight, 400)} // 确保最小高度400px
            estimateItemSize={(index) => {
              // 根据消息内容估算高度
              if (!allMessages || index >= allMessages.length || index < 0) {
                return 100; // 默认高度
              }
              const msg = allMessages[index];
              if (!msg) {
                return 100; // 默认高度
              }
              const content = typeof msg.content === 'string'
                ? msg.content
                : (msg.content as any)?.text || '';
              // 基础高度 + 内容行数 * 行高
              const baseHeight = 80;
              const lineHeight = 24;
              const lines = Math.ceil(content.length / 50); // 假设每行50个字符
              return Math.max(baseHeight + lines * lineHeight, 60); // 最小高度60px
            }}
          />
        )}
      </div>

      {/* 工具栏 */}
      <ChatToolbar isMobile={isMobile} />

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
          {!isVoiceCallActive && !isConnecting && (isMobile || preferences?.always_show_voice_input) && (
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
          {!isVoiceCallActive && !isConnecting && !isVoiceInputMode && (
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
          {!isVoiceCallActive && !isConnecting && isVoiceInputMode && (
            <TextArea
              ref={inputRef}
              value={
                isRecording 
                  ? `正在录音... ${recordingDuration > 0 ? `${recordingDuration}秒` : ''}`.trim()
                  : isTranscribing 
                    ? '识别中...' 
                    : usePressMode 
                      ? '按住说话' 
                      : '点击说话'
              }
              readOnly
              onClick={usePressMode ? undefined : handleClickToRecord}
              onMouseDown={usePressMode ? handlePressStart : undefined}
              onMouseUp={usePressMode ? handlePressEnd : undefined}
              onMouseLeave={usePressMode ? handlePressCancel : undefined}
              onTouchStart={usePressMode ? handlePressStart : undefined}
              onTouchEnd={usePressMode ? handlePressEnd : undefined}
              onTouchCancel={usePressMode ? handlePressCancel : undefined}
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
                userSelect: 'none', // 防止文本选择
                WebkitUserSelect: 'none',
                backgroundColor: isPressing || isRecording 
                  ? 'var(--error-color)' 
                  : isTranscribing
                    ? 'var(--bg-tertiary)'
                    : 'var(--bg-primary)',
                color: isPressing || isRecording 
                  ? 'var(--text-inverse)' 
                  : 'var(--text-primary)',
                borderColor: isPressing || isRecording 
                  ? 'var(--error-color)' 
                  : 'var(--border-color)',
                transform: isPressing ? 'scale(0.98)' : 'scale(1)',
                transition: 'transform 0.1s ease, background-color 0.2s ease',
                textAlign: 'center',
              }}
              autoSize={{ minRows: 1, maxRows: 1 }}
            />
          )}

          {/* 发送按钮 */}
          {!isVoiceCallActive && !isConnecting && (
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
          )}

          {/* 语音通话按钮 */}
          <button
            type="button"
            onClick={async (e) => {
              // ✅ 关键修复：阻止事件冒泡和重复触发
              e.preventDefault();
              e.stopPropagation();
              
              // ✅ 关键修复：使用 ref 锁定按钮状态，防止异步过程中状态变化
              // 在事件处理开始时立即锁定状态，避免异步操作期间状态变化导致重复触发
              const buttonClickedAt = Date.now();
              const wasActive = isVoiceCallActive;
              
              // 添加防抖：如果距离上次点击太近（< 500ms），忽略
              const lastClickTime = (window as any).__lastVoiceCallClick || 0;
              if (buttonClickedAt - lastClickTime < 500) {
                log.debug('点击过快，忽略');
                return;
              }
              (window as any).__lastVoiceCallClick = buttonClickedAt;
              
              if (wasActive) {
                // 如果正在通话，结束通话
                try {
                  await endCall();
                  
                  // 保存语音通话消息到数据库，并添加到 React Query 缓存
                  if (voiceCallMessages.length > 0 && currentSessionId) {
                    try {
                      // 过滤并格式化消息：只保存有效的消息（content不为空）
                      const validMessages = voiceCallMessages
                        .map((msg) => {
                          // 提取content
                          let content = '';
                          if (typeof msg.content === 'string') {
                            content = msg.content.trim();
                          } else if (msg.content && typeof msg.content === 'object') {
                            // 尝试从对象中提取text字段
                            content = (msg.content as any)?.text || '';
                            if (typeof content === 'string') {
                              content = content.trim();
                            } else {
                              content = '';
                            }
                          }
                          
                          // 只返回有内容的消息
                          if (!content) {
                            return null;
                          }
                          
                          return {
                            role: msg.role as 'user' | 'assistant',
                            content: content,
                            timestamp: typeof msg.timestamp === 'string' 
                              ? msg.timestamp 
                              : msg.timestamp instanceof Date 
                                ? msg.timestamp.toISOString()
                                : new Date(msg.timestamp).toISOString(),
                          };
                        })
                        .filter((msg): msg is { role: 'user' | 'assistant'; content: string; timestamp: string } => msg !== null);
                      
                      // 只保存有有效消息的情况
                      if (validMessages.length > 0) {
                        await chatApi.saveVoiceCallMessages(currentSessionId, validMessages);
                        log.debug(`语音通话消息已保存到数据库: ${validMessages.length}条`);
                      } else {
                        log.warn('没有有效的语音通话消息需要保存（所有消息内容为空）');
                      }
                      log.debug('语音通话消息已保存到数据库');
                      
                      // 将消息添加到 React Query 缓存，保留在会话历史中
                      queryClient.setQueryData(
                        ['chat', 'messages', currentSessionId],
                        (old: Message[] = []) => {
                          // 合并消息，去重（基于ID）
                          const existingIds = new Set(old.map(m => m.id));
                          const newMessages = voiceCallMessages.filter(msg => !existingIds.has(msg.id));
                          return [...old, ...newMessages].sort((a, b) => {
                            const timeA = typeof a.timestamp === 'string' ? new Date(a.timestamp).getTime() : 
                                         typeof a.timestamp === 'number' ? a.timestamp : 
                                         a.timestamp instanceof Date ? a.timestamp.getTime() : 0;
                            const timeB = typeof b.timestamp === 'string' ? new Date(b.timestamp).getTime() : 
                                         typeof b.timestamp === 'number' ? b.timestamp : 
                                         b.timestamp instanceof Date ? b.timestamp.getTime() : 0;
                            return timeA - timeB;
                          });
                        }
                      );
                      
                      // 语音通话结束后触发标题生成（如果消息数达到阈值）
                      try {
                        const totalMessages = queryClient.getQueryData<Message[]>(['chat', 'messages', currentSessionId]) || [];
                        if (totalMessages.length >= TITLE_TRIGGER_LENGTH && !titleGeneratedRef.current.has(currentSessionId)) {
                          log.debug('Triggering title generation after voice call for session:', currentSessionId);
                          await sessionApi.generateTitle(currentSessionId);
                          titleGeneratedRef.current.add(currentSessionId);
                          // 刷新会话列表以显示新标题（使用正确的queryKey，包含userId）
                          // 使用 refetchQueries 立即刷新，而不是 invalidateQueries
                          if (userId) {
                            await queryClient.refetchQueries({ queryKey: ['sessions', userId] });
                          } else {
                            await queryClient.refetchQueries({ queryKey: ['sessions'] });
                          }
                          log.info('Session title generated after voice call:', currentSessionId);
                        }
                      } catch (titleError: any) {
                        // 标题生成失败不影响主流程，仅记录日志
                        if (titleError?.response?.status !== 400) {
                          log.error('Failed to generate title after voice call:', titleError);
                        }
                      }
                    } catch (error) {
                      log.error('保存语音通话消息失败:', error);
                      showError(error, '保存语音通话消息失败');
                    }
                  }
                  
                  // 清空状态（不影响已添加到缓存的消息）
                  clearVoiceCallMessages();
                  endVoiceCall();
                } catch (error) {
                  log.error('结束通话失败:', error);
                  showError(error, '结束通话失败');
                }
              } else {
                // 开始语音通话
                try {
                  // ✅ 关键修复：不立即设置 startVoiceCall()
                  // 让 isConnecting 状态控制UI显示"正在连接"
                  // 在 startCall() 成功后，才设置 startVoiceCall() 显示"可以说话"
                  
                  // 开始实际通话（异步）
                  await startCall();
                  
                  // ✅ 通话启动成功后，才设置UI状态为"可以说话"
                  // 此时 isCalling = true，UI会显示为通话状态
                  startVoiceCall();
                } catch (error) {
                  log.error('开始语音通话失败:', error);
                  showError(error, '开始语音通话失败');
                  // 失败时清除UI状态
                  endVoiceCall();
                }
              }
            }}
            disabled={isLoading || isStreaming || isTranscribing || (isConnecting && !isVoiceCallActive)}
            style={{
              // 连接中或通话中时，按钮直接变成通话状态大小（无动画）
              // 保持固定高度36px，不会因为内容变化而改变
              ...((isConnecting || isVoiceCallActive)
                ? { 
                    flex: 1, 
                    flexGrow: 1, 
                    flexBasis: 0,
                    width: '100%',
                    height: '36px', // 固定高度
                    padding: '0 16px', // 只设置左右内边距
                  }
                : { 
                    flex: 'none', 
                    flexGrow: 0, 
              flexShrink: 0,
                    flexBasis: 'auto',
              width: '36px',
              height: '36px',
                    padding: 0,
                  }
              ),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              border: 'none',
              borderRadius: '8px',
              backgroundColor: isVoiceCallActive ? '#ff4d4f' : (isConnecting ? 'var(--primary-color)' : 'var(--primary-color)'),
              cursor: (isLoading || isStreaming || isTranscribing || (isConnecting && !isVoiceCallActive)) ? 'not-allowed' : 'pointer',
              color: 'white',
              transition: 'background-color 0.2s ease', // 只保留背景色过渡，不包含尺寸变化
              outline: 'none',
              opacity: (isLoading || isStreaming || isTranscribing) ? 0.5 : 1,
              position: 'relative',
              zIndex: 10,
            }}
            onMouseEnter={(e) => {
              if (!(isLoading || isStreaming || isTranscribing || (isConnecting && !isVoiceCallActive))) {
                e.currentTarget.style.backgroundColor = isVoiceCallActive ? '#ff7875' : 'var(--primary-hover)';
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = isVoiceCallActive ? '#ff4d4f' : (isConnecting ? 'var(--primary-color)' : 'var(--primary-color)');
            }}
            title={
              isConnecting 
                ? '正在连接...' 
                : isVoiceCallActive 
                  ? '结束通话' 
                  : '语音通话'
            }
          >
            {isConnecting ? (
              // 连接中：只显示声纹动画
              <div className="voice-waveforms" style={{ width: '180px', height: '40px' }}>
                <VoiceWaveform 
                  frequencyData={null} 
                  color="#ffffff"
                  isActive={true}
                  isConnecting={true}
                />
              </div>
            ) : isVoiceCallActive ? (
              // 通话中：显示挂断图标
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 16 16" style={{ display: 'block' }}>
                <path fill="#fff" d="M15.897 9c.125.867.207 2.053-.182 2.507c-.643.751-4.714.751-4.714-.751c0-.756.67-1.252.027-2.003c-.632-.738-1.766-.75-3.027-.751s-2.394.012-3.027.751c-.643.751.027 1.247.027 2.003c0 1.501-4.071 1.501-4.714.751C-.102 11.053-.02 9.867.105 9c.096-.579.339-1.203 1.118-2c1.168-1.09 2.935-1.98 6.716-2h.126c3.781.019 5.548.91 6.716 2c.778.797 1.022 1.421 1.118 2z" />
              </svg>
            ) : (
              // 未连接：显示电话图标
            <PhoneOutlined style={{ fontSize: '18px', color: 'white', transform: 'rotate(-90deg)' }} />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

