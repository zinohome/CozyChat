import React, { useEffect, useState, useRef, useMemo, useCallback } from 'react';
import { PhoneOutlined } from '@ant-design/icons';
import { useChatStore, getVoiceCallDuration } from '@/store/slices/chatSlice';
import './VoiceCallIndicator.css';

/**
 * 语音通话指示器组件属性
 */
interface VoiceCallIndicatorProps {
  /** 结束通话回调 */
  onEndCall: () => void;
  /** 会话ID */
  sessionId?: string;
  /** 人格ID */
  personalityId?: string;
  /** 用户音频频率数据（用于可视化） */
  userFrequencyData?: Uint8Array | null;
  /** 助手音频频率数据（用于可视化） */
  assistantFrequencyData?: Uint8Array | null;
}

/**
 * 格式化通话时长（MM:SS）
 *
 * @param seconds 秒数
 * @returns 格式化的时长字符串
 */
function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

/**
 * 声纹可视化组件 - SVG 波形路径样式（基于 FastRTC）
 * 
 * 使用 SVG 路径绘制多层波形，支持渐变和发光效果
 */
const VoiceWaveform: React.FC<{ 
  frequencyData: Uint8Array | null; 
  color: string;
  isActive?: boolean;
}> = ({ frequencyData, color, isActive = true }) => {
  const waveContainerRef = useRef<HTMLDivElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  const idleAnimationFrameRef = useRef<number | null>(null);
  const timeRef = useRef<number>(0);
  
  // 波形参数
  const numBands = 16; // 波形条数
  const waveAmplitudesRef = useRef<number[]>(new Array(numBands).fill(0));
  const waveOffsetsRef = useRef<number[]>(new Array(numBands).fill(0));

  // 生成波形路径
  const generateWavePath = useCallback((waveIndex: number, width: number, height: number): string => {
    const centerY = height / 2;
    const points = 100;
    let path = `M 0 ${centerY}`;

    for (let i = 0; i <= points; i++) {
      const x = (i / points) * width;
      const normalizedX = (i / points) * Math.PI * 4;

      const frequency = 1 + waveIndex * 0.3;
      const phase = waveOffsetsRef.current[waveIndex] || 0;
      const baseAmplitude = 20;

      // 计算振幅（使用多个波形的加权平均）
      let amplitude = 0;
      for (let j = 0; j < Math.min(4, waveAmplitudesRef.current.length); j++) {
        const weight = 1 / (j + 1);
        amplitude += (waveAmplitudesRef.current[j] || 0) * weight;
      }
      amplitude = amplitude * baseAmplitude * (0.6 + waveIndex * 0.1);

      // 正弦波 + 余弦波组合
      const sineWave = Math.sin(normalizedX * frequency + phase) * amplitude;
      const cosineWave = Math.cos(normalizedX * frequency * 1.3 + phase * 0.7) * amplitude * 0.3;

      const y = centerY + sineWave + cosineWave;

      if (i === 0) {
        path = `M ${x} ${y}`;
      } else {
        path += ` L ${x} ${y}`;
      }
    }

    return path;
  }, []);

  // 更新波形路径
  const updateWavePaths = useCallback(() => {
    if (!waveContainerRef.current) return;

    const waves = waveContainerRef.current.querySelectorAll('.wave-path');
    const width = waveContainerRef.current.clientWidth || 200;
    const height = 64;

    waves.forEach((wave, waveIndex) => {
      const path = generateWavePath(waveIndex, width, height);
      (wave as SVGPathElement).setAttribute('d', path);
    });
  }, [generateWavePath]);

  // Idle 动画（等待连接时）
  const updateIdleVisualization = useCallback(() => {
    timeRef.current += 0.012;

    for (let i = 0; i < numBands; i++) {
      const baseAmplitude = 0.15 + Math.sin(timeRef.current * 0.5 + i * 0.3) * 0.05;
      waveAmplitudesRef.current[i] = baseAmplitude;
      waveOffsetsRef.current[i] = timeRef.current * (0.3 + i * 0.05);
    }

    updateWavePaths();

    if (!isActive || !frequencyData) {
      idleAnimationFrameRef.current = requestAnimationFrame(updateIdleVisualization);
    }
  }, [isActive, frequencyData, updateWavePaths, numBands]);

  // 实时音频可视化
  const updateVisualization = useCallback(() => {
    if (!frequencyData || !(frequencyData instanceof Uint8Array) || frequencyData.length === 0) {
      // 没有数据时，切换到 idle 动画
      if (isActive) {
        updateIdleVisualization();
      }
      return;
    }

    timeRef.current += 0.016;

    // 根据频率数据更新波形振幅
    for (let i = 0; i < numBands; i++) {
      const freqIndex = Math.floor((i / numBands) * frequencyData.length);
      const amplitude = (frequencyData[freqIndex] / 255) * 0.8 + 0.2;
      waveAmplitudesRef.current[i] = amplitude;
      waveOffsetsRef.current[i] = timeRef.current * (0.5 + i * 0.1);
    }

    updateWavePaths();

    if (isActive) {
      animationFrameRef.current = requestAnimationFrame(updateVisualization);
    }
  }, [frequencyData, isActive, updateWavePaths, numBands, updateIdleVisualization]);

  useEffect(() => {
    if (!isActive) {
      // 停止所有动画
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      if (idleAnimationFrameRef.current) {
        cancelAnimationFrame(idleAnimationFrameRef.current);
        idleAnimationFrameRef.current = null;
      }
      return;
    }

    // 初始化波形数据
    waveAmplitudesRef.current = new Array(numBands).fill(0);
    waveOffsetsRef.current = new Array(numBands).fill(0);

    if (frequencyData && frequencyData.length > 0) {
      // 有音频数据，启动实时可视化
      if (idleAnimationFrameRef.current) {
        cancelAnimationFrame(idleAnimationFrameRef.current);
        idleAnimationFrameRef.current = null;
      }
      updateVisualization();
    } else {
      // 没有音频数据，启动 idle 动画
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      updateIdleVisualization();
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      if (idleAnimationFrameRef.current) {
        cancelAnimationFrame(idleAnimationFrameRef.current);
        idleAnimationFrameRef.current = null;
      }
    };
  }, [isActive, frequencyData, updateVisualization, updateIdleVisualization, numBands]);

  // 生成渐变 ID（基于颜色）
  const gradientId1 = `waveGradient1-${color.replace('#', '')}`;
  const gradientId2 = `waveGradient2-${color.replace('#', '')}`;
  const gradientId3 = `waveGradient3-${color.replace('#', '')}`;

  return (
    <div className="voice-waveform-container" ref={waveContainerRef}>
      <svg className="voice-waveform-svg" viewBox="0 0 200 64" preserveAspectRatio="none">
        <defs>
          <linearGradient id={gradientId1} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={color} stopOpacity="0.8" />
            <stop offset="50%" stopColor={color} stopOpacity="0.9" />
            <stop offset="100%" stopColor={color} stopOpacity="0.8" />
          </linearGradient>
          <linearGradient id={gradientId2} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={color} stopOpacity="0.6" />
            <stop offset="50%" stopColor={color} stopOpacity="0.7" />
            <stop offset="100%" stopColor={color} stopOpacity="0.6" />
          </linearGradient>
          <linearGradient id={gradientId3} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={color} stopOpacity="0.4" />
            <stop offset="50%" stopColor={color} stopOpacity="0.5" />
            <stop offset="100%" stopColor={color} stopOpacity="0.4" />
          </linearGradient>
          <filter id={`glow-${color.replace('#', '')}`}>
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* 3层波形叠加，创建深度效果 */}
        <path
          className="wave-path wave-layer-3"
          stroke={`url(#${gradientId3})`}
          strokeWidth="1.5"
          fill="none"
          filter={`url(#glow-${color.replace('#', '')})`}
        />
        <path
          className="wave-path wave-layer-2"
          stroke={`url(#${gradientId2})`}
          strokeWidth="2"
          fill="none"
          filter={`url(#glow-${color.replace('#', '')})`}
        />
        <path
          className="wave-path wave-layer-1"
          stroke={`url(#${gradientId1})`}
          strokeWidth="2.5"
          fill="none"
          filter={`url(#glow-${color.replace('#', '')})`}
        />
      </svg>
    </div>
  );
};

/**
 * 语音通话指示器组件
 *
 * 显示语音通话状态、时长和结束按钮。
 */
export const VoiceCallIndicator: React.FC<VoiceCallIndicatorProps> = ({
  onEndCall,
  userFrequencyData,
  assistantFrequencyData,
}) => {
  const { voiceCallStartTime } = useChatStore();
  const [duration, setDuration] = useState(0);

  // 计算音频强度，判断是否有声音
  const getAudioIntensity = useCallback((frequencyData: Uint8Array | null | undefined): number => {
    if (!frequencyData || !(frequencyData instanceof Uint8Array) || frequencyData.length === 0) {
      return 0;
    }
    try {
      let totalIntensity = 0;
      for (let i = 0; i < frequencyData.length; i++) {
        totalIntensity += frequencyData[i];
      }
      return totalIntensity / frequencyData.length / 255; // 0-1
    } catch (err) {
      console.error('计算音频强度失败:', err);
      return 0;
    }
  }, []);
  
  // 节流日志输出（每1秒最多输出一次）
  const lastLogTimeRef = useRef<number>(0);
  const LOG_THROTTLE_MS = 1000;
  
  // 使用 useMemo 计算音频强度和声纹显示
  const { activeFrequencyData, activeColor } = useMemo(() => {
    const userInt = getAudioIntensity(userFrequencyData);
    const assistantInt = getAudioIntensity(assistantFrequencyData);
    // 降低阈值，提高灵敏度（从5%降到3%）
    const hasUser = userInt > 0.03; // 阈值 3%
    const hasAssistant = assistantInt > 0.03; // 阈值 3%
    
    // 决定显示哪个声纹：优先显示有声音的，如果都有声音则显示用户的
    const activeData = hasUser ? userFrequencyData : (hasAssistant ? assistantFrequencyData : null);
    const activeCol = hasUser ? '#52c41a' : (hasAssistant ? '#ff4d4f' : '#52c41a');
    
    // 节流调试日志（每1秒最多输出一次）
    if (process.env.NODE_ENV === 'development') {
      const now = Date.now();
      if (now - lastLogTimeRef.current >= LOG_THROTTLE_MS) {
        lastLogTimeRef.current = now;
      console.log('VoiceCallIndicator: 音频强度', {
        userIntensity: userInt.toFixed(3),
        assistantIntensity: assistantInt.toFixed(3),
        hasUserSound: hasUser,
        hasAssistantSound: hasAssistant,
        hasActiveData: !!activeData,
      });
      }
    }
    
    return {
      activeFrequencyData: activeData,
      activeColor: activeCol,
    };
  }, [userFrequencyData, assistantFrequencyData, getAudioIntensity]);

  // 更新通话时长
  useEffect(() => {
    if (!voiceCallStartTime) {
      setDuration(0);
      return;
    }

    const interval = setInterval(() => {
      setDuration(getVoiceCallDuration(voiceCallStartTime));
    }, 1000); // 每秒更新一次

    return () => clearInterval(interval);
  }, [voiceCallStartTime]);


  return (
    <div className="voice-call-indicator">
      <div className="voice-call-indicator-content">
        {/* 左侧：图标和状态 */}
        <div className="voice-call-indicator-left">
          <PhoneOutlined className="voice-call-icon" />
          <span className="voice-call-status">语音通话中</span>
        </div>

        {/* 中间：声纹和通话时长 */}
        <div className="voice-call-indicator-center">
          <div className="voice-waveforms">
            {/* 只有在有音频数据时才显示波形 */}
            {activeFrequencyData ? (
            <VoiceWaveform 
                frequencyData={activeFrequencyData} 
              color={activeColor}
              isActive={true}
            />
            ) : (
              <div style={{ width: '200px', height: '64px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-tertiary)', fontSize: '12px' }}>
                等待音频...
              </div>
            )}
          </div>
          <span className="voice-call-duration">{formatDuration(duration)}</span>
        </div>

        {/* 右侧：结束通话按钮 */}
        <div className="voice-call-indicator-right">
          <button
            type="button"
            className="voice-call-end-button"
            onClick={onEndCall}
            title="结束通话"
          >
            {/* 挂断电话图标 */}
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
              <path fill="#fff" d="M15.897 9c.125.867.207 2.053-.182 2.507c-.643.751-4.714.751-4.714-.751c0-.756.67-1.252.027-2.003c-.632-.738-1.766-.75-3.027-.751s-2.394.012-3.027.751c-.643.751.027 1.247.027 2.003c0 1.501-4.071 1.501-4.714.751C-.102 11.053-.02 9.867.105 9c.096-.579.339-1.203 1.118-2c1.168-1.09 2.935-1.98 6.716-2h.126c3.781.019 5.548.91 6.716 2c.778.797 1.022 1.421 1.118 2z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

