import React, { useEffect, useState, useRef, useMemo } from 'react';
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
 * 声纹可视化组件 - 水波纹样式
 * 
 * 根据音频强度绘制水波纹效果
 */
const VoiceWaveform: React.FC<{ frequencyData: Uint8Array | null; color: string }> = ({ frequencyData, color }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  const rippleRef = useRef<{ radius: number; opacity: number; speed: number }[]>([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const maxRadius = Math.min(width, height) / 2 - 2;

    // 计算音频强度
    const getAudioIntensity = (): number => {
      if (!frequencyData || frequencyData.length === 0) return 0;
      
      let totalIntensity = 0;
      for (let i = 0; i < frequencyData.length; i++) {
        totalIntensity += frequencyData[i];
      }
      return totalIntensity / frequencyData.length / 255; // 0-1
    };

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      const intensity = getAudioIntensity();
      const hasSound = intensity > 0.05; // 阈值，低于此值认为没有声音

      if (hasSound) {
        // 有声音时，创建新的波纹
        if (rippleRef.current.length === 0 || rippleRef.current[rippleRef.current.length - 1].radius > 10) {
          rippleRef.current.push({
            radius: 0,
            opacity: 0.8,
            speed: 2 + intensity * 3, // 根据强度调整速度
          });
        }

        // 限制波纹数量
        if (rippleRef.current.length > 3) {
          rippleRef.current.shift();
        }

        // 更新和绘制波纹
        for (let i = rippleRef.current.length - 1; i >= 0; i--) {
          const ripple = rippleRef.current[i];
          
          // 更新波纹
          ripple.radius += ripple.speed;
          ripple.opacity = Math.max(0, 0.8 - (ripple.radius / maxRadius) * 0.8);

          // 如果波纹超出范围，移除
          if (ripple.radius > maxRadius || ripple.opacity <= 0) {
            rippleRef.current.splice(i, 1);
            continue;
          }

          // 绘制波纹
          ctx.beginPath();
          ctx.arc(centerX, centerY, ripple.radius, 0, Math.PI * 2);
          ctx.strokeStyle = color;
          ctx.globalAlpha = ripple.opacity;
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        ctx.globalAlpha = 1;
      } else {
        // 没有声音时，清空波纹
        rippleRef.current = [];
      }

      animationFrameRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [frequencyData, color]);

  return (
    <canvas
      ref={canvasRef}
      width={120}
      height={16}
      style={{ display: 'block' }}
    />
  );
};

/**
 * 语音通话指示器组件
 *
 * 显示语音通话状态、时长和结束按钮。
 */
export const VoiceCallIndicator: React.FC<VoiceCallIndicatorProps> = ({
  onEndCall,
  sessionId,
  personalityId,
  userFrequencyData,
  assistantFrequencyData,
}) => {
  const { voiceCallStartTime } = useChatStore();
  const [duration, setDuration] = useState(0);

  // 计算音频强度，判断是否有声音
  const getAudioIntensity = useCallback((frequencyData: Uint8Array | null | undefined): number => {
    if (!frequencyData || frequencyData.length === 0) return 0;
    let totalIntensity = 0;
    for (let i = 0; i < frequencyData.length; i++) {
      totalIntensity += frequencyData[i];
    }
    return totalIntensity / frequencyData.length / 255; // 0-1
  }, []);
  
  const userIntensity = getAudioIntensity(userFrequencyData);
  const assistantIntensity = getAudioIntensity(assistantFrequencyData);
  const hasUserSound = userIntensity > 0.05; // 阈值 5%
  const hasAssistantSound = assistantIntensity > 0.05; // 阈值 5%
  
  // 决定显示哪个声纹：优先显示有声音的，如果都有声音则显示用户的
  const activeFrequencyData = hasUserSound ? userFrequencyData : (hasAssistantSound ? assistantFrequencyData : null);
  const activeColor = hasUserSound ? '#52c41a' : (hasAssistantSound ? '#ff4d4f' : '#52c41a');

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
            {activeFrequencyData && (
              <VoiceWaveform frequencyData={activeFrequencyData} color={activeColor} />
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

