import React from 'react';
import { Button, Space, Typography, message } from 'antd';
import { AudioOutlined, PauseOutlined, StopOutlined } from '@ant-design/icons';
import { useAudioRecorder } from '@/hooks/useAudioRecorder';
import { showError } from '@/utils/errorHandler';

const { Text } = Typography;

/**
 * 音频录音组件属性
 */
interface AudioRecorderProps {
  /** 录音完成回调 */
  onRecordComplete?: (audioBlob: Blob) => void;
  /** 是否禁用 */
  disabled?: boolean;
}

/**
 * 音频录音组件
 *
 * 提供录音功能，支持开始、暂停、停止等操作。
 */
export const AudioRecorder: React.FC<AudioRecorderProps> = ({
  onRecordComplete,
  disabled = false,
}) => {
  const {
    status,
    isRecording,
    duration,
    audioBlob,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    clearRecording,
    error,
  } = useAudioRecorder();

  // 显示错误
  React.useEffect(() => {
    if (error) {
      showError(error, '录音失败');
    }
  }, [error]);

  // 录音完成时调用回调
  React.useEffect(() => {
    if (audioBlob && status === 'stopped' && onRecordComplete) {
      onRecordComplete(audioBlob);
    }
  }, [audioBlob, status, onRecordComplete]);

  /**
   * 格式化时长
   */
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  /**
   * 处理开始录音
   */
  const handleStart = async () => {
    await startRecording();
  };

  /**
   * 处理停止录音
   */
  const handleStop = () => {
    stopRecording();
  };

  /**
   * 处理暂停/恢复
   */
  const handlePauseResume = () => {
    if (status === 'recording') {
      pauseRecording();
    } else if (status === 'paused') {
      resumeRecording();
    }
  };

  /**
   * 处理清除
   */
  const handleClear = () => {
    clearRecording();
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Space>
        {status === 'idle' && (
          <Button
            type="primary"
            icon={<AudioOutlined />}
            onClick={handleStart}
            disabled={disabled}
          >
            开始录音
          </Button>
        )}

        {status === 'recording' && (
          <>
            <Button
              type="primary"
              danger
              icon={<StopOutlined />}
              onClick={handleStop}
            >
              停止
            </Button>
            <Button icon={<PauseOutlined />} onClick={handlePauseResume}>
              暂停
            </Button>
          </>
        )}

        {status === 'paused' && (
          <>
            <Button
              type="primary"
              danger
              icon={<StopOutlined />}
              onClick={handleStop}
            >
              停止
            </Button>
            <Button type="primary" onClick={handlePauseResume}>
              继续
            </Button>
          </>
        )}

        {status === 'stopped' && audioBlob && (
          <>
            <Button onClick={handleClear}>清除</Button>
            <Text type="secondary">录音完成 ({formatDuration(duration)})</Text>
          </>
        )}
      </Space>

      {(isRecording || status === 'paused') && (
        <Text type="secondary">录音时长: {formatDuration(duration)}</Text>
      )}
    </Space>
  );
};

