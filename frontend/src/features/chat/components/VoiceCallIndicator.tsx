import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import './VoiceCallIndicator.css';
import { logger } from '@/utils/logger';

const log = logger.withTag('VoiceCallIndicator');

/**
 * 语音通话指示器组件属性
 */
interface VoiceCallIndicatorProps {
  /** 用户音频频率数据（用于可视化） */
  userFrequencyData?: Uint8Array | null;
  /** 助手音频频率数据（用于可视化） */
  assistantFrequencyData?: Uint8Array | null;
}

/**
 * 现代频谱柱状图可视化组件
 *
 * 类似 Apple Music / Spotify 风格的音频可视化
 * 特点：流畅动画、渐变色彩、发光效果、镜像对称
 */
export const VoiceWaveform: React.FC<{ 
  frequencyData: Uint8Array | null; 
  color: string;
  isActive?: boolean;
  isConnecting?: boolean;
}> = ({ frequencyData, color, isActive = true, isConnecting = false }) => {
  const animationFrameRef = useRef<number | null>(null);
  const [bars, setBars] = useState<number[]>(Array(18).fill(0));
  const smoothedBarsRef = useRef<number[]>(Array(18).fill(0));
  const timeRef = useRef<number>(0);
  
  // 连接动画（正在连接时）
  const updateConnectingAnimation = useCallback(() => {
    timeRef.current += 0.04; // 控制移动速度
    const barCount = 18;
    const dotCount = 3; // 三个白点
    const dotSpacing = 3; // 点之间的间距（柱子索引）- 减小间距
    
    // 计算第一个点的位置（循环移动，范围：0 到 barCount + dotSpacing）
    const cycleLength = barCount + dotSpacing;
    const firstDotPosition = (timeRef.current * 1.5) % cycleLength;
    
    const newBars = Array(barCount).fill(0).map((_, i) => {
      // 计算每个点应该亮起的位置
      let isLit = false;
      for (let dotIndex = 0; dotIndex < dotCount; dotIndex++) {
        let dotPosition = firstDotPosition + dotIndex * dotSpacing;

        // 处理循环：如果位置超过总数，从左边开始
        if (dotPosition >= barCount) {
          dotPosition = dotPosition - barCount;
        }
        
        // 检查这个点是否在当前柱子位置
        if (Math.abs(i - dotPosition) < 0.5) {
          isLit = true;
          break;
      }
    }

      // 如果这个位置应该亮起，设置较高的高度；否则保持很低
      return isLit ? 0.4 : 0.08; // 亮起的高度降低到0.4，暗着的高度保持0.08
    });
    
    setBars(newBars);
    
    if (isActive && isConnecting) {
      animationFrameRef.current = requestAnimationFrame(updateConnectingAnimation);
    }
  }, [isActive, isConnecting]);

  // Idle 动画（等待音频时）
  const updateIdleAnimation = useCallback(() => {
    timeRef.current += 0.03;
    const newBars = Array(18).fill(0).map((_, i) => {
      // 创建微妙的波浪效果
      const wave1 = Math.sin(timeRef.current + i * 0.25) * 0.15;
      const wave2 = Math.sin(timeRef.current * 1.2 + i * 0.15) * 0.1;
      return Math.max(0.08, (wave1 + wave2 + 0.5) * 0.2);
    });
    setBars(newBars);

    if (isActive && (!frequencyData || frequencyData.length === 0) && !isConnecting) {
      animationFrameRef.current = requestAnimationFrame(updateIdleAnimation);
    }
  }, [isActive, frequencyData, isConnecting]);

  // 实时音频可视化
  const updateVisualization = useCallback(() => {
    if (!frequencyData || frequencyData.length === 0) {
      updateIdleAnimation();
      return;
    }

    const barCount = 18;
    const newBars: number[] = [];

    // 将频率数据映射到柱状图
    for (let i = 0; i < barCount; i++) {
      // 使用对数分布，低频占更多柱子（更符合人耳感知）
      const freqIndex = Math.floor(Math.pow(i / barCount, 1.5) * frequencyData.length);
      const value = frequencyData[freqIndex] / 255;
      
      // 平滑处理（降低平滑系数，提高响应速度）
      const smoothing = 0.4;
      const smoothed = smoothedBarsRef.current[i] * smoothing + value * (1 - smoothing);
      smoothedBarsRef.current[i] = smoothed;
      
      // 添加最小高度，避免完全消失
      newBars.push(Math.max(0.03, smoothed));
    }

    setBars(newBars);

    if (isActive) {
      animationFrameRef.current = requestAnimationFrame(updateVisualization);
    }
  }, [frequencyData, isActive, updateIdleAnimation]);

  useEffect(() => {
    if (!isActive) {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      return;
      }

    // 优先显示连接动画
    if (isConnecting) {
      updateConnectingAnimation();
      return;
    }

    if (frequencyData && frequencyData.length > 0) {
      updateVisualization();
    } else {
      updateIdleAnimation();
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
    };
  }, [isActive, isConnecting, frequencyData, updateVisualization, updateIdleAnimation, updateConnectingAnimation]);

  // 根据颜色生成渐变
  const getGradientStops = (baseColor: string) => {
    // 将 hex 颜色转换为 RGB
    const r = parseInt(baseColor.slice(1, 3), 16);
    const g = parseInt(baseColor.slice(3, 5), 16);
    const b = parseInt(baseColor.slice(5, 7), 16);
    
    return {
      light: `rgba(${r}, ${g}, ${b}, 0.9)`,
      medium: `rgba(${r}, ${g}, ${b}, 0.7)`,
      dark: `rgba(${r}, ${g}, ${b}, 0.4)`,
    };
  };

  const gradient = getGradientStops(color);
  const gradientId = `barGradient-${color.replace('#', '')}`;
  const glowId = `barGlow-${color.replace('#', '')}`;

  return (
    <div className="modern-waveform-container">
      <svg className="modern-waveform-svg" viewBox="0 0 180 40" preserveAspectRatio="xMidYMid meet">
        <defs>
          {/* 垂直渐变：从上到下颜色变深 */}
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={gradient.light} />
            <stop offset="50%" stopColor={gradient.medium} />
            <stop offset="100%" stopColor={gradient.dark} />
          </linearGradient>
          
          {/* 发光效果 */}
          <filter id={glowId} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="1.5" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* 绘制对称的柱状图 */}
        {bars.map((height, index) => {
          const barWidth = 4;
          const gap = 3;
          const x = index * (barWidth + gap) + gap;
          const centerY = 20;
          const barHeight = height * 18; // 最大高度18px（上下各18px）
          
          return (
            <rect
              key={index}
              x={x}
              y={centerY - barHeight}
              width={barWidth}
              height={barHeight * 2}
              rx={barWidth / 2} // 圆角半径 = 宽度的一半，形成胶囊形状
              ry={barWidth / 2}
              fill={`url(#${gradientId})`}
              filter={`url(#${glowId})`}
              className="spectrum-bar"
            />
          );
        })}
      </svg>
    </div>
  );
};

/**
 * 语音通话指示器组件
 *
 * 只显示声纹指示器。
 */
export const VoiceCallIndicator: React.FC<VoiceCallIndicatorProps> = ({
  userFrequencyData,
  assistantFrequencyData,
}) => {
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
      log.error('计算音频强度失败:', err);
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
    
    // 开发环境下的音频监控（已节流）
    if (process.env.NODE_ENV === 'development') {
      const now = Date.now();
      if (now - lastLogTimeRef.current >= LOG_THROTTLE_MS) {
        lastLogTimeRef.current = now;
        if (hasUser || hasAssistant) {
          log.debug(`🎤 音频: 用户 ${userInt.toFixed(2)} | 助手 ${assistantInt.toFixed(2)}`);
        }
      }
    }
    
    return {
      activeFrequencyData: activeData,
      activeColor: activeCol,
    };
  }, [userFrequencyData, assistantFrequencyData, getAudioIntensity]);

  return (
    <div className="voice-call-indicator">
          <div className="voice-waveforms">
            <VoiceWaveform 
              frequencyData={activeFrequencyData ?? null} 
              color={activeColor}
              isActive={true}
            />
      </div>
    </div>
  );
};

