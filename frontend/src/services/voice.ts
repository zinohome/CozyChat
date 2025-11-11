import { apiClient } from './api';
import type {
  TranscriptionRequest,
  TranscriptionResponse,
  SpeechRequest,
} from '@/types/voice';

/**
 * 语音API服务
 *
 * 封装语音相关的API调用。
 */
export const voiceApi = {
  /**
   * STT转录（语音转文本）
   */
  async transcribe(
    audioFile: File,
    options?: TranscriptionRequest
  ): Promise<TranscriptionResponse> {
    const formData = new FormData();
    formData.append('file', audioFile);
    if (options?.model) {
      formData.append('model', options.model);
    }
    if (options?.language) {
      formData.append('language', options.language);
    }
    if (options?.personality_id) {
      formData.append('personality_id', options.personality_id);
    }

    return apiClient.post<TranscriptionResponse>(
      '/v1/audio/transcribe',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
  },

  /**
   * TTS语音合成（文本转语音）
   */
  async synthesize(request: SpeechRequest): Promise<Blob> {
    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/v1/audio/speech`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '语音合成失败' }));
      throw new Error(error.detail || '语音合成失败');
    }

    return response.blob();
  },

  /**
   * 流式TTS语音合成
   */
  async *synthesizeStream(request: SpeechRequest): AsyncGenerator<Blob> {
    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/v1/audio/speech/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '流式语音合成失败' }));
      throw new Error(error.detail || '流式语音合成失败');
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('无法读取响应流');
    }

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        yield new Blob([value]);
      }
    } finally {
      reader.releaseLock();
    }
  },
};

