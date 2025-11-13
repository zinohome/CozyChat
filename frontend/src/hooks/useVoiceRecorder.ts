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
   * 将 WebM 音频转换为 WAV 格式
   */
  const convertWebMToWAV = useCallback(async (webmBlob: Blob): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      // 创建音频上下文
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      
      // 读取 WebM Blob
      const fileReader = new FileReader();
      fileReader.onload = async () => {
        try {
          // 解码音频数据
          const audioBuffer = await audioContext.decodeAudioData(fileReader.result as ArrayBuffer);
          
          // 获取音频参数
          const sampleRate = audioBuffer.sampleRate;
          const numberOfChannels = audioBuffer.numberOfChannels;
          const length = audioBuffer.length;
          
          // 创建 WAV 文件头
          const wavHeader = new ArrayBuffer(44);
          const view = new DataView(wavHeader);
          
          // RIFF chunk descriptor
          const writeString = (offset: number, string: string) => {
            for (let i = 0; i < string.length; i++) {
              view.setUint8(offset + i, string.charCodeAt(i));
            }
          };
          
          writeString(0, 'RIFF');
          view.setUint32(4, 36 + length * numberOfChannels * 2, true); // File size - 8
          writeString(8, 'WAVE');
          
          // FMT sub-chunk
          writeString(12, 'fmt ');
          view.setUint32(16, 16, true); // Sub-chunk size
          view.setUint16(20, 1, true); // Audio format (PCM)
          view.setUint16(22, numberOfChannels, true);
          view.setUint32(24, sampleRate, true);
          view.setUint32(28, sampleRate * numberOfChannels * 2, true); // Byte rate
          view.setUint16(32, numberOfChannels * 2, true); // Block align
          view.setUint16(34, 16, true); // Bits per sample
          
          // Data sub-chunk
          writeString(36, 'data');
          view.setUint32(40, length * numberOfChannels * 2, true);
          
          // 转换音频数据为 PCM16
          const pcmData = new Int16Array(length * numberOfChannels);
          for (let channel = 0; channel < numberOfChannels; channel++) {
            const channelData = audioBuffer.getChannelData(channel);
            for (let i = 0; i < length; i++) {
              const sample = Math.max(-1, Math.min(1, channelData[i]));
              pcmData[i * numberOfChannels + channel] = sample < 0 
                ? sample * 0x8000 
                : sample * 0x7FFF;
            }
          }
          
          // 合并 WAV 头和数据
          const wavBlob = new Blob([wavHeader, pcmData.buffer], { type: 'audio/wav' });
          resolve(wavBlob);
        } catch (error) {
          reject(error);
        }
      };
      
      fileReader.onerror = reject;
      fileReader.readAsArrayBuffer(webmBlob);
    });
  }, []);

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
        const webmBlob = new Blob(audioChunksRef.current, {
          type: 'audio/webm;codecs=opus',
        });

        // 将 WebM 转换为 WAV（New API 需要 WAV 格式）
        console.log('开始转换 WebM 到 WAV，原始大小:', webmBlob.size, 'bytes');
        const wavBlob = await convertWebMToWAV(webmBlob);
        console.log('转换完成，WAV 大小:', wavBlob.size, 'bytes');

        // 转换为 File 对象
        const audioFile = new File([wavBlob], 'recording.wav', {
          type: 'audio/wav',
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
    [convertWebMToWAV]
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

