import { useState, useRef, useCallback } from 'react';

/**
 * 录音状态
 */
export type RecordingStatus = 'idle' | 'recording' | 'paused' | 'stopped';

/**
 * 录音Hook返回值
 */
export interface UseAudioRecorderReturn {
  /** 录音状态 */
  status: RecordingStatus;
  /** 是否正在录音 */
  isRecording: boolean;
  /** 录音时长（秒） */
  duration: number;
  /** 音频Blob */
  audioBlob: Blob | null;
  /** 音频URL */
  audioUrl: string | null;
  /** 开始录音 */
  startRecording: () => Promise<void>;
  /** 停止录音 */
  stopRecording: () => void;
  /** 暂停录音 */
  pauseRecording: () => void;
  /** 恢复录音 */
  resumeRecording: () => void;
  /** 清除录音 */
  clearRecording: () => void;
  /** 错误信息 */
  error: string | null;
}

/**
 * 音频录音Hook
 *
 * 提供录音功能，支持开始、停止、暂停、恢复等操作。
 */
export const useAudioRecorder = (): UseAudioRecorderReturn => {
  const [status, setStatus] = useState<RecordingStatus>('idle');
  const [duration, setDuration] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const durationIntervalRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);

  /**
   * 清除录音
   */
  const clearRecording = useCallback(() => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    setAudioBlob(null);
    setAudioUrl(null);
    setDuration(0);
    setError(null);
  }, [audioUrl]);

  /**
   * 开始录音
   */
  const startRecording = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);

        // 清理流
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }
      };

      mediaRecorder.onerror = (event) => {
        setError('录音过程中发生错误');
        console.error('MediaRecorder error:', event);
      };

      mediaRecorder.start();
      setStatus('recording');
      startTimeRef.current = Date.now();

      // 更新时长
      durationIntervalRef.current = window.setInterval(() => {
        if (startTimeRef.current) {
          setDuration(Math.floor((Date.now() - startTimeRef.current) / 1000));
        }
      }, 1000);
    } catch (err: any) {
      setError(err.message || '无法访问麦克风');
      setStatus('idle');
    }
  }, []);

  /**
   * 停止录音
   */
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && status === 'recording') {
      mediaRecorderRef.current.stop();
      setStatus('stopped');

      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
      }
      startTimeRef.current = null;
    }
  }, [status]);

  /**
   * 暂停录音
   */
  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && status === 'recording') {
      mediaRecorderRef.current.pause();
      setStatus('paused');

      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
      }
    }
  }, [status]);

  /**
   * 恢复录音
   */
  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && status === 'paused') {
      mediaRecorderRef.current.resume();
      setStatus('recording');
      startTimeRef.current = Date.now() - duration * 1000;

      durationIntervalRef.current = window.setInterval(() => {
        if (startTimeRef.current) {
          setDuration(Math.floor((Date.now() - startTimeRef.current) / 1000));
        }
      }, 1000);
    }
  }, [status, duration]);

  return {
    status,
    isRecording: status === 'recording',
    duration,
    audioBlob,
    audioUrl,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    clearRecording,
    error,
  };
};

