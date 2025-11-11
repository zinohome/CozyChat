import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AudioRecorder } from './AudioRecorder';

// Mock useAudioRecorder
vi.mock('@/hooks/useAudioRecorder', () => ({
  useAudioRecorder: vi.fn(() => ({
    status: 'idle',
    isRecording: false,
    duration: 0,
    audioBlob: null,
    audioUrl: null,
    startRecording: vi.fn(),
    stopRecording: vi.fn(),
    pauseRecording: vi.fn(),
    resumeRecording: vi.fn(),
    clearRecording: vi.fn(),
    error: null,
  })),
}));

describe('AudioRecorder', () => {
  const mockOnRecordComplete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('应该渲染开始录音按钮', () => {
    render(<AudioRecorder onRecordComplete={mockOnRecordComplete} />);
    expect(screen.getByText('开始录音')).toBeInTheDocument();
  });

  it('应该显示录音时长', async () => {
    const { useAudioRecorder } = await import('@/hooks/useAudioRecorder');
    vi.mocked(useAudioRecorder).mockReturnValue({
      status: 'recording',
      isRecording: true,
      duration: 65,
      audioBlob: null,
      audioUrl: null,
      startRecording: vi.fn(),
      stopRecording: vi.fn(),
      pauseRecording: vi.fn(),
      resumeRecording: vi.fn(),
      clearRecording: vi.fn(),
      error: null,
    });

    render(<AudioRecorder onRecordComplete={mockOnRecordComplete} />);
    expect(screen.getByText(/录音时长: 01:05/)).toBeInTheDocument();
  });

  it('应该在禁用时禁用按钮', () => {
    render(<AudioRecorder onRecordComplete={mockOnRecordComplete} disabled />);
    const button = screen.getByText('开始录音').closest('button');
    expect(button).toBeDisabled();
  });
});

