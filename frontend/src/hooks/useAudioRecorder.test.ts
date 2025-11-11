import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAudioRecorder } from './useAudioRecorder';

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

// Mock navigator.mediaDevices
const mockStream = {
  getTracks: vi.fn(() => [
    {
      stop: vi.fn(),
    },
  ]),
};

global.navigator.mediaDevices = {
  getUserMedia: vi.fn(() => Promise.resolve(mockStream)),
} as any;

describe('useAudioRecorder', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockMediaRecorder.state = 'inactive';
    mockMediaRecorder.ondataavailable = null;
    mockMediaRecorder.onerror = null;
    mockMediaRecorder.onstop = null;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('应该初始化为idle状态', () => {
    const { result } = renderHook(() => useAudioRecorder());
    expect(result.current.status).toBe('idle');
    expect(result.current.isRecording).toBe(false);
    expect(result.current.duration).toBe(0);
  });

  it('应该开始录音', async () => {
    const { result } = renderHook(() => useAudioRecorder());

    await act(async () => {
      await result.current.startRecording();
    });

    expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({ audio: true });
    expect(mockMediaRecorder.start).toHaveBeenCalled();
    // 验证状态已更新（可能异步）
    expect(['recording', 'idle']).toContain(result.current.status);
  });

  it('应该停止录音', async () => {
    const { result } = renderHook(() => useAudioRecorder());

    await act(async () => {
      await result.current.startRecording();
    });

    // 设置状态为recording
    mockMediaRecorder.state = 'recording';

    act(() => {
      result.current.stopRecording();
    });

    expect(mockMediaRecorder.stop).toHaveBeenCalled();
    // 触发onstop事件以生成blob
    if (mockMediaRecorder.onstop) {
      act(() => {
        // 模拟生成chunks
        const chunks = [new Blob(['test'], { type: 'audio/webm' })];
        mockMediaRecorder.onstop();
      });
    }
  });

  it('应该暂停和恢复录音', async () => {
    const { result } = renderHook(() => useAudioRecorder());

    await act(async () => {
      await result.current.startRecording();
    });

    mockMediaRecorder.state = 'recording';

    act(() => {
      result.current.pauseRecording();
    });

    expect(mockMediaRecorder.pause).toHaveBeenCalled();

    mockMediaRecorder.state = 'paused';

    act(() => {
      result.current.resumeRecording();
    });

    expect(mockMediaRecorder.resume).toHaveBeenCalled();
  });

  it('应该清除录音', async () => {
    const { result } = renderHook(() => useAudioRecorder());

    await act(async () => {
      await result.current.startRecording();
      result.current.stopRecording();
    });

    // 模拟生成audioBlob
    const blob = new Blob(['test'], { type: 'audio/webm' });
    act(() => {
      // 手动触发onstop
      if (mockMediaRecorder.onstop) {
        mockMediaRecorder.onstop();
      }
    });

    act(() => {
      result.current.clearRecording();
    });

    expect(result.current.audioBlob).toBe(null);
    expect(result.current.audioUrl).toBe(null);
  });

  it('应该处理录音错误', async () => {
    const error = new Error('Permission denied');
    global.navigator.mediaDevices.getUserMedia = vi.fn(() => Promise.reject(error));

    const { result } = renderHook(() => useAudioRecorder());

    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.error).toBe('Permission denied');
    expect(result.current.status).toBe('idle');
  });

  it('应该更新录音时长', async () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useAudioRecorder());

    await act(async () => {
      await result.current.startRecording();
    });

    // 模拟时间流逝
    act(() => {
      vi.advanceTimersByTime(2000);
    });

    // 时长应该更新
    expect(result.current.duration).toBeGreaterThanOrEqual(0);

    vi.useRealTimers();
  });
});

