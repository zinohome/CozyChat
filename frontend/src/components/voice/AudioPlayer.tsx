import React from 'react';
import { Button, Slider, Space, Typography } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, StopOutlined } from '@ant-design/icons';
import { useAudioPlayer } from '@/hooks/useAudioPlayer';

const { Text } = Typography;

/**
 * 音频播放组件属性
 */
interface AudioPlayerProps {
  /** 音频URL或Blob */
  audioUrl: string | Blob | null;
  /** 是否自动播放 */
  autoPlay?: boolean;
  /** 是否显示进度条 */
  showProgress?: boolean;
  /** 是否显示音量控制 */
  showVolume?: boolean;
}

/**
 * 音频播放组件
 *
 * 提供音频播放功能，支持播放、暂停、停止、进度控制等操作。
 */
export const AudioPlayer: React.FC<AudioPlayerProps> = ({
  audioUrl,
  autoPlay = false,
  showProgress = true,
  showVolume = true,
}) => {
  const {
    status,
    isPlaying,
    currentTime,
    duration,
    volume,
    progress,
    play,
    pause,
    resume,
    stop,
    seek,
    setVolume,
    error,
  } = useAudioPlayer();

  // 自动播放
  React.useEffect(() => {
    if (audioUrl && autoPlay && status === 'idle') {
      play(audioUrl);
    }
  }, [audioUrl, autoPlay, status, play]);

  /**
   * 格式化时长
   */
  const formatDuration = (seconds: number): string => {
    if (isNaN(seconds)) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  /**
   * 处理播放/暂停
   */
  const handlePlayPause = () => {
    if (!audioUrl) return;

    if (status === 'idle' || status === 'stopped') {
      play(audioUrl);
    } else if (status === 'playing') {
      pause();
    } else if (status === 'paused') {
      resume();
    }
  };

  /**
   * 处理进度条变化
   */
  const handleProgressChange = (value: number) => {
    const time = (value / 100) * duration;
    seek(time);
  };

  /**
   * 处理音量变化
   */
  const handleVolumeChange = (value: number) => {
    setVolume(value / 100);
  };

  if (!audioUrl) {
    return null;
  }

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Space>
        <Button
          type="primary"
          icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
          onClick={handlePlayPause}
          disabled={!audioUrl}
        >
          {isPlaying ? '暂停' : '播放'}
        </Button>
        <Button icon={<StopOutlined />} onClick={stop} disabled={status === 'idle'}>
          停止
        </Button>
        <Text type="secondary">
          {formatDuration(currentTime)} / {formatDuration(duration)}
        </Text>
      </Space>

      {showProgress && (
        <div>
          <Slider
            value={progress * 100}
            onChange={handleProgressChange}
            disabled={status === 'idle'}
          />
        </div>
      )}

      {showVolume && (
        <Space>
          <Text type="secondary">音量:</Text>
          <Slider
            value={volume * 100}
            onChange={handleVolumeChange}
            style={{ width: 150 }}
            min={0}
            max={100}
          />
        </Space>
      )}

      {error && <Text type="danger">{error}</Text>}
    </Space>
  );
};

