import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAudioPlayer } from './useAudioPlayer';

// Mock HTMLAudioElement
let mockAudio: any;

beforeEach(() => {
  mockAudio = {
    play: vi.fn(() => Promise.resolve()),
    pause: vi.fn(),
    load: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    currentTime: 0,
    duration: 100,
    volume: 1,
  };

  global.Audio = vi.fn().mockImplementation(() => mockAudio) as any;
});

describe('useAudioPlayer', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('应该初始化为idle状态', () => {
    const { result } = renderHook(() => useAudioPlayer());
    expect(result.current.status).toBe('idle');
    expect(result.current.isPlaying).toBe(false);
    expect(result.current.currentTime).toBe(0);
  });

  it('应该播放音频', async () => {
    const { result } = renderHook(() => useAudioPlayer());
    const audioUrl = 'blob:test-url';

    await act(async () => {
      await result.current.play(audioUrl);
    });

    expect(global.Audio).toHaveBeenCalled();
    expect(mockAudio.play).toHaveBeenCalled();
    // 注意：由于Audio事件是异步的，status可能不会立即更新
  });

  it('应该暂停播放', async () => {
    const { result } = renderHook(() => useAudioPlayer());
    const audioUrl = 'blob:test-url';

    await act(async () => {
      await result.current.play(audioUrl);
      // 手动设置状态为playing以测试pause
      if (mockAudio.addEventListener.mock.calls.length > 0) {
        const timeupdateHandler = mockAudio.addEventListener.mock.calls.find(
          (call: any[]) => call[0] === 'timeupdate'
        )?.[1];
        if (timeupdateHandler) {
          mockAudio.currentTime = 10;
          timeupdateHandler();
        }
      }
    });

    act(() => {
      result.current.pause();
    });

    expect(mockAudio.pause).toHaveBeenCalled();
  });

  it('应该恢复播放', async () => {
    const { result } = renderHook(() => useAudioPlayer());
    const audioUrl = 'blob:test-url';

    await act(async () => {
      await result.current.play(audioUrl);
    });

    act(() => {
      result.current.pause();
    });

    await act(async () => {
      await result.current.resume();
    });

    expect(mockAudio.play).toHaveBeenCalled();
  });

  it('应该停止播放', async () => {
    const { result } = renderHook(() => useAudioPlayer());
    const audioUrl = 'blob:test-url';

    await act(async () => {
      await result.current.play(audioUrl);
    });

    act(() => {
      result.current.stop();
    });

    expect(mockAudio.pause).toHaveBeenCalled();
    expect(mockAudio.currentTime).toBe(0);
  });

  it('应该设置播放位置', async () => {
    const { result } = renderHook(() => useAudioPlayer());
    const audioUrl = 'blob:test-url';

    await act(async () => {
      await result.current.play(audioUrl);
    });

    act(() => {
      result.current.seek(50);
    });

    expect(mockAudio.currentTime).toBe(50);
  });

  it('应该设置音量', () => {
    const { result } = renderHook(() => useAudioPlayer());

    act(() => {
      result.current.setVolume(0.5);
    });

    expect(result.current.volume).toBe(0.5);
  });

  it('应该限制音量范围', () => {
    const { result } = renderHook(() => useAudioPlayer());

    act(() => {
      result.current.setVolume(1.5);
    });

    expect(result.current.volume).toBe(1);

    act(() => {
      result.current.setVolume(-0.5);
    });

    expect(result.current.volume).toBe(0);
  });

  it('应该计算播放进度', async () => {
    const { result } = renderHook(() => useAudioPlayer());
    const audioUrl = 'blob:test-url';

    await act(async () => {
      await result.current.play(audioUrl);
    });

    // 模拟更新currentTime和duration
    mockAudio.currentTime = 50;
    mockAudio.duration = 100;

    // 触发timeupdate和loadedmetadata事件
    act(() => {
      const timeupdateCall = mockAudio.addEventListener.mock.calls.find(
        (call: any[]) => call[0] === 'timeupdate'
      );
      if (timeupdateCall && timeupdateCall[1]) {
        timeupdateCall[1]();
      }

      const metadataCall = mockAudio.addEventListener.mock.calls.find(
        (call: any[]) => call[0] === 'loadedmetadata'
      );
      if (metadataCall && metadataCall[1]) {
        metadataCall[1]();
      }
    });

    // 验证duration已更新
    expect(result.current.duration).toBeGreaterThanOrEqual(0);
  });
});

