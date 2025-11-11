import { useState, useRef, useCallback, useEffect } from 'react';

/**
 * 音频可视化Hook返回值
 */
export interface UseAudioVisualizationReturn {
  /** 频率数据 */
  frequencyData: Uint8Array | null;
  /** 时域数据 */
  timeData: Uint8Array | null;
  /** 开始可视化 */
  start: (audioElement: HTMLAudioElement | MediaStream) => void;
  /** 停止可视化 */
  stop: () => void;
  /** 是否正在可视化 */
  isActive: boolean;
}

/**
 * 音频可视化Hook
 *
 * 提供音频可视化功能，使用Web Audio API分析音频数据。
 */
export const useAudioVisualization = (): UseAudioVisualizationReturn => {
  const [frequencyData, setFrequencyData] = useState<Uint8Array | null>(null);
  const [timeData, setTimeData] = useState<Uint8Array | null>(null);
  const [isActive, setIsActive] = useState(false);

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | MediaStreamAudioSourceNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  /**
   * 分析音频数据
   */
  const analyze = useCallback(() => {
    if (!analyserRef.current) return;

    const bufferLength = analyserRef.current.frequencyBinCount;
    const frequencyDataArray = new Uint8Array(bufferLength);
    const timeDataArray = new Uint8Array(bufferLength);

    analyserRef.current.getByteFrequencyData(frequencyDataArray);
    analyserRef.current.getByteTimeDomainData(timeDataArray);

    setFrequencyData(frequencyDataArray);
    setTimeData(timeDataArray);

    if (isActive) {
      animationFrameRef.current = requestAnimationFrame(analyze);
    }
  }, [isActive]);

  /**
   * 开始可视化
   */
  const start = useCallback((audioElement: HTMLAudioElement | MediaStream) => {
    try {
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
      if (audioElement instanceof HTMLAudioElement) {
        const source = audioContext.createMediaElementSource(audioElement);
        source.connect(analyser);
        analyser.connect(audioContext.destination);
        sourceRef.current = source;
      } else {
        const source = audioContext.createMediaStreamSource(audioElement);
        source.connect(analyser);
        sourceRef.current = source;
      }

      setIsActive(true);
      analyze();
    } catch (err) {
      console.error('Failed to start audio visualization:', err);
    }
  }, [analyze]);

  /**
   * 停止可视化
   */
  const stop = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close().catch(console.error);
      audioContextRef.current = null;
    }

    setIsActive(false);
    setFrequencyData(null);
    setTimeData(null);
  }, []);

  // 清理
  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  return {
    frequencyData,
    timeData,
    start,
    stop,
    isActive,
  };
};

