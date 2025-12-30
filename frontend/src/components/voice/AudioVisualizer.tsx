import React, { useEffect, useRef } from 'react';
import { useAudioVisualization } from '@/hooks/useAudioVisualization';

/**
 * 音频可视化组件属性
 */
interface AudioVisualizerProps {
  /** 音频元素或流 */
  audioSource: HTMLAudioElement | MediaStream | null;
  /** 可视化类型 */
  type?: 'frequency' | 'waveform' | 'both';
  /** 宽度 */
  width?: number;
  /** 高度 */
  height?: number;
  /** 颜色 */
  color?: string;
}

/**
 * 音频可视化组件
 *
 * 使用Canvas绘制音频波形或频谱图。
 */
export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
  audioSource,
  type = 'both',
  width = 400,
  height = 100,
  color = '#1890ff',
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { frequencyData, timeData, start, stop, isActive } = useAudioVisualization();

  // 启动可视化
  useEffect(() => {
    if (audioSource && !isActive) {
      start(audioSource);
    }

    return () => {
      if (isActive) {
        stop();
      }
    };
  }, [audioSource, isActive, start, stop]);

  // 绘制可视化
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      if (type === 'frequency' || type === 'both') {
        if (frequencyData) {
          const barWidth = width / frequencyData.length;
          ctx.fillStyle = color;

          for (let i = 0; i < frequencyData.length; i++) {
            const barHeight = (frequencyData[i] / 255) * height;
            ctx.fillRect(i * barWidth, height - barHeight, barWidth - 1, barHeight);
          }
        }
      }

      if (type === 'waveform' || type === 'both') {
        if (timeData) {
          ctx.strokeStyle = color;
          ctx.lineWidth = 2;
          ctx.beginPath();

          const sliceWidth = width / timeData.length;
          let x = 0;

          for (let i = 0; i < timeData.length; i++) {
            const v = timeData[i] / 128.0;
            const y = (v * height) / 2;

            if (i === 0) {
              ctx.moveTo(x, y);
            } else {
              ctx.lineTo(x, y);
            }

            x += sliceWidth;
          }

          ctx.stroke();
        }
      }

      if (isActive) {
        requestAnimationFrame(draw);
      }
    };

    if (isActive) {
      draw();
    }
  }, [frequencyData, timeData, isActive, type, width, height, color]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{ display: 'block', background: '#f5f5f5', borderRadius: '4px' }}
    />
  );
};

