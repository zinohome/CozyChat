import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { EnhancedChatContainer } from '../components/EnhancedChatContainer';
import { useChatStore } from '@/store/slices/chatSlice';
import { personalityApi } from '@/services/personality';
import { showError } from '@/utils/errorHandler';

/**
 * 聊天页面
 *
 * 集成ChatUI组件的聊天页面。
 */
export const ChatPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const { setCurrentSessionId } = useChatStore();
  const [personalityId, setPersonalityId] = useState<string>('default');

  // 设置当前会话ID
  useEffect(() => {
    if (sessionId) {
      setCurrentSessionId(sessionId);
    } else {
      // 如果没有sessionId，创建新会话或使用默认会话
      setCurrentSessionId(null);
    }
  }, [sessionId, setCurrentSessionId]);

  // 获取默认人格
  useEffect(() => {
    const loadDefaultPersonality = async () => {
      try {
        const personalities = await personalityApi.getPersonalities();
        if (personalities.length > 0) {
          setPersonalityId(personalities[0].id);
        }
      } catch (error) {
        showError(error, '加载人格列表失败');
      }
    };
    loadDefaultPersonality();
  }, []);

  const currentSessionId = sessionId || 'default';

  return (
    <MainLayout>
      <div style={{ height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column' }}>
        <EnhancedChatContainer
          sessionId={currentSessionId}
          personalityId={personalityId}
        />
      </div>
    </MainLayout>
  );
};

export default ChatPage;

