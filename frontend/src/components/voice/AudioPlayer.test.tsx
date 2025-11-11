import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AudioPlayer } from './AudioPlayer';

// Mock useAudioPlayer
const mockPlay = vi.fn();
const mockPause = vi.fn();
const mockResume = vi.fn();
const mockStop = vi.fn();
const mockSeek = vi.fn();
const mockSetVolume = vi.fn();

vi.mock('@/hooks/useAudioPlayer', () => ({
  useAudioPlayer: vi.fn(() => ({
    status: 'idle',
    isPlaying: false,
    currentTime: 0,
    duration: 100,
    volume: 1,
    progress: 0,
    play: mockPlay,
    pause: mockPause,
    resume: mockResume,
    stop: mockStop,
    seek: mockSeek,
    setVolume: mockSetVolume,
    error: null,
  })),
}));

describe('AudioPlayer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('应该不渲染当audioUrl为空', () => {
    const { container } = render(<AudioPlayer audioUrl={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('应该渲染播放器', () => {
    render(<AudioPlayer audioUrl="blob:test-url" />);
    expect(screen.getByRole('button', { name: /播放/i })).toBeInTheDocument();
  });

  it('应该播放音频', async () => {
    const user = userEvent.setup();
    render(<AudioPlayer audioUrl="blob:test-url" />);

    const playButton = screen.getByRole('button', { name: /播放/i });
    await user.click(playButton);

    expect(mockPlay).toHaveBeenCalledWith('blob:test-url');
  });

  it('应该暂停播放', async () => {
    const { useAudioPlayer } = await import('@/hooks/useAudioPlayer');
    vi.mocked(useAudioPlayer).mockReturnValue({
      status: 'playing',
      isPlaying: true,
      currentTime: 50,
      duration: 100,
      volume: 1,
      progress: 0.5,
      play: mockPlay,
      pause: mockPause,
      resume: mockResume,
      stop: mockStop,
      seek: mockSeek,
      setVolume: mockSetVolume,
      error: null,
    });

    const user = userEvent.setup();
    render(<AudioPlayer audioUrl="blob:test-url" />);

    const pauseButton = screen.getByRole('button', { name: /暂停/i });
    await user.click(pauseButton);

    expect(mockPause).toHaveBeenCalled();
  });

  it('应该显示播放进度', () => {
    const { useAudioPlayer } = require('@/hooks/useAudioPlayer');
    vi.mocked(useAudioPlayer).mockReturnValue({
      status: 'playing',
      isPlaying: true,
      currentTime: 30,
      duration: 100,
      volume: 1,
      progress: 0.3,
      play: mockPlay,
      pause: mockPause,
      resume: mockResume,
      stop: mockStop,
      seek: mockSeek,
      setVolume: mockSetVolume,
      error: null,
    });

    render(<AudioPlayer audioUrl="blob:test-url" showProgress />);
    expect(screen.getByText(/00:30/i)).toBeInTheDocument();
  });
});

