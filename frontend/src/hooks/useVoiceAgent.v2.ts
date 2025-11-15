/**
 * Voice Agent Hook（重构版本）
 * 
 * 使用 VoiceAgentService 协调所有模块，简化 Hook 逻辑。
 * 从原来的 900+ 行简化到 ~150 行。
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { VoiceAgentService } from '@/features/voice/services/VoiceAgentService';
import type { EventHandlerCallbacks } from '@/features/voice/services/EventHandler';

/**
 * Voice Agent Hook 返回值
 */
export interface UseVoiceAgentReturn {
  /** 是否已连接 */
  isConnected: boolean;
  /** 是否正在连接中 */
  isConnecting: boolean;
  /** 是否正在通话 */
  isCalling: boolean;
  /** 错误信息 */
  error: string | null;
  /** 用户音频频率数据（用于可视化） */
  userFrequencyData: Uint8Array | null;
  /** 助手音频频率数据（用于可视化） */
  assistantFrequencyData: Uint8Array | null;
  /** 连接 Voice Agent */
  connect: () => Promise<void>;
  /** 断开连接 */
  disconnect: () => void;
  /** 开始通话 */
  startCall: () => Promise<void>;
  /** 结束通话 */
  endCall: () => Promise<void>;
}

/**
 * Voice Agent Hook
 * 
 * @param sessionId - 会话ID
 * @param personalityId - 人格ID
 * @param callbacks - 回调函数
 * @returns Voice Agent Hook返回值
 */
export const useVoiceAgent = (
  sessionId?: string,
  personalityId?: string,
  callbacks?: EventHandlerCallbacks
): UseVoiceAgentReturn => {
  // 状态
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isCalling, setIsCalling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userFrequencyData, setUserFrequencyData] = useState<Uint8Array | null>(null);
  const [assistantFrequencyData, setAssistantFrequencyData] = useState<Uint8Array | null>(null);

  // VoiceAgentService 实例
  const serviceRef = useRef<VoiceAgentService | null>(null);
  const frequencyUpdateIntervalRef = useRef<number | null>(null);

  /**
   * 初始化服务
   */
  const initService = useCallback(() => {
    if (!serviceRef.current) {
      serviceRef.current = new VoiceAgentService({
        sessionId,
        personalityId,
        callbacks,
      });
      console.log('[useVoiceAgent] VoiceAgentService 已初始化');
    }
    return serviceRef.current;
  }, [sessionId, personalityId, callbacks]);

  /**
   * 连接 Voice Agent
   */
  const connect = useCallback(async () => {
    if (isConnected) {
      console.warn('[useVoiceAgent] 已连接，无需重复连接');
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const service = initService();
      await service.connect();
      
      setIsConnected(true);
      setIsConnecting(false);
      
      console.log('[useVoiceAgent] 连接成功');
    } catch (err: any) {
      console.error('[useVoiceAgent] 连接失败:', err);
      setError(err.message || '连接失败');
      setIsConnecting(false);
      setIsConnected(false);
      throw err;
    }
  }, [isConnected, initService]);

  /**
   * 断开连接
   */
  const disconnect = useCallback(() => {
    if (serviceRef.current) {
      serviceRef.current.disconnect();
      serviceRef.current = null;
    }

    // 停止频率数据更新
    if (frequencyUpdateIntervalRef.current) {
      clearInterval(frequencyUpdateIntervalRef.current);
      frequencyUpdateIntervalRef.current = null;
    }

    setIsConnected(false);
    setIsCalling(false);
    setUserFrequencyData(null);
    setAssistantFrequencyData(null);
    
    console.log('[useVoiceAgent] 已断开连接');
  }, []);

  /**
   * 开始通话
   */
  const startCall = useCallback(async () => {
    if (!isConnected || !serviceRef.current) {
      // 如果未连接，先连接
      await connect();
    }

    if (isCalling) {
      console.warn('[useVoiceAgent] 已在通话中');
      return;
    }

    try {
      console.log('[useVoiceAgent] 开始通话');
      
      await serviceRef.current!.startCall();
      setIsCalling(true);

      // 启动频率数据更新（轮询）
      // 注意：这里使用轮询而不是回调，因为 Hook 层需要触发 React 更新
      const audioVisualizer = serviceRef.current!.getAudioVisualizer();
      
      frequencyUpdateIntervalRef.current = window.setInterval(() => {
        // 从 AudioVisualizer 获取最新的频率数据
        const userFreq = audioVisualizer.getCurrentUserFrequencyData();
        const assistantFreq = audioVisualizer.getCurrentAssistantFrequencyData();
        
        if (userFreq) {
          setUserFrequencyData(userFreq);
        }
        if (assistantFreq) {
          setAssistantFrequencyData(assistantFreq);
        }
      }, 50); // 20fps更新频率

      console.log('[useVoiceAgent] 通话已开始');
    } catch (err: any) {
      console.error('[useVoiceAgent] 开始通话失败:', err);
      setError(err.message || '开始通话失败');
      throw err;
    }
  }, [isConnected, isCalling, connect]);

  /**
   * 结束通话
   */
  const endCall = useCallback(() => {
    if (!isCalling || !serviceRef.current) {
      console.warn('[useVoiceAgent] 未在通话中');
      return;
    }

    console.log('[useVoiceAgent] 结束通话');
    
    serviceRef.current.endCall();

    // 停止频率数据更新
    if (frequencyUpdateIntervalRef.current) {
      clearInterval(frequencyUpdateIntervalRef.current);
      frequencyUpdateIntervalRef.current = null;
    }

    setIsCalling(false);
    setUserFrequencyData(null);
    setAssistantFrequencyData(null);
    
    console.log('[useVoiceAgent] 通话已结束');
  }, [isCalling]);

  /**
   * 组件卸载时清理
   */
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // 返回接口
  return {
    isConnected,
    isConnecting,
    isCalling,
    error,
    userFrequencyData,
    assistantFrequencyData,
    connect,
    disconnect,
    startCall,
    endCall,
  };
};

