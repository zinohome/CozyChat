/**
 * useVoiceRecorder Hook测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useVoiceRecorder } from './useVoiceRecorder';

// Mock MediaRecorder
const mockMediaRecorder = {
  start: vi.fn(),
  stop: vi.fn(),
  pause: vi.fn(),
  resume: vi.fn(),
  state: 'inactive',
  ondataavailable: null,
  onerror: null,
  onstop: null,
};

global.MediaRecorder = vi.fn().mockImplementation(() => mockMediaRecorder) as any;
(global.MediaRecorder as any).isTypeSupported = vi.fn(() => true);

// Mock navigator.mediaDevices
Object.defineProperty(navigator, 'mediaDevices', {
  writable: true,
  value: {
    getUserMedia: vi.fn(() =>
      Promise.resolve({
        getTracks: () => [
          {
            stop: vi.fn(),
          },
        ],
      })
    ),
  },
});

// Mock voiceApi
vi.mock('@/services/voice', () => ({
  voiceApi: {
    transcribe: vi.fn(() => Promise.resolve({ text: 'Transcribed text' })),
  },
}));

describe('useVoiceRecorder', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockMediaRecorder.state = 'inactive';
  });

  it('应该初始化录音器', () => {
    const { result } = renderHook(() => useVoiceRecorder());
    
    expect(result.current.isRecording).toBe(false);
    expect(result.current.isTranscribing).toBe(false);
    expect(result.current.recordingDuration).toBe(0);
  });

  it('应该开始录音', async () => {
    const { result } = renderHook(() => useVoiceRecorder());
    
    await act(async () => {
      await result.current.startRecording();
    });
    
    expect(result.current.isRecording).toBe(true);
    expect(mockMediaRecorder.start).toHaveBeenCalled();
  });

  it('应该停止录音', async () => {
    const { result } = renderHook(() => useVoiceRecorder());
    
    await act(async () => {
      await result.current.startRecording();
    });
    
    await act(async () => {
      await result.current.stopRecording();
    });
    
    expect(result.current.isRecording).toBe(false);
    expect(mockMediaRecorder.stop).toHaveBeenCalled();
  });

  it('应该转录音频', async () => {
    const { result } = renderHook(() => useVoiceRecorder());
    
    // 模拟录音数据
    const mockBlob = new Blob(['audio data'], { type: 'audio/webm' });
    
    await act(async () => {
      await result.current.startRecording();
    });
    
    // 模拟录音数据收集
    if (mockMediaRecorder.ondataavailable) {
      mockMediaRecorder.ondataavailable({
        data: mockBlob,
        timecode: 0,
      } as any);
    }
    
    await act(async () => {
      await result.current.stopRecording();
    });
    
    // 等待录音停止
    await waitFor(() => {
      expect(result.current.isRecording).toBe(false);
    });
    
    // 转录音频
    await act(async () => {
      const text = await result.current.transcribe({ personality_id: 'test' });
      expect(text).toBe('Transcribed text');
    });
  });
});
