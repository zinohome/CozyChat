import { useState, useRef, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { configApi } from '@/services/config';
import { personalityApi } from '@/services/personality';
import type { OpenAIConfig } from '@/services/config';

/**
 * Voice Agent Hook返回值
 */
export interface UseVoiceAgentReturn {
  /** 是否已连接 */
  isConnected: boolean;
  /** 是否正在通话 */
  isCalling: boolean;
  /** 错误信息 */
  error: string | null;
  /** 用户音频频率数据（用于可视化） */
  userFrequencyData: Uint8Array | null;
  /** 助手音频频率数据（用于可视化） */
  assistantFrequencyData: Uint8Array | null;
  /** WebSocket 延迟（毫秒） */
  latency: number | null;
  /** 连接 Voice Agent */
  connect: () => Promise<void>;
  /** 断开连接 */
  disconnect: () => void;
  /** 开始通话 */
  startCall: () => Promise<void>;
  /** 结束通话 */
  endCall: () => Promise<void>;
}

/**
 * WebSocket 消息类型
 */
interface RealtimeMessage {
  type: string;
  event_id?: string;
  [key: string]: any;
}

/**
 * Voice Agent Hook
 *
 * 使用原生 WebSocket 实现语音通话功能。
 * 前端直接连接 OpenAI Realtime API（通过 New API 或 OpenAI 官方），后端仅提供配置。
 *
 * @param sessionId - 会话ID
 * @param personalityId - 人格ID
 * @param callbacks - 回调函数
 * @returns Voice Agent Hook返回值
 *
 * 参考文档：
 * - https://docs.newapi.pro/api/openai-realtime/#websocket_1
 * - https://platform.openai.com/docs/guides/realtime
 */
export const useVoiceAgent = (
  _sessionId?: string,
  personalityId?: string,
  callbacks?: {
    onUserTranscript?: (text: string) => void;
    onAssistantTranscript?: (text: string) => void;
  }
): UseVoiceAgentReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [isCalling, setIsCalling] = useState(false);
  const isCallingRef = useRef<boolean>(false); // 用于闭包中访问最新的 isCalling 值
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const configRef = useRef<OpenAIConfig | null>(null);
  const realtimeTokenRef = useRef<{ token: string; url: string; model: string } | null>(null);
  
  // 音频相关引用
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioPlaybackContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const eventIdCounterRef = useRef<number>(0);
  
  // 音频可视化相关
  const userAnalyserRef = useRef<AnalyserNode | null>(null);
  const assistantAnalyserRef = useRef<AnalyserNode | null>(null);
  const [userFrequencyData, setUserFrequencyData] = useState<Uint8Array | null>(null);
  const [assistantFrequencyData, setAssistantFrequencyData] = useState<Uint8Array | null>(null);
  const userAnimationFrameRef = useRef<number | null>(null);
  const assistantAnimationFrameRef = useRef<number | null>(null);
  
  // 音频播放队列和调度
  const audioQueueRef = useRef<Array<{ buffer: AudioBuffer; startTime: number }>>([]);
  const nextPlayTimeRef = useRef<number>(0);
  const isPlayingRef = useRef<boolean>(false);
  
  // 打断和响应管理
  const currentResponseIdRef = useRef<string | null>(null);
  const isAssistantSpeakingRef = useRef<boolean>(false);
  const userVolumeRef = useRef<number>(0);
  const lastUserSpeechTimeRef = useRef<number>(0);
  const interruptCheckIntervalRef = useRef<number | null>(null);
  
  // 转录文本相关
  const assistantTranscriptRef = useRef<string>('');
  const assistantTextRef = useRef<string>('');
  
  // 心跳和延迟监控
  const pingIntervalRef = useRef<number | null>(null);
  const lastPingTimeRef = useRef<number>(0);
  const [latency, setLatency] = useState<number | null>(null);
  
  // 调试日志时间戳
  const lastDebugLogTimeRef = useRef<number>(0);

  // 获取 personality 配置
  const { data: personality } = useQuery({
    queryKey: ['personality', personalityId],
    queryFn: () => personalityApi.getPersonality(personalityId!),
    enabled: !!personalityId,
    staleTime: 10 * 60 * 1000, // 10分钟
  });

  /**
   * 获取 OpenAI 配置
   */
  const loadConfig = useCallback(async () => {
    if (configRef.current) {
      return configRef.current;
    }
    
    const config = await configApi.getOpenAIConfig();
    configRef.current = config;
    return config;
  }, []);

  /**
   * 生成事件ID
   */
  const generateEventId = useCallback(() => {
    eventIdCounterRef.current += 1;
    return `event_${Date.now()}_${eventIdCounterRef.current}`;
  }, []);

  /**
   * 发送 WebSocket 消息
   */
  const sendMessage = useCallback((message: RealtimeMessage) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket 未连接，无法发送消息');
      return;
    }
    
    const messageWithId = {
      ...message,
      event_id: message.event_id || generateEventId(),
    };
    
    console.log('发送 WebSocket 消息:', messageWithId);
    wsRef.current.send(JSON.stringify(messageWithId));
  }, [generateEventId]);

  /**
   * 初始化音频录制
   */
  const initAudioRecording = useCallback(async () => {
    try {
      // 请求麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 24000,
          echoCancellation: true,
          noiseSuppression: true,
        }
      });
      
      mediaStreamRef.current = stream;
      
      // 创建 AudioContext
      const audioContext = new AudioContext({ sampleRate: 24000 });
      audioContextRef.current = audioContext;
      
      // 确保 AudioContext 处于运行状态（浏览器可能自动暂停）
      if (audioContext.state === 'suspended') {
        console.log('AudioContext 被暂停，正在恢复...');
        await audioContext.resume();
        console.log('AudioContext 已恢复，状态:', audioContext.state);
      }
      
      // 创建 MediaStreamAudioSourceNode
      const source = audioContext.createMediaStreamSource(stream);
      
      // 创建 AnalyserNode 用于音频可视化
      // 使用较小的 FFT 大小（128）以提高性能，参考 FastRTC 优化
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 128;
      analyser.smoothingTimeConstant = 0.85; // 平滑音频数据，参考 FastRTC
      userAnalyserRef.current = analyser;
      
      // 使用 ScriptProcessorNode 处理音频（兼容性更好）
      const bufferSize = 4096;
      const processor = audioContext.createScriptProcessor(bufferSize, 1, 1);
      processorRef.current = processor; // 保存引用以便清理
      
      // 连接音频流：source -> analyser（用于可视化）
      // 注意：AnalyserNode 是被动节点，不需要连接到 destination 也能工作
      // 参考 FastRTC 实现：只连接 source -> analyser
      source.connect(analyser);
      
      // 连接 source -> processor（用于录制和发送）
      // 注意：processor 不需要连接到 destination，只要它有 onaudioprocess 回调就会工作
      source.connect(processor);
      
      // 调试日志
      const audioTracks = stream.getAudioTracks();
      console.log('用户音频可视化初始化:', {
        hasStream: !!stream,
        hasSource: !!source,
        hasAnalyser: !!analyser,
        hasProcessor: !!processor,
        analyserFftSize: analyser.fftSize,
        analyserFrequencyBinCount: analyser.frequencyBinCount,
        streamActive: stream.active,
        audioTracksCount: audioTracks.length,
        audioContextState: audioContext.state,
        trackEnabled: audioTracks.length > 0 ? audioTracks[0].enabled : false,
        trackReadyState: audioTracks.length > 0 ? audioTracks[0].readyState : 'N/A',
        trackMuted: audioTracks.length > 0 ? audioTracks[0].muted : false,
      });
      
      // 监听音频轨道状态变化
      if (audioTracks.length > 0) {
        const track = audioTracks[0];
        track.onended = () => {
          console.warn('用户音频轨道已结束');
        };
        track.onmute = () => {
          console.warn('用户音频轨道被静音');
        };
        track.onunmute = () => {
          console.log('用户音频轨道取消静音');
        };
      }
      
      // 启动用户音频可视化（优化：使用 setInterval 每 100ms 更新一次，降低 CPU 使用）
      const updateUserAudioVisualization = () => {
        if (!userAnalyserRef.current) {
          if (process.env.NODE_ENV === 'development') {
            console.warn('updateUserAudioVisualization: userAnalyserRef.current 不存在');
          }
          return;
        }
        
        if (!isCallingRef.current) {
          if (process.env.NODE_ENV === 'development') {
            console.warn('updateUserAudioVisualization: isCallingRef.current 为 false');
          }
          return;
        }
        
        const bufferLength = userAnalyserRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        userAnalyserRef.current.getByteFrequencyData(dataArray);
        setUserFrequencyData(dataArray);
        
        // 计算用户音量（用于打断检测）
        let sum = 0;
        let maxValue = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
          maxValue = Math.max(maxValue, dataArray[i]);
        }
        const avgVolume = sum / dataArray.length / 255; // 0-1
        userVolumeRef.current = avgVolume;
        
        // 调试日志：每 1 秒输出一次音量信息
        if (process.env.NODE_ENV === 'development') {
          const now = Date.now();
          if (!lastDebugLogTimeRef.current || now - lastDebugLogTimeRef.current > 1000) {
            console.log('用户音频可视化:', {
              hasAnalyser: !!userAnalyserRef.current,
              isCalling: isCallingRef.current,
              avgVolume: avgVolume.toFixed(4),
              dataLength: dataArray.length,
              maxValue: maxValue,
              firstFewValues: Array.from(dataArray.slice(0, 5)), // 显示前几个值用于调试
            });
            lastDebugLogTimeRef.current = now;
          }
        }
        
        // 如果用户音量超过阈值，记录说话时间
        if (avgVolume > 0.05) {
          lastUserSpeechTimeRef.current = Date.now();
        }
      };
      
      // 每 100ms 更新一次（参考文档建议，降低 CPU 使用）
      const userVisualizationInterval = window.setInterval(() => {
        updateUserAudioVisualization();
      }, 100);
      
      // 保存 interval ID 以便清理
      userAnimationFrameRef.current = userVisualizationInterval as any; // 复用 ref 存储 interval ID
      
      // 音频发送节流（避免发送太频繁）
      let lastAudioSendTime = 0;
      const AUDIO_SEND_INTERVAL = 20; // 每 20ms 发送一次（50Hz）
      
      // VAD（Voice Activity Detection）阈值
      const VAD_THRESHOLD = 0.01; // 音量阈值，低于此值视为静音
      
      processor.onaudioprocess = (e) => {
        // 使用 ref 检查 isCalling，避免闭包问题
        if (!isCallingRef.current || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          return;
        }
        
        const now = Date.now();
        if (now - lastAudioSendTime < AUDIO_SEND_INTERVAL) {
          return; // 节流：避免发送太频繁
        }
        lastAudioSendTime = now;
        
        const inputData = e.inputBuffer.getChannelData(0);
        
        // VAD：计算音频块的音量（RMS - Root Mean Square）
        let sumSquares = 0;
        for (let i = 0; i < inputData.length; i++) {
          sumSquares += inputData[i] * inputData[i];
        }
        const rms = Math.sqrt(sumSquares / inputData.length);
        
        // 只有在音量超过阈值时才发送音频数据
        if (rms < VAD_THRESHOLD) {
          return; // 静音，不发送
        }
        
        // 转换为 PCM16 格式
        const pcm16 = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          // 将 float32 (-1.0 到 1.0) 转换为 int16 (-32768 到 32767)
          const sample = Math.max(-1, Math.min(1, inputData[i]));
          pcm16[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
        }
        
        // 将 Int16Array 转换为 Base64 编码的字符串
        // 注意：使用更安全的方式处理大数组，避免栈溢出
        const uint8Array = new Uint8Array(pcm16.buffer);
        
        // 将 Uint8Array 转换为 Base64（使用更安全的方式）
        let binary = '';
        const chunkSize = 8192; // 分块处理，避免栈溢出
        for (let i = 0; i < uint8Array.length; i += chunkSize) {
          const chunk = uint8Array.slice(i, i + chunkSize);
          binary += String.fromCharCode(...chunk);
        }
        const base64 = btoa(binary);
        
        // 发送音频数据（只有在检测到声音时才发送）
        sendMessage({
          type: 'conversation.item.input_audio_buffer.append',
          audio: base64,
        });
      };
      
      // processor 不需要连接到 destination（只用于处理音频数据）
      
      console.log('音频录制初始化成功');
    } catch (err: any) {
      console.error('初始化音频录制失败:', err);
      setError(`初始化音频录制失败: ${err.message}`);
      throw err;
    }
  }, [sendMessage]); // 移除 isCalling 依赖，使用 isCallingRef.current 代替

  /**
   * 停止音频录制
   */
  const stopAudioRecording = useCallback(() => {
    // 停止用户音频可视化（现在使用 setInterval，需要 clearInterval）
    if (userAnimationFrameRef.current) {
      clearInterval(userAnimationFrameRef.current as any);
      userAnimationFrameRef.current = null;
    }
    setUserFrequencyData(null);
    
    // 停止媒体流
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    
    // 断开 processor 连接
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    
    // 断开 analyser 连接
    if (userAnalyserRef.current) {
      userAnalyserRef.current.disconnect();
      userAnalyserRef.current = null;
    }
    
    // 关闭 AudioContext
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    // 停止助手音频可视化（现在使用 setInterval，需要 clearInterval）
    if (assistantAnimationFrameRef.current) {
      clearInterval(assistantAnimationFrameRef.current as any);
      assistantAnimationFrameRef.current = null;
    }
    if (assistantAnalyserRef.current) {
      assistantAnalyserRef.current.disconnect();
      assistantAnalyserRef.current = null;
    }
    setAssistantFrequencyData(null);
    
    // 停止打断检测
    if (interruptCheckIntervalRef.current) {
      clearInterval(interruptCheckIntervalRef.current);
      interruptCheckIntervalRef.current = null;
    }
    
    // 清空音频播放队列
    audioQueueRef.current = [];
    nextPlayTimeRef.current = 0;
    isPlayingRef.current = false;
    
    // 重置状态
    currentResponseIdRef.current = null;
    isAssistantSpeakingRef.current = false;
    userVolumeRef.current = 0;
    lastUserSpeechTimeRef.current = 0;
    
    // 注意：不关闭 audioPlaybackContextRef，因为可能还在播放音频
    
    console.log('音频录制已停止');
  }, []);

  /**
   * 初始化助手音频可视化
   */
  const initAssistantAudioVisualization = useCallback(() => {
    if (!audioPlaybackContextRef.current) {
      console.warn('助手音频可视化：audioPlaybackContextRef 不存在');
      return;
    }
    
    const audioContext = audioPlaybackContextRef.current;
    
    // 创建 AnalyserNode 用于可视化（如果还没有）
    if (!assistantAnalyserRef.current) {
      console.log('创建助手音频 AnalyserNode');
      // 使用较小的 FFT 大小（128）以提高性能，参考 FastRTC 优化
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 128;
      analyser.smoothingTimeConstant = 0.85; // 平滑音频数据，参考 FastRTC
      assistantAnalyserRef.current = analyser;
      
      // 连接到 destination（只连接一次）
      analyser.connect(audioContext.destination);
      console.log('助手音频 AnalyserNode 已连接到 destination');
    }
    
    // 启动助手音频可视化（优化：使用 setInterval 每 100ms 更新一次，降低 CPU 使用）
    if (!assistantAnimationFrameRef.current) {
      console.log('启动助手音频可视化循环');
      let updateCount = 0;
      
      const updateAssistantAudioVisualization = () => {
        // 使用 ref 检查 isCalling，避免闭包问题
        if (!assistantAnalyserRef.current || !isCallingRef.current) {
          console.log('助手音频可视化循环停止', {
            hasAnalyser: !!assistantAnalyserRef.current,
            isCalling: isCallingRef.current,
          });
          if (assistantAnimationFrameRef.current) {
            clearInterval(assistantAnimationFrameRef.current as any);
            assistantAnimationFrameRef.current = null;
          }
          return;
        }
        
        const bufferLength = assistantAnalyserRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        assistantAnalyserRef.current.getByteFrequencyData(dataArray);
        
        // 计算平均强度用于调试
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avgIntensity = sum / dataArray.length / 255;
        
        // 每 10 次更新（约 1 秒）打印一次调试信息
        if (updateCount % 10 === 0 && avgIntensity > 0.01) {
          console.log('助手音频可视化:', {
            updateCount,
            avgIntensity: avgIntensity.toFixed(3),
            dataLength: dataArray.length,
            maxValue: Math.max(...Array.from(dataArray)),
          });
        }
        updateCount++;
        
        setAssistantFrequencyData(dataArray);
      };
      
      // 每 100ms 更新一次（参考文档建议，降低 CPU 使用）
      const assistantVisualizationInterval = window.setInterval(() => {
        updateAssistantAudioVisualization();
      }, 100);
      
      // 保存 interval ID 以便清理
      assistantAnimationFrameRef.current = assistantVisualizationInterval as any; // 复用 ref 存储 interval ID
    } else {
      console.log('助手音频可视化循环已启动，跳过');
    }
  }, []); // 移除 isCalling 依赖，使用 isCallingRef.current 代替
  
  /**
   * 处理音频播放队列
   */
  const processAudioQueue = useCallback(() => {
    if (!audioPlaybackContextRef.current || isPlayingRef.current) {
      return;
    }
    
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      return;
    }
    
    const audioContext = audioPlaybackContextRef.current;
    const currentTime = audioContext.currentTime;
    
    // 如果下一个播放时间已经过去，立即播放
    const playTime = Math.max(currentTime, nextPlayTimeRef.current);
    
    const { buffer } = audioQueueRef.current.shift()!;
    const duration = buffer.duration;
    
    // 确保助手音频可视化已初始化
    if (!assistantAnalyserRef.current) {
      console.log('processAudioQueue: 初始化助手音频可视化');
      initAssistantAudioVisualization();
    }
    
    // 创建 AudioBufferSourceNode
    const source = audioContext.createBufferSource();
    source.buffer = buffer;
    
    // 连接：source -> analyser（analyser 已经连接到 destination）
    if (assistantAnalyserRef.current) {
      console.log('processAudioQueue: 连接 source 到 analyser, buffer duration:', duration.toFixed(3), 's');
      source.connect(assistantAnalyserRef.current);
      
      // 确保可视化循环正在运行
      if (!assistantAnimationFrameRef.current) {
        console.log('processAudioQueue: 可视化循环未运行，重新启动');
        initAssistantAudioVisualization();
      }
    } else {
      // 如果没有 analyser，直接连接到 destination
      console.warn('processAudioQueue: analyser 不存在，直接连接到 destination');
      source.connect(audioContext.destination);
    }
    
    // 播放完成后继续处理队列
    source.onended = () => {
      source.disconnect();
      nextPlayTimeRef.current = playTime + duration;
      isPlayingRef.current = false;
      processAudioQueue();
    };
    
    source.start(playTime);
    isPlayingRef.current = true;
  }, [initAssistantAudioVisualization]);
  
  /**
   * 播放音频数据（PCM16格式）
   * 
   * 使用音频队列和调度确保连续播放，避免音频重叠或中断
   */
  const playAudioChunk = useCallback(async (audioData: string) => {
    try {
      // 创建或获取音频播放上下文（与录制上下文分开）
      if (!audioPlaybackContextRef.current) {
        audioPlaybackContextRef.current = new AudioContext({ sampleRate: 24000 });
      }
      
      const audioContext = audioPlaybackContextRef.current;
      
      // 如果上下文被暂停（浏览器自动暂停），恢复它
      if (audioContext.state === 'suspended') {
        await audioContext.resume();
      }
      
      // 解析 Base64 编码的 PCM16 音频数据
      const binaryString = atob(audioData);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      
      // 将 Uint8Array 转换为 Int16Array（PCM16）
      if (bytes.length % 2 !== 0) {
        console.warn('音频数据长度不是 2 的倍数，可能有问题');
        return;
      }
      const pcm16Data = new Int16Array(bytes.buffer, 0, bytes.length / 2);
      
      // 将 Int16Array 转换为 Float32Array（Web Audio API 需要）
      const float32Data = new Float32Array(pcm16Data.length);
      for (let i = 0; i < pcm16Data.length; i++) {
        float32Data[i] = Math.max(-1, Math.min(1, pcm16Data[i] / 32768.0));
      }
      
      // 创建 AudioBuffer
      const audioBuffer = audioContext.createBuffer(1, float32Data.length, 24000);
      audioBuffer.copyToChannel(float32Data, 0);
      
      // 添加到播放队列
      audioQueueRef.current.push({
        buffer: audioBuffer,
        startTime: audioContext.currentTime,
      });
      
      // 处理队列
      processAudioQueue();
    } catch (err) {
      console.error('播放音频失败:', err);
    }
  }, [processAudioQueue]);

  /**
   * 处理 WebSocket 消息
   */
  const handleMessage = useCallback((data: RealtimeMessage) => {
    // 只在开发环境打印所有消息，生产环境只打印重要消息
    if (process.env.NODE_ENV === 'development') {
      console.log('收到 WebSocket 消息:', data);
    }
    
    switch (data.type) {
      case 'session.created':
        console.log('会话已创建:', data.session);
        break;
        
      case 'session.updated':
        console.log('会话已更新:', data.session);
        break;
        
      // 心跳响应
      case 'pong':
        const currentLatency = Date.now() - lastPingTimeRef.current;
        setLatency(currentLatency);
        if (process.env.NODE_ENV === 'development') {
          console.log('WebSocket 延迟:', currentLatency, 'ms');
        }
        break;
        
      // 用户语音转文本完成
      case 'conversation.item.input_audio_transcription.completed':
        const userTranscript = data.transcript || data.item?.transcript;
        console.log('用户语音转文本完成:', userTranscript);
        if (userTranscript && callbacks?.onUserTranscript) {
          callbacks.onUserTranscript(userTranscript);
        }
        // 用户说话后，如果助手没有在说话，创建新的响应
        if (userTranscript && !isAssistantSpeakingRef.current) {
          console.log('用户说话后，创建新响应');
          sendMessage({
            type: 'response.create',
            response: {
              modalities: ['text', 'audio'],
            },
          });
        }
        break;
        
      // 助手音频转录增量
      case 'response.audio_transcript.delta':
        if (data.delta) {
          assistantTranscriptRef.current += data.delta;
          // 可以实时更新 UI（如果需要）
        }
        break;
        
      // 助手音频转录完成
      case 'response.audio_transcript.done':
        const finalTranscript = data.transcript || assistantTranscriptRef.current;
        if (finalTranscript && callbacks?.onAssistantTranscript) {
          callbacks.onAssistantTranscript(finalTranscript);
        }
        assistantTranscriptRef.current = ''; // 重置
        break;
        
      // 助手文本增量
      case 'response.text.delta':
        if (data.delta) {
          assistantTextRef.current += data.delta;
          // 可以实时更新 UI（如果需要）
        }
        break;
        
      // 助手文本完成
      case 'response.text.done':
        const finalText = data.text || assistantTextRef.current;
        if (finalText && callbacks?.onAssistantTranscript) {
          callbacks.onAssistantTranscript(finalText);
        }
        assistantTextRef.current = ''; // 重置
        break;
        
      // 助手音频流（增量）- 实时播放
      case 'response.audio.delta':
        if (data.delta) {
          // 确保助手音频可视化已初始化
          if (!assistantAnalyserRef.current) {
            console.log('response.audio.delta: 初始化助手音频可视化');
            initAssistantAudioVisualization();
          }
          isAssistantSpeakingRef.current = true;
          playAudioChunk(data.delta);
        }
        break;
        
      // 助手音频完成
      case 'response.audio.done':
        console.log('助手音频播放完成');
        isAssistantSpeakingRef.current = false;
        break;
        
      // 响应创建
      case 'response.created':
        // 重置转录和文本
        assistantTranscriptRef.current = '';
        assistantTextRef.current = '';
        // 记录当前响应 ID（用于打断）
        currentResponseIdRef.current = data.response?.id || null;
        isAssistantSpeakingRef.current = true;
        // 确保助手音频可视化已初始化
        if (!assistantAnalyserRef.current) {
          initAssistantAudioVisualization();
        }
        break;
        
      // 响应完成
      case 'response.done':
        console.log('响应完成:', data.response);
        currentResponseIdRef.current = null;
        isAssistantSpeakingRef.current = false;
        // 响应完成后，等待用户说话
        // 服务器端 VAD 会自动检测用户说话并创建新的响应
        // 如果 2 秒后用户还没有说话，我们可以创建一个新的响应来"唤醒"助手
        setTimeout(() => {
          if (isCalling && !isAssistantSpeakingRef.current && !currentResponseIdRef.current) {
            console.log('响应完成后等待用户输入，创建新响应以监听用户说话');
            sendMessage({
              type: 'response.create',
              response: {
                modalities: ['text', 'audio'],
              },
            });
          }
        }, 2000);
        break;
        
      // 错误
      case 'error':
        const errorMessage = data.error?.message || 'WebSocket 错误';
        setError(errorMessage);
        console.error('WebSocket 错误:', data.error);
        break;
        
      // 其他消息类型（记录但不处理）
      case 'response.output_item.added':
      case 'response.output_item.done':
      case 'response.content_part.added':
      case 'response.content_part.done':
      case 'conversation.item.created':
        console.log('对话项已创建:', data.item);
        // 检查是否是用户创建的对话项（type: 'input_audio_buffer' 或 role: 'user'）
        const itemType = data.item?.type;
        const itemRole = data.item?.role;
        if (itemType === 'input_audio_buffer' || itemRole === 'user') {
          console.log('检测到用户对话项创建，等待服务器端 VAD 检测用户说话');
          // 不立即创建响应，让服务器端 VAD 自动检测用户说话
        } else if (itemRole === 'assistant' && !isAssistantSpeakingRef.current && !currentResponseIdRef.current) {
          // 如果是助手创建的对话项，且助手没有在说话，创建响应
          console.log('助手对话项创建后，创建新响应');
          sendMessage({
            type: 'response.create',
            response: {
              modalities: ['text', 'audio'],
            },
          });
        }
        break;
        
      case 'rate_limits.updated':
        // 这些消息类型不需要特殊处理，只记录
        if (process.env.NODE_ENV === 'development') {
          console.log(`收到消息类型: ${data.type}`);
        }
        break;
        
      default:
        if (process.env.NODE_ENV === 'development') {
          console.log('未知消息类型:', data.type);
        }
    }
  }, [callbacks, playAudioChunk, initAssistantAudioVisualization, sendMessage]);

  /**
   * 连接 Voice Agent
   */
  const connect = useCallback(async () => {
    try {
      setError(null);
      
      // 1. 获取配置
      const config = await loadConfig();
      configRef.current = config;
      
      // 2. 获取 WebSocket URL 和 token
      const realtimeToken = await configApi.getRealtimeToken();
      realtimeTokenRef.current = realtimeToken;
      
      console.log('获取 Realtime Token 成功:', {
        url: realtimeToken.url,
        model: realtimeToken.model,
      });
      
          // 3. 建立 WebSocket 连接
      return new Promise<void>((resolve, reject) => {
        try {
          // 构建 WebSocket URL（如果后端返回的 URL 不完整）
          let wsUrl = realtimeToken.url;
          if (!wsUrl.startsWith('ws://') && !wsUrl.startsWith('wss://')) {
            // 如果后端只返回了路径，需要拼接完整的 URL
            const baseUrl = config.base_url || 'https://api.openai.com/v1';
            const wsBaseUrl = baseUrl.replace(/^https?:\/\//, 'wss://').replace(/\/v1$/, '');
            wsUrl = `${wsBaseUrl}/v1/realtime?model=${realtimeToken.model}`;
          }
          
          console.log('连接 WebSocket:', wsUrl);
          console.log('使用 Token:', realtimeToken.token.substring(0, 20) + '...');
          
          // 创建 WebSocket 连接
          // 根据 New API 文档：浏览器环境使用子协议（subprotocols）传递认证信息
          // 参考：https://docs.newapi.pro/api/openai-realtime/#websocket_1
          // 格式：["realtime", "openai-insecure-api-key." + API_KEY, "openai-beta.realtime-v1"]
          // 注意：即使无法获取 ephemeral client key，也可以使用 API key 通过子协议认证
          const protocols = [
            'realtime',
            `openai-insecure-api-key.${realtimeToken.token}`,
            'openai-beta.realtime-v1',
          ];
          
          console.log('使用子协议认证（useInsecureApiKey 方式）');
          
          const ws = new WebSocket(wsUrl, protocols);
          wsRef.current = ws;
          
          ws.onopen = () => {
            console.log('WebSocket 连接成功');
            
            // 连接成功后，立即发送认证消息（如果服务器支持）
            // 或者直接发送 session.update（如果服务器在 URL 中已经验证了 token）
            
            // 发送 session.update 消息配置会话
            const personalityConfig = (personality as any)?.config || {};
            const voiceConfig = personalityConfig?.voice || {};
            const realtimeConfig = voiceConfig?.realtime || {};
            const aiConfig = personalityConfig?.ai || {};
            
            const instructions = realtimeConfig.instructions 
              || aiConfig.system_prompt 
              || '你是一个友好的AI助手，帮助用户解答问题。';
            
            const voice = realtimeConfig.voice || 'shimmer';
            
            // 配置会话
            sendMessage({
              type: 'session.update',
              session: {
                modalities: ['text', 'audio'],
                instructions: instructions,
                voice: voice,
                input_audio_format: 'pcm16',
                output_audio_format: 'pcm16',
                input_audio_transcription: {
                  model: 'whisper-1',
                },
                turn_detection: {
                  type: 'server_vad',
                  threshold: 0.3, // 降低阈值，更容易检测到用户说话
                  prefix_padding_ms: 300,
                  silence_duration_ms: 500,
                },
              },
            });
            
            setIsConnected(true);
            
            // 启动心跳机制（每 5 秒发送一次 ping）
            pingIntervalRef.current = window.setInterval(() => {
              if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                lastPingTimeRef.current = Date.now();
                sendMessage({ type: 'ping' });
              }
            }, 5000);
            
            resolve();
          };
          
          ws.onmessage = (event) => {
            try {
              const data = JSON.parse(event.data);
              handleMessage(data);
            } catch (err) {
              console.error('解析 WebSocket 消息失败:', err);
            }
          };
          
          ws.onerror = (err) => {
            console.error('WebSocket 错误:', err);
            setError('WebSocket 连接错误');
            reject(new Error('WebSocket 连接错误'));
          };
          
          ws.onclose = (event) => {
            console.log('WebSocket 连接已关闭:', event.code, event.reason);
            
            // 停止心跳机制
            if (pingIntervalRef.current) {
              clearInterval(pingIntervalRef.current);
              pingIntervalRef.current = null;
            }
            setLatency(null);
            
            setIsConnected(false);
            setIsCalling(false);
            isCallingRef.current = false; // 同步更新 ref
            
            if (event.code !== 1000) {
              // 非正常关闭
              setError(`WebSocket 连接关闭: ${event.reason || '未知原因'}`);
            }
          };
          
        } catch (err: any) {
          const errorMessage = err.message || '连接失败';
          setError(errorMessage);
          console.error('Failed to connect WebSocket:', err);
          reject(err);
        }
      });
    } catch (err: any) {
      const errorMessage = err.message || '连接失败';
      setError(errorMessage);
      console.error('Failed to connect Voice Agent:', err);
      throw err;
    }
  }, [loadConfig, personality, handleMessage, sendMessage]);

  /**
   * 检测用户说话并打断助手
   */
  const checkAndInterrupt = useCallback(() => {
    if (!isCalling || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }
    
    const userVolume = userVolumeRef.current;
    
    // 如果用户音量超过阈值，且助手正在说话，则打断
    if (userVolume > 0.1 && isAssistantSpeakingRef.current && currentResponseIdRef.current) {
      console.log('检测到用户说话，打断助手响应');
      
      // 取消当前响应（只有在响应活跃时才取消）
      sendMessage({
        type: 'response.cancel',
      });
      
      // 清空音频播放队列
      audioQueueRef.current = [];
      nextPlayTimeRef.current = 0;
      isPlayingRef.current = false;
      
      // 重置状态
      currentResponseIdRef.current = null;
      isAssistantSpeakingRef.current = false;
      
      // 创建新的响应（让助手处理用户的输入）
      // 注意：延迟一点，确保 cancel 消息先发送
      setTimeout(() => {
        if (isCalling && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          sendMessage({
            type: 'response.create',
            response: {
              modalities: ['text', 'audio'],
            },
          });
        }
      }, 100);
    }
  }, [isCalling, sendMessage]);

  /**
   * 开始通话
   */
  const startCall = useCallback(async () => {
    if (!isConnected) {
      await connect();
    }
    
    try {
      // 先设置 isCalling 状态，确保音频可视化循环能够运行
      setIsCalling(true);
      isCallingRef.current = true; // 同步更新 ref
      
      // 初始化音频录制
      await initAudioRecording();
      
      // 初始化助手音频可视化（提前初始化，确保能显示声纹）
      // 注意：audioPlaybackContextRef 会在第一次播放时创建，但我们需要提前创建以确保可视化可用
      if (!audioPlaybackContextRef.current) {
        console.log('startCall: 创建音频播放上下文');
        audioPlaybackContextRef.current = new AudioContext({ sampleRate: 24000 });
        
        // 如果上下文被暂停（浏览器自动暂停），恢复它
        if (audioPlaybackContextRef.current.state === 'suspended') {
          await audioPlaybackContextRef.current.resume();
        }
      }
      
      // 初始化助手音频可视化
      console.log('startCall: 初始化助手音频可视化');
      initAssistantAudioVisualization();
      
      // 启动打断检测（每 100ms 检查一次）
      interruptCheckIntervalRef.current = window.setInterval(() => {
        checkAndInterrupt();
      }, 100);
      
      // 发送 response.create 开始响应
      sendMessage({
        type: 'response.create',
        response: {
          modalities: ['text', 'audio'],
        },
      });
      
      console.log('开始语音通话');
    } catch (err: any) {
      setError(err.message || '开始通话失败');
      throw err;
    }
  }, [isConnected, connect, initAudioRecording, sendMessage, initAssistantAudioVisualization, checkAndInterrupt]);

  /**
   * 结束通话
   */
  const endCall = useCallback(async () => {
    try {
      // 停止打断检测
      if (interruptCheckIntervalRef.current) {
        clearInterval(interruptCheckIntervalRef.current);
        interruptCheckIntervalRef.current = null;
      }
      
      // 停止音频录制
      stopAudioRecording();
      
      // 发送 response.cancel 取消响应
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        sendMessage({
          type: 'response.cancel',
        });
      }
      
      // 清空音频播放队列
      audioQueueRef.current = [];
      nextPlayTimeRef.current = 0;
      isPlayingRef.current = false;
      
      // 重置状态
      currentResponseIdRef.current = null;
      isAssistantSpeakingRef.current = false;
      userVolumeRef.current = 0;
      lastUserSpeechTimeRef.current = 0;
      
      setIsCalling(false);
      isCallingRef.current = false; // 同步更新 ref
      console.log('结束语音通话');
    } catch (err) {
      console.error('结束通话失败:', err);
    }
  }, [stopAudioRecording, sendMessage]);

  /**
   * 断开连接
   */
  const disconnect = useCallback(() => {
    try {
      // 停止音频录制
      stopAudioRecording();
      
      // 停止心跳机制
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }
      setLatency(null);
      
      // 关闭 WebSocket 连接
      if (wsRef.current) {
        wsRef.current.close(1000, '正常关闭');
        wsRef.current = null;
      }
      
      setIsConnected(false);
      setIsCalling(false);
      isCallingRef.current = false; // 同步更新 ref
      console.log('断开 WebSocket 连接');
    } catch (err) {
      console.error('断开连接失败:', err);
    }
  }, [stopAudioRecording]);

  // 清理
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    isCalling,
    error,
    userFrequencyData,
    assistantFrequencyData,
    latency,
    connect,
    disconnect,
    startCall,
    endCall,
  };
};
