import { useState, useRef, useCallback, useEffect } from 'react';
import { useVAD, type VADStatus } from './useVAD';
import { showError } from '@/utils/errorHandler';

/**
 * RealTime语音消息类型
 */
export type RealtimeMessageType =
  | 'session.update'
  | 'response.audio.delta'
  | 'response.audio.done'
  | 'response.done'
  | 'error';

/**
 * RealTime消息
 */
export interface RealtimeMessage {
  type: RealtimeMessageType;
  data?: any;
}

/**
 * RealTime语音Hook返回值
 */
export interface UseRealtimeVoiceReturn {
  /** 是否已连接 */
  isConnected: boolean;
  /** 是否正在录音 */
  isRecording: boolean;
  /** VAD状态 */
  vadStatus: VADStatus;
  /** 连接WebSocket */
  connect: () => Promise<void>;
  /** 断开连接 */
  disconnect: () => void;
  /** 开始录音 */
  startRecording: () => void;
  /** 停止录音 */
  stopRecording: () => void;
  /** 发送音频数据 */
  sendAudio: (audioData: ArrayBuffer) => void;
  /** 错误信息 */
  error: string | null;
}

/**
 * RealTime语音Hook
 *
 * 集成WebSocket实现实时语音对话。
 */
export const useRealtimeVoice = (
  sessionId?: string,
  personalityId?: string
): UseRealtimeVoiceReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  const { status: vadStatus, start: startVAD, stop: stopVAD } = useVAD();

  /**
   * 处理WebSocket消息
   */
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: RealtimeMessage = JSON.parse(event.data);

      switch (message.type) {
        case 'session.update':
          // 会话更新
          break;
        case 'response.audio.delta':
          // 音频数据块
          if (message.data?.delta) {
            // 播放音频
            playAudioChunk(message.data.delta);
          }
          break;
        case 'response.audio.done':
          // 音频完成
          break;
        case 'response.done':
          // 响应完成
          break;
        case 'error':
          setError(message.data?.message || 'RealTime语音错误');
          break;
      }
    } catch (err) {
      console.error('Failed to parse WebSocket message:', err);
    }
  }, []);

  /**
   * 播放音频块
   */
  const playAudioChunk = useCallback(async (audioData: ArrayBuffer) => {
    try {
      if (!audioContextRef.current) {
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        audioContextRef.current = new AudioContextClass();
      }

      const audioBuffer = await audioContextRef.current.decodeAudioData(audioData);
      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContextRef.current.destination);
      source.start();
    } catch (err) {
      console.error('Failed to play audio chunk:', err);
    }
  }, []);

  /**
   * 连接WebSocket
   */
  const connect = useCallback(async () => {
    try {
      setError(null);

      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('未登录');
      }

      const wsUrl = `${
        import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'
      }/v1/ws/realtime?token=${token}&session_id=${sessionId || ''}&personality_id=${
        personalityId || ''
      }`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = handleMessage;

      ws.onerror = (event) => {
        setError('WebSocket连接错误');
        console.error('WebSocket error:', event);
      };

      ws.onclose = () => {
        setIsConnected(false);
        setIsRecording(false);
      };
    } catch (err: any) {
      setError(err.message || '连接失败');
      showError(err, 'RealTime语音连接失败');
    }
  }, [sessionId, personalityId, handleMessage]);

  /**
   * 断开连接
   */
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close().catch(console.error);
      audioContextRef.current = null;
    }

    stopVAD();
    setIsConnected(false);
    setIsRecording(false);
  }, [stopVAD]);

  /**
   * 开始录音
   */
  const startRecording = useCallback(async () => {
    if (!isConnected || !wsRef.current) {
      await connect();
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          event.data.arrayBuffer().then((buffer) => {
            wsRef.current?.send(buffer);
          });
        }
      };

      mediaRecorder.start(100); // 每100ms发送一次数据
      setIsRecording(true);
      startVAD();
    } catch (err: any) {
      setError(err.message || '无法访问麦克风');
      showError(err, '开始录音失败');
    }
  }, [isConnected, connect, startVAD]);

  /**
   * 停止录音
   */
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      stopVAD();
    }
  }, [isRecording, stopVAD]);

  /**
   * 发送音频数据
   */
  const sendAudio = useCallback(
    (audioData: ArrayBuffer) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(audioData);
      }
    },
    []
  );

  // 清理
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    isRecording,
    vadStatus,
    connect,
    disconnect,
    startRecording,
    stopRecording,
    sendAudio,
    error,
  };
};

