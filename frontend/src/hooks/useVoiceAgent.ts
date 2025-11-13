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
  
  // 转录文本相关
  const assistantTranscriptRef = useRef<string>('');
  const assistantTextRef = useRef<string>('');

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
      
      // 创建 MediaStreamAudioSourceNode
      const source = audioContext.createMediaStreamSource(stream);
      
      // 创建 AnalyserNode 用于音频可视化
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;
      userAnalyserRef.current = analyser;
      
      // 连接 source -> analyser（用于可视化）
      source.connect(analyser);
      
      // 启动用户音频可视化
      const analyzeUserAudio = () => {
        if (!userAnalyserRef.current || !isCalling) {
          return;
        }
        
        const bufferLength = userAnalyserRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        userAnalyserRef.current.getByteFrequencyData(dataArray);
        setUserFrequencyData(dataArray);
        
        userAnimationFrameRef.current = requestAnimationFrame(analyzeUserAudio);
      };
      analyzeUserAudio();
      
      // 使用 ScriptProcessorNode 处理音频（兼容性更好）
      const bufferSize = 4096;
      const processor = audioContext.createScriptProcessor(bufferSize, 1, 1);
      processorRef.current = processor; // 保存引用以便清理
      
      // 连接 source -> processor（用于录制和发送）
      source.connect(processor);
      
      processor.onaudioprocess = (e) => {
        if (!isCalling || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          return;
        }
        
        const inputData = e.inputBuffer.getChannelData(0);
        
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
        
        // 发送音频数据
        // 注意：根据 OpenAI Realtime API 文档，消息类型应该是 conversation.item.input_audio_buffer.append
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
  }, [isCalling, sendMessage]);

  /**
   * 停止音频录制
   */
  const stopAudioRecording = useCallback(() => {
    // 停止用户音频可视化
    if (userAnimationFrameRef.current) {
      cancelAnimationFrame(userAnimationFrameRef.current);
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
    
    // 停止助手音频可视化
    if (assistantAnimationFrameRef.current) {
      cancelAnimationFrame(assistantAnimationFrameRef.current);
      assistantAnimationFrameRef.current = null;
    }
    setAssistantFrequencyData(null);
    
    // 清空音频播放队列
    audioQueueRef.current = [];
    nextPlayTimeRef.current = 0;
    isPlayingRef.current = false;
    
    // 注意：不关闭 audioPlaybackContextRef，因为可能还在播放音频
    
    console.log('音频录制已停止');
  }, []);

  /**
   * 初始化助手音频可视化
   */
  const initAssistantAudioVisualization = useCallback(() => {
    if (!audioPlaybackContextRef.current || assistantAnalyserRef.current) {
      return;
    }
    
    const audioContext = audioPlaybackContextRef.current;
    
    // 创建 AnalyserNode 用于可视化
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.8;
    assistantAnalyserRef.current = analyser;
    
    // 连接到 destination（只连接一次）
    analyser.connect(audioContext.destination);
    
    // 启动助手音频可视化
    const analyzeAssistantAudio = () => {
      if (!assistantAnalyserRef.current || !isCalling) {
        assistantAnimationFrameRef.current = null;
        return;
      }
      
      const bufferLength = assistantAnalyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      assistantAnalyserRef.current.getByteFrequencyData(dataArray);
      setAssistantFrequencyData(dataArray);
      
      assistantAnimationFrameRef.current = requestAnimationFrame(analyzeAssistantAudio);
    };
    analyzeAssistantAudio();
  }, [isCalling]);
  
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
      initAssistantAudioVisualization();
    }
    
    // 创建 AudioBufferSourceNode
    const source = audioContext.createBufferSource();
    source.buffer = buffer;
    
    // 连接：source -> analyser（analyser 已经连接到 destination）
    if (assistantAnalyserRef.current) {
      source.connect(assistantAnalyserRef.current);
    } else {
      // 如果没有 analyser，直接连接到 destination
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
        
      // 用户语音转文本完成
      case 'conversation.item.input_audio_transcription.completed':
        const userTranscript = data.transcript || data.item?.transcript;
        if (userTranscript && callbacks?.onUserTranscript) {
          callbacks.onUserTranscript(userTranscript);
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
          playAudioChunk(data.delta);
        }
        break;
        
      // 助手音频完成
      case 'response.audio.done':
        console.log('助手音频播放完成');
        break;
        
      // 响应创建
      case 'response.created':
        // 重置转录和文本
        assistantTranscriptRef.current = '';
        assistantTextRef.current = '';
        break;
        
      // 响应完成
      case 'response.done':
        console.log('响应完成:', data.response);
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
  }, [callbacks, playAudioChunk]);

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
          const protocols = [
            'realtime',
            `openai-insecure-api-key.${realtimeToken.token}`,
            'openai-beta.realtime-v1',
          ];
          
          console.log('使用子协议认证（隐藏 token）');
          
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
                  threshold: 0.5,
                },
              },
            });
            
            setIsConnected(true);
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
            setIsConnected(false);
            setIsCalling(false);
            
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
   * 开始通话
   */
  const startCall = useCallback(async () => {
    if (!isConnected) {
      await connect();
    }
    
    try {
      // 初始化音频录制
      await initAudioRecording();
      
      // 发送 response.create 开始响应
      sendMessage({
        type: 'response.create',
        response: {
          modalities: ['text', 'audio'],
        },
      });
      
      setIsCalling(true);
      console.log('开始语音通话');
    } catch (err: any) {
      setError(err.message || '开始通话失败');
      throw err;
    }
  }, [isConnected, connect, initAudioRecording, sendMessage]);

  /**
   * 结束通话
   */
  const endCall = useCallback(async () => {
    try {
      // 停止音频录制
      stopAudioRecording();
      
      // 发送 response.cancel 取消响应
      sendMessage({
        type: 'response.cancel',
      });
      
      setIsCalling(false);
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
      
      // 关闭 WebSocket 连接
      if (wsRef.current) {
        wsRef.current.close(1000, '正常关闭');
        wsRef.current = null;
      }
      
      setIsConnected(false);
      setIsCalling(false);
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
    connect,
    disconnect,
    startCall,
    endCall,
  };
};
