import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/MainLayout';
import { EnhancedChatContainer } from '../components/EnhancedChatContainer';
import { useChatStore } from '@/store/slices/chatSlice';
import { useAuthStore } from '@/store/slices/authSlice';
import { personalityApi } from '@/services/personality';
import { userApi } from '@/services/user';
import { useSessions } from '../hooks/useSessions';
import { showError } from '@/utils/errorHandler';
import { useIsMobile } from '@/hooks/useMediaQuery';

/**
 * 聊天页面
 *
 * 集成ChatUI组件的聊天页面。
 */
export const ChatPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();
  const { setCurrentSessionId } = useChatStore();
  const { user } = useAuthStore();
  const userId = user?.id || null;
  const [personalityId, setPersonalityId] = useState<string>('default');
  const isMobile = useIsMobile();
  const { sessions, isLoading: isLoadingSessions, createSession } = useSessions();
  const hasAutoSelectedRef = useRef(false); // 防止重复自动选择

  // 获取用户偏好设置（用于读取默认人格）
  const { data: preferences } = useQuery({
    queryKey: ['user', 'preferences'],
    queryFn: () => userApi.getCurrentUserPreferences(),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // 5分钟内认为数据是新鲜的
    cacheTime: 10 * 60 * 1000, // 10分钟内保留缓存
  });

  // 设置默认人格（优先使用用户偏好设置中的 default_personality）
  useEffect(() => {
    // 1. 优先使用用户偏好设置中的 default_personality（不需要等待人格列表）
    if (preferences?.default_personality && personalityId === 'default') {
      console.log('ChatPage: 使用用户偏好设置的人格', preferences.default_personality);
      setPersonalityId(preferences.default_personality);
      return;
    }

    // 2. 如果没有偏好设置，尝试加载人格列表（异步，不阻塞）
    if (!preferences?.default_personality && personalityId === 'default') {
      const loadDefaultPersonality = async () => {
        try {
          const personalities = await personalityApi.getPersonalities();
          if (personalities.length > 0) {
            // 优先使用 health_assistant
            const healthAssistant = personalities.find(p => p.id === 'health_assistant');
            const selectedPersonalityId = healthAssistant?.id || personalities[0].id;
            console.log('ChatPage: 从人格列表设置默认人格', selectedPersonalityId);
            setPersonalityId(selectedPersonalityId);
          } else {
            console.log('ChatPage: 人格列表为空，保持默认人格 default');
          }
        } catch (error) {
          console.error('ChatPage: 加载人格列表失败', error);
          // 保持 'default'，不影响自动选择会话
        }
      };
      loadDefaultPersonality();
    }
  }, [preferences, personalityId]);

  // 设置当前会话ID
  useEffect(() => {
    if (sessionId) {
      setCurrentSessionId(sessionId);
      // 如果有 sessionId，标记为已处理，不需要自动选择
      hasAutoSelectedRef.current = true;
    } else {
      setCurrentSessionId(null);
      // 如果没有 sessionId，重置标记，允许自动选择
      hasAutoSelectedRef.current = false;
    }
  }, [sessionId, setCurrentSessionId]);

  // 自动选择第一个会话或创建新会话
  useEffect(() => {
    // 如果已经有 sessionId，不需要自动选择
    if (sessionId) {
      return;
    }

    // 如果已经自动选择过，不再重复执行
    if (hasAutoSelectedRef.current) {
      return;
    }

    // 等待用户登录和会话列表加载完成
    // 注意：选择现有会话不需要人格ID，只有创建新会话时才需要
    if (!userId || isLoadingSessions) {
      console.log('ChatPage: 等待条件满足', {
        userId,
        isLoadingSessions,
        personalityId,
        sessionsLength: sessions.length,
      });
      return;
    }

    // 如果需要创建新会话，优先使用用户偏好设置中的 default_personality
    // 如果没有，可以使用 'default' 作为后备
    if (sessions.length === 0) {
      // 如果 personalityId 为空，使用偏好设置或 'default'
      const sessionPersonalityId = personalityId || preferences?.default_personality || 'default';
      if (!personalityId && !preferences?.default_personality) {
        // 如果既没有 personalityId 也没有偏好设置，等待一下（但不会阻塞太久）
        console.log('ChatPage: 等待人格ID或偏好设置加载（需要创建新会话）', {
          personalityId,
          hasPreferences: !!preferences,
          sessionsLength: sessions.length,
        });
        return;
      }
      // 如果有偏好设置或 personalityId，可以继续创建会话
    }

    // 标记为已处理，防止重复执行
    hasAutoSelectedRef.current = true;

    console.log('ChatPage: 开始自动选择会话', {
      sessionsLength: sessions.length,
      personalityId,
    });

    const autoSelectSession = async () => {
      try {
        if (sessions.length > 0) {
          // 有会话，选择第一个（最上面的，最新的）
          const firstSession = sessions[0];
          const firstSessionId = firstSession.id || firstSession.session_id;
          console.log('ChatPage: 选择第一个会话', firstSessionId);
          if (firstSessionId) {
            setCurrentSessionId(firstSessionId);
            navigate(`/chat/${firstSessionId}`, { replace: true });
          }
        } else {
          // 没有会话，自动创建新会话
          // 优先级：personalityId > preferences.default_personality > 'default'
          const sessionPersonalityId = personalityId || preferences?.default_personality || 'default';
          console.log('ChatPage: 没有会话，创建新会话，使用人格:', sessionPersonalityId, {
            fromPersonalityId: !!personalityId,
            fromPreferences: !!preferences?.default_personality,
            fallback: sessionPersonalityId === 'default',
          });
          const newSession = await createSession({
            title: '新会话',
            personality_id: sessionPersonalityId,
          });
          const newSessionId = newSession.id || newSession.session_id;
          console.log('ChatPage: 新会话创建成功', newSessionId);
          if (newSessionId) {
            setCurrentSessionId(newSessionId);
            navigate(`/chat/${newSessionId}`, { replace: true });
          }
        }
      } catch (error) {
        console.error('ChatPage: 自动选择会话失败:', error);
        // 重置标记，允许重试
        hasAutoSelectedRef.current = false;
        // 不显示错误，因为这是自动操作
      }
    };

    autoSelectSession();
  }, [sessionId, sessions, isLoadingSessions, personalityId, createSession, setCurrentSessionId, navigate]);

  const currentSessionId = sessionId || 'default';

  // 根据屏幕尺寸计算 padding（MainLayout Content 的 padding）
  const contentPadding = isMobile ? 12 : 24;
  const paddingTotal = contentPadding * 2; // 左右各一个 padding

  return (
    <MainLayout>
      <div 
        style={{ 
          height: 'calc(100vh - 64px)',
          display: 'flex', 
          flexDirection: 'column',
          overflow: 'hidden',
          margin: `-${contentPadding}px`,
          width: `calc(100% + ${paddingTotal}px)`,
          maxWidth: `calc(100% + ${paddingTotal}px)`,
        }}
      >
        <EnhancedChatContainer
          sessionId={currentSessionId}
          personalityId={personalityId}
        />
      </div>
    </MainLayout>
  );
};

export default ChatPage;

