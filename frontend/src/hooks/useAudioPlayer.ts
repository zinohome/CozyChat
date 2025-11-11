import { useState, useRef, useCallback, useEffect } from 'react';

/**
 * 播放状态
 */
export type PlaybackStatus = 'idle' | 'playing' | 'paused' | 'stopped';

/**
 * 音频播放Hook返回值
 */
export interface UseAudioPlayerReturn {
  /** 播放状态 */
  status: PlaybackStatus;
  /** 是否正在播放 */
  isPlaying: boolean;
  /** 当前播放时间（秒） */
  currentTime: number;
  /** 总时长（秒） */
  duration: number;
  /** 音量（0-1） */
  volume: number;
  /** 播放进度（0-1） */
  progress: number;
  /** 播放音频 */
  play: (audioUrl: string | Blob) => Promise<void>;
  /** 暂停播放 */
  pause: () => void;
  /** 恢复播放 */
  resume: () => void;
  /** 停止播放 */
  stop: () => void;
  /** 设置播放位置 */
  seek: (time: number) => void;
  /** 设置音量 */
  setVolume: (volume: number) => void;
  /** 错误信息 */
  error: string | null;
}

/**
 * 音频播放Hook
 *
 * 提供音频播放功能，支持播放、暂停、停止、进度控制等操作。
 */
export const useAudioPlayer = (): UseAudioPlayerReturn => {
  const [status, setStatus] = useState<PlaybackStatus>('idle');
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolumeState] = useState(1);
  const [error, setError] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  /**
   * 更新播放进度
   */
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => {
      setCurrentTime(audio.currentTime);
    };

    const updateDuration = () => {
      setDuration(audio.duration || 0);
    };

    const handleEnded = () => {
      setStatus('stopped');
      setCurrentTime(0);
    };

    const handleError = () => {
      setError('音频播放失败');
      setStatus('idle');
    };

    audio.addEventListener('timeupdate', updateTime);
    audio.addEventListener('loadedmetadata', updateDuration);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);

    return () => {
      audio.removeEventListener('timeupdate', updateTime);
      audio.removeEventListener('loadedmetadata', updateDuration);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
    };
  }, []);

  /**
   * 播放音频
   */
  const play = useCallback(async (audioUrl: string | Blob) => {
    try {
      setError(null);

      // 如果已有音频，先停止
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }

      const url = typeof audioUrl === 'string' ? audioUrl : URL.createObjectURL(audioUrl);
      const audio = new Audio(url);
      audio.volume = volume;
      audioRef.current = audio;

      await audio.play();
      setStatus('playing');
    } catch (err: any) {
      setError(err.message || '音频播放失败');
      setStatus('idle');
    }
  }, [volume]);

  /**
   * 暂停播放
   */
  const pause = useCallback(() => {
    if (audioRef.current && status === 'playing') {
      audioRef.current.pause();
      setStatus('paused');
    }
  }, [status]);

  /**
   * 恢复播放
   */
  const resume = useCallback(() => {
    if (audioRef.current && status === 'paused') {
      audioRef.current.play();
      setStatus('playing');
    }
  }, [status]);

  /**
   * 停止播放
   */
  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setStatus('stopped');
      setCurrentTime(0);
    }
  }, []);

  /**
   * 设置播放位置
   */
  const seek = useCallback((time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  }, []);

  /**
   * 设置音量
   */
  const setVolume = useCallback((newVolume: number) => {
    const clampedVolume = Math.max(0, Math.min(1, newVolume));
    setVolumeState(clampedVolume);
    if (audioRef.current) {
      audioRef.current.volume = clampedVolume;
    }
  }, []);

  // 清理
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const progress = duration > 0 ? currentTime / duration : 0;

  return {
    status,
    isPlaying: status === 'playing',
    currentTime,
    duration,
    volume,
    progress,
    play,
    pause,
    resume,
    stop,
    seek,
    setVolume,
    error,
  };
};

