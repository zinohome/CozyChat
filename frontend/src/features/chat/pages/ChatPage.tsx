import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { EnhancedChatContainer } from '../components/EnhancedChatContainer';
import { useChatStore } from '@/store/slices/chatSlice';
import { personalityApi } from '@/services/personality';
import { showError } from '@/utils/errorHandler';
import { useIsMobile } from '@/hooks/useMediaQuery';

/**
 * 聊天页面
 *
 * 集成ChatUI组件的聊天页面。
 */
export const ChatPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const { setCurrentSessionId } = useChatStore();
  const [personalityId, setPersonalityId] = useState<string>('default');
  const isMobile = useIsMobile();

  // 设置当前会话ID
  useEffect(() => {
    if (sessionId) {
      setCurrentSessionId(sessionId);
    } else {
      // 如果没有sessionId，创建新会话或使用默认会话
      setCurrentSessionId(null);
    }
  }, [sessionId, setCurrentSessionId]);

  // 获取默认人格（优先使用 health_assistant）
  useEffect(() => {
    const loadDefaultPersonality = async () => {
      try {
        const personalities = await personalityApi.getPersonalities();
        if (personalities.length > 0) {
          // 优先选择 health_assistant，如果不存在则使用第一个
          const healthAssistant = personalities.find(p => p.id === 'health_assistant');
          setPersonalityId(healthAssistant?.id || personalities[0].id);
        }
      } catch (error) {
        showError(error, '加载人格列表失败');
      }
    };
    loadDefaultPersonality();
  }, []);

  const currentSessionId = sessionId || 'default';

  // 根据屏幕尺寸计算 padding（MainLayout Content 的 padding）
  const contentPadding = isMobile ? 12 : 24;
  const paddingTotal = contentPadding * 2; // 上下各一个 padding

  return (
    <MainLayout>
      <div 
        style={{ 
          height: `calc(100vh - 64px - ${paddingTotal}px)`, // 减去 header(64px) 和 Content padding
          display: 'flex', 
          flexDirection: 'column',
          overflow: 'hidden', // 防止外层出现滚动条
          margin: `-${contentPadding}px`, // 抵消 MainLayout Content 的 padding
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

