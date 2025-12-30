/**
 * voiceApi服务测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { voiceApi } from './voice';
import { apiClient } from './api';

// Mock apiClient
vi.mock('./api', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe('voiceApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该发送语音转文字请求', async () => {
    const mockResponse = { text: 'Hello, world!' };
    (apiClient.post as any).mockResolvedValue(mockResponse);

    const audioFile = new File(['audio data'], 'audio.wav', { type: 'audio/wav' });
    const result = await voiceApi.transcribe(audioFile, { language: 'zh-CN' });
    
    expect(apiClient.post).toHaveBeenCalledWith(
      '/v1/audio/transcriptions',
      expect.any(FormData),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'multipart/form-data',
        }),
      })
    );
    expect(result).toEqual(mockResponse);
  });

  it('应该发送文字转语音请求', async () => {
    const mockBlob = new Blob(['audio data'], { type: 'audio/mpeg' });
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
    } as any);

    const result = await voiceApi.synthesize({
      text: 'Hello',
      voice: 'zh-CN-XiaoxiaoNeural',
    });
    
    expect(global.fetch).toHaveBeenCalled();
    expect(result).toBeInstanceOf(Blob);
  });
});
