/**
 * 语音相关类型定义
 */

/**
 * STT转录请求
 */
export interface TranscriptionRequest {
  model?: string;
  language?: string;
  personality_id?: string;
}

/**
 * STT转录响应
 */
export interface TranscriptionResponse {
  text: string;
}

/**
 * TTS语音合成请求
 */
export interface SpeechRequest {
  model?: string;
  input: string;
  voice?: 'alloy' | 'echo' | 'fable' | 'onyx' | 'nova' | 'shimmer';
  speed?: number;
  personality_id?: string;
}

/**
 * 音频格式
 */
export type AudioFormat = 'mp3' | 'opus' | 'aac' | 'flac' | 'wav' | 'pcm';

/**
 * 录音状态
 */
export type RecordingStatus = 'idle' | 'recording' | 'paused' | 'stopped';

/**
 * 播放状态
 */
export type PlaybackStatus = 'idle' | 'playing' | 'paused' | 'stopped';

/**
 * 音频可视化数据
 */
export interface AudioVisualizationData {
  frequencyData: Uint8Array;
  timeData: Uint8Array;
}

