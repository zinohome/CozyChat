import { useState, useRef, useCallback, useEffect } from 'react';

/**
 * VAD状态
 */
export type VADStatus = 'idle' | 'listening' | 'speaking' | 'silence';

/**
 * VAD配置
 */
export interface VADConfig {
  /** 音量阈值（0-1） */
  volumeThreshold?: number;
  /** 静音持续时间（毫秒） */
  silenceDuration?: number;
  /** 语音持续时间（毫秒） */
  speechDuration?: number;
}

/**
 * VAD Hook返回值
 */
export interface UseVADReturn {
  /** VAD状态 */
  status: VADStatus;
  /** 是否正在监听 */
  isListening: boolean;
  /** 是否检测到语音 */
  isSpeaking: boolean;
  /** 当前音量（0-1） */
  volume: number;
  /** 开始监听 */
  start: () => Promise<void>;
  /** 停止监听 */
  stop: () => void;
  /** 错误信息 */
  error: string | null;
}

/**
 * 语音活动检测（VAD）Hook
 *
 * 使用Web Audio API检测语音活动。
 */
export const useVAD = (config?: VADConfig): UseVADReturn => {
  const {
    volumeThreshold = 0.01,
    silenceDuration = 1000,
    speechDuration = 200,
  } = config || {};

  const [status, setStatus] = useState<VADStatus>('idle');
  const [volume, setVolume] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const silenceTimerRef = useRef<number | null>(null);
  const speechTimerRef = useRef<number | null>(null);

  /**
   * 分析音频
   */
  const analyze = useCallback(() => {
    if (!analyserRef.current) return;

    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyserRef.current.getByteFrequencyData(dataArray);

    // 计算平均音量
    const sum = dataArray.reduce((acc, val) => acc + val, 0);
    const avg = sum / bufferLength;
    const normalizedVolume = avg / 255;

    setVolume(normalizedVolume);

    // 检测语音活动
    if (normalizedVolume > volumeThreshold) {
      // 检测到语音
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }

      if (status !== 'speaking') {
        // 延迟设置speaking状态，避免短暂噪音
        if (speechTimerRef.current) {
          clearTimeout(speechTimerRef.current);
        }
        speechTimerRef.current = window.setTimeout(() => {
          setStatus('speaking');
        }, speechDuration);
      }
    } else {
      // 检测到静音
      if (speechTimerRef.current) {
        clearTimeout(speechTimerRef.current);
        speechTimerRef.current = null;
      }

      if (status === 'speaking') {
        // 延迟设置silence状态
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
        }
        silenceTimerRef.current = window.setTimeout(() => {
          setStatus('silence');
        }, silenceDuration);
      }
    }

    if (status === 'listening' || status === 'speaking' || status === 'silence') {
      animationFrameRef.current = requestAnimationFrame(analyze);
    }
  }, [status, volumeThreshold, silenceDuration, speechDuration]);

  /**
   * 开始监听
   */
  const start = useCallback(async () => {
    try {
      setError(null);

      // 获取麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // 创建AudioContext
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      const audioContext = new AudioContextClass();
      audioContextRef.current = audioContext;

      // 创建AnalyserNode
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;
      analyserRef.current = analyser;

      // 连接音频源
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);
      sourceRef.current = source;

      setStatus('listening');
      analyze();
    } catch (err: any) {
      setError(err.message || '无法访问麦克风');
      setStatus('idle');
    }
  }, [analyze]);

  /**
   * 停止监听
   */
  const stop = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }

    if (speechTimerRef.current) {
      clearTimeout(speechTimerRef.current);
      speechTimerRef.current = null;
    }

    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close().catch(console.error);
      audioContextRef.current = null;
    }

    setStatus('idle');
    setVolume(0);
  }, []);

  // 清理
  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  return {
    status,
    isListening: status === 'listening' || status === 'speaking' || status === 'silence',
    isSpeaking: status === 'speaking',
    volume,
    start,
    stop,
    error,
  };
};

