import { useState, useRef, useCallback } from 'react';
import { voiceApi } from '@/services/voice';
import { showError } from '@/utils/errorHandler';
import type { TranscriptionRequest } from '@/types/voice';

/**
 * 语音录制Hook
 *
 * 提供录音、停止、转录等功能。
 */
export function useVoiceRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  /**
   * 开始录音
   */
  const startRecording = useCallback(async () => {
    try {
      // 请求麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // 创建 MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus', // 使用 WebM 格式，兼容性好
      });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // 监听数据可用事件
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // 开始录音
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error: any) {
      console.error('开始录音失败:', error);
      showError(error, '无法访问麦克风，请检查权限设置');
      setIsRecording(false);
    }
  }, []);

  /**
   * 停止录音
   */
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }

    // 停止所有音频轨道
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, [isRecording]);

  /**
   * 转录录音
   */
  const transcribe = useCallback(
    async (options?: TranscriptionRequest): Promise<string | null> => {
      if (audioChunksRef.current.length === 0) {
        return null;
      }

      try {
        setIsTranscribing(true);

        // 合并音频块
        const audioBlob = new Blob(audioChunksRef.current, {
          type: 'audio/webm;codecs=opus',
        });

        // 转换为 File 对象
        const audioFile = new File([audioBlob], 'recording.webm', {
          type: 'audio/webm;codecs=opus',
        });

        // 调用 STT API
        console.log('开始调用STT API，音频文件大小:', audioFile.size, 'bytes');
        const response = await voiceApi.transcribe(audioFile, options);
        console.log('STT API响应:', response);

        // 清空音频块
        audioChunksRef.current = [];

        const text = response.text || null;
        console.log('STT识别文本:', text, '长度:', text?.length);
        return text;
      } catch (error) {
        console.error('转录失败:', error);
        showError(error, '语音识别失败');
        return null;
      } finally {
        setIsTranscribing(false);
      }
    },
    []
  );

  /**
   * 清理资源
   */
  const cleanup = useCallback(() => {
    stopRecording();
    audioChunksRef.current = [];
  }, [stopRecording]);

  return {
    isRecording,
    isTranscribing,
    startRecording,
    stopRecording,
    transcribe,
    cleanup,
  };
}

