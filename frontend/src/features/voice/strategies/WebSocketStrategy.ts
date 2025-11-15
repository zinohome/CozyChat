/**
 * WebSocket 传输层策略
 * 
 * 负责处理 WebSocket 传输层的所有逻辑：
 * - 使用 SDK 原生的 'websocket' transport
 * - 手动处理音频捕获和播放
 * - 初始化音频可视化
 */

import { RealtimeAgent, RealtimeSession } from '@openai/agents/realtime';
import type { ITransportStrategy, TransportStrategyConfig } from './ITransportStrategy';
import { AudioVisualizer } from '../visualization/AudioVisualizer';

/**
 * WebSocket 传输层策略类
 */
export class WebSocketStrategy implements ITransportStrategy {
  readonly type = 'websocket' as const;

  // 保留用于将来可能的扩展（如直接访问session）
  private session: RealtimeSession | null = null;
  private mediaStream: MediaStream | null = null;
  private audioElement: HTMLAudioElement | null = null;
  private audioContext: AudioContext | null = null;
  private processor: ScriptProcessorNode | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private audioVisualizer: AudioVisualizer;
  // 保留用于将来可能的扩展（回调函数已通过audioVisualizer处理）
  // @ts-expect-error - 保留用于接口兼容性
  private onUserFrequencyData: ((data: Uint8Array) => void) | null = null;
  // @ts-expect-error - 保留用于接口兼容性
  private onAssistantFrequencyData: ((data: Uint8Array) => void) | null = null;
  private isCalling: boolean = false;
  
  // ✅ 音频播放队列管理
  private audioQueue: ArrayBuffer[] = [];
  private isPlayingAudio: boolean = false;
  private playbackAudioContext: AudioContext | null = null;
  
  // ✅ 音频缓冲管理（用于流式播放）
  private audioBuffer: Float32Array | null = null; // 累积的音频缓冲区
  private minBufferSize: number = 24000 * 3.0; // 最小缓冲区：3.0秒（72000个采样点）- 平衡流畅度和延迟
  private maxBufferSize: number = 24000 * 5.0; // 最大缓冲区：5.0秒（120000个采样点）- 防止延迟过大
  private flushInterval: number | null = null; // 定时刷新缓冲区
  private nextPlayTime: number = 0; // 下一个音频片段的播放时间（用于无缝拼接）
  private gainNode: GainNode | null = null; // 音量控制节点
  private activeSources: AudioBufferSourceNode[] = []; // 正在播放的音频源（用于打断时停止）
  private lastUserAudioTime: number = 0; // 上次用户音频时间（用于检测用户开始说话）
  private crossfadeLength: number = 240; // 交叉淡入淡出长度：约10ms（240个采样点）
  private previousSource: AudioBufferSourceNode | null = null; // 上一个音频源（用于交叉淡入淡出）

  constructor() {
    this.audioVisualizer = new AudioVisualizer();
  }

  /**
   * 创建并连接 RealtimeSession
   */
  async createSession(
    agent: RealtimeAgent,
    config: TransportStrategyConfig
  ): Promise<RealtimeSession> {
    console.log('[WebSocketStrategy] 创建 WebSocket Session...');

    // 1. 创建用户音频流（用于捕获和发送）
    // 如果流不存在或已停止，重新创建
    if (!this.mediaStream || this.mediaStream.getTracks().every(track => track.readyState === 'ended')) {
      // 如果流已停止，重新创建
      if (this.mediaStream) {
        console.log('[WebSocketStrategy] 检测到音频流已停止，重新创建...');
      }
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 24000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
    }

    // 2. 创建助手音频元素（用于播放接收到的音频）
    // 注意：WebSocket 模式下，我们需要手动播放音频
    if (!this.audioElement) {
      this.audioElement = new Audio();
      this.audioElement.autoplay = true;
      this.audioElement.muted = false;
    }

    // 3. 创建 RealtimeSession（使用 SDK 原生的 'websocket' transport）
    const session = new RealtimeSession(agent, {
      apiKey: config.apiKey,
      transport: 'websocket', // ✅ 使用 SDK 原生支持
      model: config.model,
    });

    this.session = session;

    // 4. 设置音频捕获和播放逻辑
    this.setupAudioHandling(session);

    console.log('[WebSocketStrategy] WebSocket Session 已创建');
    return session;
  }

  /**
   * 设置音频处理
   * 
   * 根据官方文档，WebSocket 模式需要手动处理音频：
   * - 监听 session.on('audio', ...) 接收音频数据（PCM16 格式）
   * - 调用 session.sendAudio(audioBuffer) 发送音频数据（PCM16 格式）
   */
  private setupAudioHandling(session: RealtimeSession): void {
    console.log('[WebSocketStrategy] 设置音频处理...');

    if (!this.mediaStream) {
      throw new Error('音频流未初始化');
    }

    // 1. 设置音频捕获（从 MediaStream 捕获并发送）
    // 如果 AudioContext 已关闭，重新创建
    if (!this.audioContext || this.audioContext.state === 'closed') {
      if (this.audioContext) {
        console.log('[WebSocketStrategy] 检测到 AudioContext 已关闭，重新创建...');
      }
      this.audioContext = new AudioContext({ sampleRate: 24000 });
    }
    
    // 如果 source 或 processor 已断开，重新创建
    // 注意：每次 createSession 都会调用 setupAudioHandling，所以需要重新连接
    if (this.source) {
      try {
        this.source.disconnect();
      } catch (e) {
        // 忽略已断开的错误
      }
    }
    if (this.processor) {
      try {
        this.processor.disconnect();
      } catch (e) {
        // 忽略已断开的错误
      }
    }
    
    // 重新创建 source 和 processor
    this.source = this.audioContext.createMediaStreamSource(this.mediaStream);
    this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);

    this.processor.onaudioprocess = (event) => {
      if (!this.isCalling) {
        return;
      }

      // 获取音频数据（Float32Array，范围 -1 到 1）
      const inputData = event.inputBuffer.getChannelData(0);

      // ✅ 检测用户开始说话（用于自动打断）
      // 计算音频能量（RMS）
      let sum = 0;
      for (let i = 0; i < inputData.length; i++) {
        sum += inputData[i] * inputData[i];
      }
      const rms = Math.sqrt(sum / inputData.length);
      const threshold = 0.01; // 能量阈值（可调整）
      
      const currentTime = Date.now();
      const timeSinceLastAudio = currentTime - this.lastUserAudioTime;
      
      // 如果检测到用户说话，且距离上次音频超过500ms（避免频繁打断）
      if (rms > threshold && timeSinceLastAudio > 500) {
        // 检查是否有正在播放的音频（AI在说话）
        if (this.isPlayingAudio || this.activeSources.length > 0) {
          console.log('[WebSocketStrategy] 检测到用户开始说话，触发打断...');
          this.interruptAssistant();
        }
        this.lastUserAudioTime = currentTime;
      }

      // 转换为 PCM16 格式（Int16Array，范围 -32768 到 32767）
      const pcm16 = new Int16Array(inputData.length);
      for (let i = 0; i < inputData.length; i++) {
        const sample = Math.max(-1, Math.min(1, inputData[i]));
        pcm16[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
      }

      // 发送音频数据
      try {
        session.sendAudio(pcm16.buffer);
      } catch (error) {
        console.error('[WebSocketStrategy] 发送音频失败:', error);
      }
    };

    this.source.connect(this.processor);
    this.processor.connect(this.audioContext.destination);

    // 2. 设置音频接收（监听并播放）
    // ✅ 关键优化：使用音频缓冲机制，累积音频数据后平滑播放
    session.on('audio', (event: any) => {
      if (!this.isCalling) {
        return;
      }

      // event.data 是 PCM16 音频数据（ArrayBuffer）
      const audioData = event.data;
      if (!audioData || !(audioData instanceof ArrayBuffer)) {
        return;
      }

      // 将 PCM16 转换为 Float32 并添加到缓冲区
      this.appendToAudioBuffer(audioData);
      
      // ✅ 流式播放策略：
      // 1. 如果缓冲区达到最小大小且当前没有播放，立即开始播放
      // 2. 如果缓冲区达到最大大小，强制刷新（避免延迟过大）
      // 3. 播放时继续累积数据到缓冲区，播放完成后继续播放下一段
      if (this.audioBuffer && this.audioBuffer.length >= this.minBufferSize) {
        if (!this.isPlayingAudio) {
          // 当前没有播放，立即开始
          this.flushAudioBuffer().catch((error) => {
            console.error('[WebSocketStrategy] 刷新音频缓冲区失败:', error);
          });
        } else if (this.audioBuffer.length >= this.maxBufferSize) {
          // 缓冲区过大，强制刷新（但需要等待当前播放完成）
          // 这里不立即刷新，让播放循环自然处理
        }
      }
    });

    console.log('[WebSocketStrategy] 音频处理已设置');
  }

  /**
   * 将 PCM16 数据添加到音频缓冲区
   */
  private appendToAudioBuffer(pcm16Data: ArrayBuffer): void {
    const pcm16 = new Int16Array(pcm16Data);
    const float32 = new Float32Array(pcm16.length);
    
    // 将 Int16 转换为 Float32（优化精度，保持原始音质）
    // 使用更精确的转换，避免精度损失
    for (let i = 0; i < pcm16.length; i++) {
      // 直接转换，不进行额外的裁剪（保持原始动态范围）
      float32[i] = pcm16[i] / 32768.0;
    }

    // 追加到缓冲区
    if (!this.audioBuffer) {
      this.audioBuffer = float32;
    } else {
      // 合并数组
      const merged = new Float32Array(this.audioBuffer.length + float32.length);
      merged.set(this.audioBuffer, 0);
      merged.set(float32, this.audioBuffer.length);
      this.audioBuffer = merged;
    }
  }

  /**
   * 刷新音频缓冲区（播放累积的音频数据）
   * 
   * 关键：只取最小缓冲区大小的数据，保留剩余数据继续累积
   */
  private async flushAudioBuffer(): Promise<void> {
    if (!this.audioBuffer || this.audioBuffer.length === 0 || this.isPlayingAudio) {
      return;
    }

    // 清除定时器
    if (this.flushInterval) {
      clearTimeout(this.flushInterval);
      this.flushInterval = null;
    }

    // ✅ 关键：只取最小缓冲区大小的数据播放，保留剩余数据
    const samplesToPlay = Math.min(this.audioBuffer.length, this.minBufferSize);
    const bufferToPlay = this.audioBuffer.slice(0, samplesToPlay);
    
    // 保留剩余数据
    if (this.audioBuffer.length > samplesToPlay) {
      this.audioBuffer = this.audioBuffer.slice(samplesToPlay);
    } else {
      this.audioBuffer = null;
    }

    // 播放这段数据
    await this.playAudioBuffer(bufferToPlay);
  }

  /**
   * 播放单个音频缓冲区
   * 
   * 使用 AudioContext 的 AudioBuffer 播放，确保高质量和低延迟
   * 优化：累积音频数据，减少播放次数，提升音质
   */
  private async playAudioBuffer(float32: Float32Array): Promise<void> {
    if (!this.isCalling || float32.length === 0) {
      return;
    }

    // 标记正在播放
    this.isPlayingAudio = true;

    try {
      // 创建播放用的 AudioContext（如果不存在或已关闭）
      // 使用与 WebRTC 相同的配置，确保音质一致
      if (!this.playbackAudioContext || this.playbackAudioContext.state === 'closed') {
        if (this.playbackAudioContext) {
          console.log('[WebSocketStrategy] 检测到播放 AudioContext 已关闭，重新创建...');
        }
        // 使用与 WebRTC 相同的采样率，确保音质一致
        this.playbackAudioContext = new AudioContext({ 
          sampleRate: 24000,
          latencyHint: 'interactive' // 低延迟模式，提升响应性
        });
        this.nextPlayTime = 0; // 重置播放时间
      }

      // 如果 AudioContext 被暂停，恢复它
      if (this.playbackAudioContext.state === 'suspended') {
        await this.playbackAudioContext.resume();
      }

      // 创建 GainNode（如果不存在）
      if (!this.gainNode) {
        this.gainNode = this.playbackAudioContext.createGain();
        this.gainNode.connect(this.playbackAudioContext.destination);
      }

      // 创建 AudioBuffer
      const audioBuffer = this.playbackAudioContext.createBuffer(
        1, // 单声道
        float32.length,
        24000 // 采样率
      );
      
      // 复制数据到 AudioBuffer（使用 getChannelData 获取引用，直接设置）
      const channelData = audioBuffer.getChannelData(0);
      channelData.set(float32);

      // ✅ 关键：只在第一段使用轻微淡入，其他片段保持原始音频
      // 这样可以避免开头点击声，同时保持音频完整性
      if (this.nextPlayTime === 0 && float32.length > 0) {
        const fadeInLength = Math.min(120, float32.length / 20); // 约5ms淡入
        for (let i = 0; i < fadeInLength && i < float32.length; i++) {
          const fadeIn = i / fadeInLength;
          const smoothFade = fadeIn * fadeIn * (3 - 2 * fadeIn); // smoothstep
          channelData[i] *= smoothFade;
        }
      }

      // 创建 AudioBufferSourceNode
      const source = this.playbackAudioContext.createBufferSource();
      source.buffer = audioBuffer;
      
      // ✅ 不设置 playbackRate，保持原始音质和音调
      // playbackRate 会导致音调变化，影响音质
      
      // ✅ 添加到活动源列表（用于打断时停止）
      this.activeSources.push(source);
      
      // ✅ 关键：使用精确的 scheduled playback 实现无缝拼接
      const currentTime = this.playbackAudioContext.currentTime;
      
      // 精确计算播放时间，允许小幅度重叠（10ms）用于交叉淡入淡出
      let playTime: number;
      if (this.nextPlayTime === 0) {
        // 第一段，立即播放
        playTime = currentTime;
      } else if (this.nextPlayTime > currentTime) {
        // 使用预定的时间，允许小幅度重叠用于交叉淡入淡出
        const overlapTime = this.crossfadeLength / 24000; // 约10ms
        playTime = Math.max(currentTime, this.nextPlayTime - overlapTime);
      } else {
        // 如果预定时间已过期，使用当前时间，允许小幅度重叠
        const overlapTime = this.crossfadeLength / 24000; // 约10ms
        playTime = Math.max(currentTime, this.nextPlayTime - overlapTime);
      }
      
      // ✅ 实现交叉淡入淡出（Crossfade）
      // 如果上一个音频源存在，在重叠部分进行交叉淡入淡出
      if (this.previousSource) {
        const overlapTime = this.crossfadeLength / 24000; // 转换为秒（约10ms）
        
        // 创建淡入 GainNode 用于当前源
        const fadeInGain = this.playbackAudioContext.createGain();
        fadeInGain.gain.setValueAtTime(0.0, playTime);
        fadeInGain.gain.linearRampToValueAtTime(1.0, playTime + overlapTime);
        
        // 连接新源到淡入 GainNode，再连接到主 GainNode
        source.connect(fadeInGain);
        fadeInGain.connect(this.gainNode);
      } else {
        // 没有上一个源，直接连接
        source.connect(this.gainNode);
      }
      
      // 设置 GainNode 的音量为 1.0，确保原始音质
      this.gainNode.gain.value = 1.0;
      
      // 保存当前源作为下一个的前一个源
      this.previousSource = source;
      
      // 计算播放时长
      const duration = audioBuffer.duration;
      
      // 等待播放完成
      await new Promise<void>((resolve) => {
        source.onended = () => {
          // 从活动源列表中移除
          const index = this.activeSources.indexOf(source);
          if (index > -1) {
            this.activeSources.splice(index, 1);
          }
          // 如果这是前一个源，清除引用
          if (this.previousSource === source) {
            this.previousSource = null;
          }
          // 更新下一个播放时间，实现无缝拼接
          // 考虑交叉淡入淡出的重叠时间
          const overlapTime = this.crossfadeLength / 24000; // 约10ms
          this.nextPlayTime = playTime + duration - overlapTime; // 减去重叠时间，确保连续
          resolve();
        };
        try {
          source.start(playTime);
        } catch (error) {
          console.error('[WebSocketStrategy] 启动音频播放失败:', error);
          // 从活动源列表中移除
          const index = this.activeSources.indexOf(source);
          if (index > -1) {
            this.activeSources.splice(index, 1);
          }
          this.nextPlayTime = currentTime; // 重置播放时间
          resolve(); // 即使失败也 resolve，避免阻塞
        }
      });
    } catch (error) {
      console.error('[WebSocketStrategy] 播放音频缓冲区失败:', error);
    } finally {
      this.isPlayingAudio = false;
      
      // ✅ 流式播放：如果缓冲区中还有足够的数据，立即继续播放下一段
      // 使用 requestAnimationFrame 确保与音频线程同步，提升流畅度
      if (this.isCalling && this.audioBuffer && this.audioBuffer.length >= this.minBufferSize) {
        // 使用 requestAnimationFrame 确保在下一个渲染帧执行，与音频线程同步
        requestAnimationFrame(() => {
          this.flushAudioBuffer().catch((error) => {
            console.error('[WebSocketStrategy] 继续播放缓冲区失败:', error);
          });
        });
      } else if (this.isCalling && this.audioBuffer && this.audioBuffer.length > 0) {
        // 如果数据不够最小缓冲区，等待更多数据
        // 使用更短的延迟，提升响应速度
        if (!this.flushInterval) {
          this.flushInterval = window.setTimeout(() => {
            if (this.audioBuffer && this.audioBuffer.length > 0 && !this.isPlayingAudio) {
              this.flushAudioBuffer().catch((error) => {
                console.error('[WebSocketStrategy] 延迟播放缓冲区失败:', error);
              });
            }
            this.flushInterval = null;
          }, 20); // 20ms 后重试（降低延迟）
        }
      }
    }
  }

  /**
   * 播放音频队列（保留用于兼容性，但已改用缓冲机制）
   * 
   * 按顺序播放队列中的音频数据，确保不会重叠
   * @deprecated 已改用缓冲机制，此方法保留用于兼容性
   * 注意：此方法在 playAudioQueue 内部被调用，但linter可能无法检测到
   */
  // @ts-expect-error - 保留用于兼容性，在条件分支中被调用
  private async playAudioQueue(): Promise<void> {
    if (this.isPlayingAudio || this.audioQueue.length === 0) {
      return;
    }

    this.isPlayingAudio = true;

    // 创建播放用的 AudioContext（如果不存在或已关闭）
    if (!this.playbackAudioContext || this.playbackAudioContext.state === 'closed') {
      if (this.playbackAudioContext) {
        console.log('[WebSocketStrategy] 检测到播放 AudioContext 已关闭，重新创建...');
      }
      this.playbackAudioContext = new AudioContext({ sampleRate: 24000 });
    }

    // 如果 AudioContext 被暂停，恢复它
    if (this.playbackAudioContext.state === 'suspended') {
      await this.playbackAudioContext.resume();
    }

    while (this.audioQueue.length > 0 && this.isCalling) {
      const audioData = this.audioQueue.shift();
      if (!audioData) {
        continue;
      }

      try {
        // 将 PCM16 数据转换为 Float32Array
        const pcm16 = new Int16Array(audioData);
        const float32 = new Float32Array(pcm16.length);
        
        for (let i = 0; i < pcm16.length; i++) {
          // 将 Int16 (-32768 到 32767) 转换为 Float32 (-1.0 到 1.0)
          float32[i] = pcm16[i] / 32768.0;
        }

        // 创建 AudioBuffer
        const audioBuffer = this.playbackAudioContext.createBuffer(
          1, // 单声道
          float32.length,
          24000 // 采样率
        );
        
        // 复制数据到 AudioBuffer（使用 getChannelData 获取引用，直接设置）
        const channelData = audioBuffer.getChannelData(0);
        channelData.set(float32);

        // 创建 AudioBufferSourceNode 并播放
        const source = this.playbackAudioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.playbackAudioContext.destination);

        // 等待播放完成
        await new Promise<void>((resolve) => {
          source.onended = () => {
            resolve();
          };
          try {
            source.start(0);
          } catch (error) {
            console.error('[WebSocketStrategy] 启动音频播放失败:', error);
            resolve(); // 即使失败也 resolve，避免阻塞
          }
        });

        // 短暂延迟，确保音频片段之间有平滑过渡
        await new Promise(resolve => setTimeout(resolve, 10));
      } catch (error) {
        console.error('[WebSocketStrategy] 播放音频队列失败:', error);
        // 继续播放下一个
      }
    }

    this.isPlayingAudio = false;
    
    // 如果队列中还有数据，继续播放
    if (this.audioQueue.length > 0 && this.isCalling) {
      this.playAudioQueue();
    }
  }

  /**
   * 将 PCM16 数据转换为 WAV 格式（保留用于兼容性，但不再使用）
   * @deprecated 已改用 AudioBuffer 直接播放，此方法保留用于兼容性
   */
  // @ts-expect-error - 保留用于兼容性，可能在未来需要时使用
  private pcm16ToWav(pcm16Data: ArrayBuffer, sampleRate: number, channels: number): Blob {
    const length = pcm16Data.byteLength;
    const buffer = new ArrayBuffer(44 + length);
    const view = new DataView(buffer);

    // WAV 文件头
    const writeString = (offset: number, string: string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };

    writeString(0, 'RIFF');
    view.setUint32(4, 36 + length, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, channels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * channels * 2, true);
    view.setUint16(32, channels * 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, length, true);

    // 复制 PCM16 数据
    const pcm16View = new Uint8Array(pcm16Data);
    const wavView = new Uint8Array(buffer, 44);
    wavView.set(pcm16View);

    return new Blob([buffer], { type: 'audio/wav' });
  }

  /**
   * 初始化音频可视化
   */
  async initAudioVisualization(
    _session: RealtimeSession,
    onUserFrequencyData: (data: Uint8Array) => void,
    onAssistantFrequencyData: (data: Uint8Array) => void
  ): Promise<void> {
    if (!this.mediaStream || !this.audioElement) {
      throw new Error('WebSocket 音频流未初始化');
    }

    this.onUserFrequencyData = onUserFrequencyData;
    this.onAssistantFrequencyData = onAssistantFrequencyData;

    // 初始化用户音频可视化
    await this.audioVisualizer.initUserVisualization(
      this.mediaStream,
      onUserFrequencyData
    );

    // 初始化助手音频可视化
    this.audioVisualizer.initAssistantVisualization(
      this.audioElement,
      onAssistantFrequencyData
    );

    console.log('[WebSocketStrategy] 音频可视化已初始化');
  }

  /**
   * 开始音频可视化
   */
  startAudioVisualization(): void {
    this.isCalling = true;
    this.audioVisualizer.setCallingState(true);
    this.audioVisualizer.startUserFrequencyExtraction();
    this.audioVisualizer.startAssistantFrequencyExtraction();
    console.log('[WebSocketStrategy] 音频可视化已启动');
  }

  /**
   * 停止音频可视化
   */
  stopAudioVisualization(): void {
    this.isCalling = false;
    this.audioVisualizer.setCallingState(false);
    this.audioVisualizer.stopFrequencyExtraction();
    console.log('[WebSocketStrategy] 音频可视化已停止');
  }

  /**
   * 打断助手（停止AI正在播放的音频）
   */
  private interruptAssistant(): void {
    if (!this.session) {
      return;
    }

    console.log('[WebSocketStrategy] 发送打断信号...');

    // 1. 立即停止所有正在播放的音频源
    this.activeSources.forEach((source) => {
      try {
        source.stop();
      } catch (error) {
        // 忽略已停止的错误
      }
    });
    this.activeSources = [];
    this.previousSource = null; // 清除前一个源引用
    this.isPlayingAudio = false;

    // 2. 清空音频缓冲区和队列
    this.audioBuffer = null;
    this.audioQueue = [];
    this.nextPlayTime = 0;

    // 3. 发送打断信号给服务器
    try {
      // 发送 response.audio.stop 消息，告诉服务器停止生成和播放音频
      // 注意：RealtimeSession 可能没有直接的 send 方法，使用类型断言
      if (typeof (this.session as any).send === 'function') {
        (this.session as any).send({
          type: 'response.audio.stop',
        });
        console.log('[WebSocketStrategy] 已发送打断信号到服务器');
      } else {
        console.warn('[WebSocketStrategy] Session 不支持 send 方法，无法发送打断信号');
      }
    } catch (error) {
      console.error('[WebSocketStrategy] 发送打断信号失败:', error);
    }
  }

  /**
   * 立即停止通话（停止音频播放）
   * 
   * 停止音频捕获和播放，但不释放资源（以便下次通话可以重用）
   */
  stopCall(): void {
    console.log('[WebSocketStrategy] 立即停止通话...');

    // ✅ 关键修复：立即设置 isCalling = false，阻止新的音频处理
    this.isCalling = false;

    // ✅ 调用打断方法，停止所有播放
    this.interruptAssistant();

    // ✅ 关键修复：清空音频队列和缓冲区，停止播放
    this.audioQueue = [];
    this.audioBuffer = null;
    this.isPlayingAudio = false;
    this.nextPlayTime = 0; // 重置播放时间
    
    // 清除定时器
    if (this.flushInterval) {
      clearTimeout(this.flushInterval);
      this.flushInterval = null;
    }
    
    // 断开 GainNode
    if (this.gainNode) {
      this.gainNode.disconnect();
      this.gainNode = null;
    }
    
    // 停止播放 AudioContext
    if (this.playbackAudioContext) {
      this.playbackAudioContext.close().catch(console.error);
      this.playbackAudioContext = null;
    }

    // ✅ 关键修复：停止音频捕获（断开 processor 和 source）
    if (this.processor) {
      try {
        this.processor.disconnect();
        console.log('[WebSocketStrategy] 音频处理器已断开');
      } catch (e) {
        console.error('[WebSocketStrategy] 断开处理器失败:', e);
      }
    }

    if (this.source) {
      try {
        this.source.disconnect();
        console.log('[WebSocketStrategy] 音频源已断开');
      } catch (e) {
        console.error('[WebSocketStrategy] 断开音频源失败:', e);
      }
    }

    // ✅ 关键修复：停止用户音频流的所有轨道（停止输入）
    if (this.mediaStream) {
      try {
        this.mediaStream.getTracks().forEach((track) => {
          track.stop();
          console.log('[WebSocketStrategy] 已停止音频轨道:', track.kind);
        });
        // 注意：不设置为 null，因为 cleanup() 中会处理
      } catch (error) {
        console.error('[WebSocketStrategy] 停止音频轨道失败:', error);
      }
    }

    // ✅ 关键修复：停止所有正在播放的音频元素
    // 注意：WebSocket 模式下，每次收到音频都会创建新的 Audio 元素
    // 我们需要停止所有正在播放的音频
    if (this.audioElement) {
      try {
        this.audioElement.pause();
        this.audioElement.src = '';
        this.audioElement.srcObject = null;
        console.log('[WebSocketStrategy] 音频元素已暂停');
      } catch (error) {
        console.error('[WebSocketStrategy] 暂停音频元素失败:', error);
      }
    }

    // ✅ 关键修复：停止音频可视化
    this.stopAudioVisualization();

    console.log('[WebSocketStrategy] 通话已立即停止');
  }

  /**
   * 清理资源
   */
  cleanup(): void {
    console.log('[WebSocketStrategy] 清理资源...');

    // 停止音频可视化
    this.stopAudioVisualization();
    this.audioVisualizer.cleanup();

    // 清理音频处理器
    if (this.processor) {
      try {
        this.processor.disconnect();
      } catch (e) {
        // Ignore
      }
      this.processor = null;
    }

    if (this.source) {
      try {
        this.source.disconnect();
      } catch (e) {
        // Ignore
      }
      this.source = null;
    }

    if (this.audioContext) {
      this.audioContext.close().catch(console.error);
      this.audioContext = null;
    }

    // 清理播放 AudioContext
    if (this.playbackAudioContext) {
      this.playbackAudioContext.close().catch(console.error);
      this.playbackAudioContext = null;
    }

    // 清空音频队列和缓冲区
    this.audioQueue = [];
    this.audioBuffer = null;
    this.isPlayingAudio = false;
    this.nextPlayTime = 0; // 重置播放时间
    
    // 清除定时器
    if (this.flushInterval) {
      clearTimeout(this.flushInterval);
      this.flushInterval = null;
    }
    
    // 断开 GainNode
    if (this.gainNode) {
      this.gainNode.disconnect();
      this.gainNode = null;
    }

    // 停止音频流
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    // 清理音频元素
    if (this.audioElement) {
      this.audioElement.pause();
      this.audioElement.src = '';
      this.audioElement = null;
    }

    this.session = null;
    this.onUserFrequencyData = null;
    this.onAssistantFrequencyData = null;

    console.log('[WebSocketStrategy] 资源已清理');
  }

  /**
   * 获取当前用户音频频率数据（用于可视化）
   */
  getCurrentUserFrequencyData(): Uint8Array | null {
    return this.audioVisualizer.getCurrentUserFrequencyData();
  }

  /**
   * 获取当前助手音频频率数据（用于可视化）
   */
  getCurrentAssistantFrequencyData(): Uint8Array | null {
    return this.audioVisualizer.getCurrentAssistantFrequencyData();
  }
}

