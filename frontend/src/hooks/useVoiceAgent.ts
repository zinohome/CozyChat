import { useState, useRef, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { RealtimeAgent, RealtimeSession, OpenAIRealtimeWebRTC } from '@openai/agents/realtime';
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
 * Voice Agent Hook
 *
 * 使用 OpenAI Agents SDK 的 Realtime API 实现语音通话功能。
 * 由于 oneapi.naivehero.top 是 api.openai.com 的完整镜像，可以直接使用 OpenAI SDK。
 *
 * @param sessionId - 会话ID
 * @param personalityId - 人格ID
 * @param callbacks - 回调函数
 * @returns Voice Agent Hook返回值
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
  
  const sessionRef = useRef<RealtimeSession | null>(null);
  const configRef = useRef<OpenAIConfig | null>(null);
  const isCallingRef = useRef(false);
  
  // 音频流和元素引用（用于可视化）
  const userMediaStreamRef = useRef<MediaStream | null>(null);
  const assistantAudioElementRef = useRef<HTMLAudioElement | null>(null);
  
  // 音频可视化相关
  const userAnalyserRef = useRef<AnalyserNode | null>(null);
  const assistantAnalyserRef = useRef<AnalyserNode | null>(null);
  const assistantSourceRef = useRef<MediaElementAudioSourceNode | null>(null);
  const assistantAudioContextRef = useRef<AudioContext | null>(null);
  const [userFrequencyData, setUserFrequencyData] = useState<Uint8Array | null>(null);
  const [assistantFrequencyData, setAssistantFrequencyData] = useState<Uint8Array | null>(null);
  const userAnimationFrameRef = useRef<number | null>(null);
  const assistantAnimationFrameRef = useRef<number | null>(null);
  
  // 获取 personality 配置
  const { data: personality } = useQuery({
    queryKey: ['personality', personalityId],
    queryFn: () => personalityApi.getPersonality(personalityId!),
    enabled: !!personalityId,
  });

  /**
   * 加载配置
   */
  const loadConfig = useCallback(async (): Promise<OpenAIConfig> => {
    if (configRef.current) {
      return configRef.current;
    }
    
    const config = await configApi.getOpenAIConfig();
    configRef.current = config;
    return config;
  }, []);

  /**
   * 初始化用户音频可视化
   */
  const initUserAudioVisualization = useCallback(async (stream: MediaStream) => {
    try {
      // 检查 AudioContext 状态
      let audioContext: AudioContext;
      try {
        audioContext = new AudioContext({ sampleRate: 24000 });
        if (audioContext.state === 'suspended') {
          await audioContext.resume();
        }
      } catch (e) {
        console.error('创建 AudioContext 失败:', e);
        return;
      }
      
      const source = audioContext.createMediaStreamSource(stream);
      
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.3;
      userAnalyserRef.current = analyser;
      
      source.connect(analyser);
      
      // 启动用户音频可视化
      const updateUserAudioVisualization = () => {
        if (!userAnalyserRef.current || !isCallingRef.current) {
          return;
        }
        
        try {
          const bufferLength = userAnalyserRef.current.frequencyBinCount;
          const dataArray = new Uint8Array(bufferLength);
          userAnalyserRef.current.getByteFrequencyData(dataArray);
          
          setUserFrequencyData(dataArray);
          
          userAnimationFrameRef.current = requestAnimationFrame(() => {
            updateUserAudioVisualization();
          }) as any;
        } catch (err) {
          console.error('更新用户音频可视化失败:', err);
        }
      };
      
      // 延迟启动，确保 isCallingRef 已设置
      setTimeout(() => {
        updateUserAudioVisualization();
      }, 200);
    } catch (err: any) {
      console.error('初始化用户音频可视化失败:', err);
    }
  }, []);

  /**
   * 初始化助手音频可视化
   */
  const initAssistantAudioVisualization = useCallback((audioElement: HTMLAudioElement) => {
    try {
      // 清理之前的连接（如果存在）
      if (assistantSourceRef.current) {
        try {
          assistantSourceRef.current.disconnect();
        } catch (e) {
          // 忽略断开连接错误
        }
        assistantSourceRef.current = null;
      }
      
      if (assistantAudioContextRef.current) {
        try {
          assistantAudioContextRef.current.close();
        } catch (e) {
          // 忽略关闭错误
        }
        assistantAudioContextRef.current = null;
      }
      
      // 检查 AudioContext 状态
      let audioContext: AudioContext;
      try {
        audioContext = new AudioContext({ sampleRate: 24000 });
        assistantAudioContextRef.current = audioContext;
        if (audioContext.state === 'suspended') {
          audioContext.resume();
        }
      } catch (e) {
        console.error('创建助手 AudioContext 失败:', e);
        return;
      }
      
      // 优先使用 srcObject 的 MediaStream（更可靠，不会出现"already connected"错误）
      // 注意：不要同时使用 MediaStreamSource 和 MediaElementSource，会导致重复播放
      let source: MediaElementAudioSourceNode | MediaStreamAudioSourceNode;
      
      if (audioElement.srcObject instanceof MediaStream) {
        // 如果 audioElement 有 srcObject（MediaStream），直接使用它
        try {
          const streamSource = audioContext.createMediaStreamSource(audioElement.srcObject);
          assistantSourceRef.current = streamSource as any;
          source = streamSource;
        } catch (e: any) {
          console.error('从 MediaStream 创建音频源失败:', e);
          throw e;
        }
      } else {
        // 如果没有 srcObject，尝试从 audioElement 创建 MediaElementSource
        try {
          source = audioContext.createMediaElementSource(audioElement);
          assistantSourceRef.current = source;
        } catch (e: any) {
          if (e.name === 'InvalidStateError' && e.message.includes('already connected')) {
            // 音频元素已被连接，跳过可视化（避免重复播放）
            return;
          } else {
            throw e;
          }
        }
      }
      
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.1;
      analyser.minDecibels = -90;
      analyser.maxDecibels = -10;
      assistantAnalyserRef.current = analyser;
      
      source.connect(analyser);
      analyser.connect(audioContext.destination);
      
      // 启动助手音频可视化
      const updateAssistantAudioVisualization = () => {
        if (!assistantAnalyserRef.current || !isCallingRef.current) {
          return;
        }
        
        try {
          const bufferLength = assistantAnalyserRef.current.frequencyBinCount;
          const dataArray = new Uint8Array(bufferLength);
          assistantAnalyserRef.current.getByteFrequencyData(dataArray);
          
          setAssistantFrequencyData(dataArray);
          
          assistantAnimationFrameRef.current = requestAnimationFrame(() => {
            updateAssistantAudioVisualization();
          }) as any;
        } catch (err) {
          console.error('更新助手音频可视化失败:', err);
          // 如果出错，停止更新
          if (assistantAnimationFrameRef.current) {
            cancelAnimationFrame(assistantAnimationFrameRef.current);
            assistantAnimationFrameRef.current = null;
          }
        }
      };
      
      // 立即启动可视化循环
      if (isCallingRef.current && assistantAnalyserRef.current) {
        updateAssistantAudioVisualization();
      } else {
        // 延迟启动，等待条件满足
        setTimeout(() => {
          if (isCallingRef.current && assistantAnalyserRef.current) {
            updateAssistantAudioVisualization();
          }
      }, 200);
      }
    } catch (err: any) {
      console.error('初始化助手音频可视化失败:', err);
    }
  }, []);

  /**
   * 连接 Voice Agent
   */
  const connect = useCallback(async () => {
    try {
      setError(null);
      
      // 获取配置
      const config = await loadConfig();
      
      // 获取 ephemeral client key (临时密钥)
      const realtimeToken = await configApi.getRealtimeToken();
      
      // 获取全局默认配置（来自 realtime.yaml）
      const globalConfig = await configApi.getRealtimeConfig();
      
      // 获取 personality 配置
      const personalityConfig = (personality as any)?.config || {};
      const voiceConfig = personalityConfig?.voice || {};
      const personalityRealtimeConfig = voiceConfig?.realtime || {};
      
      // 合并配置：personality 配置 > 全局配置 > 代码默认值
      const voice = personalityRealtimeConfig.voice || globalConfig.voice || 'shimmer';
      const instructions = personalityRealtimeConfig.instructions || personalityConfig?.ai?.system_prompt || 'You are a helpful assistant.';
      
      console.log('🎙️ Realtime Voice 配置:', {
        global: globalConfig.voice,
        personality: personalityRealtimeConfig.voice,
        final: voice,
      });
      
      // 创建 RealtimeAgent
      const agent = new RealtimeAgent({
        name: 'cozychat-agent',
        instructions: instructions,
        voice: voice,
      });
      
      // 创建用户音频流（用于可视化）
      // 我们需要自己创建 mediaStream，这样可以从它获取音频数据用于可视化
      const userMediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 24000,
          echoCancellation: true,
          noiseSuppression: true,
        }
      });
      userMediaStreamRef.current = userMediaStream;
      
      // 创建助手音频元素（仅用于可视化，不自动播放）
      // 注意：WebRTC transport 会自动处理音频播放，我们只需要可视化
      // 关键：必须静音，否则会和 transport 的播放重叠，导致回声
      const assistantAudioElement = new Audio();
      assistantAudioElement.autoplay = false; // 禁用自动播放
      assistantAudioElement.muted = true; // 静音！只用于可视化，不用于播放（避免与 transport 播放重叠）
      assistantAudioElementRef.current = assistantAudioElement;
      
      // 创建 WebRTC 传输层（浏览器环境）
      // 传递我们自己创建的 mediaStream 和 audioElement，以便用于可视化
      // 注意：baseUrl 需要是完整的端点 URL，包括 /v1/realtime/calls 路径
      // SDK 不会自动添加路径，需要手动指定完整 URL
      let baseUrl = config.base_url;
      if (baseUrl.endsWith('/v1')) {
        baseUrl = baseUrl.slice(0, -3);
      } else if (baseUrl.endsWith('/v1/')) {
        baseUrl = baseUrl.slice(0, -4);
      }
      // 确保 baseUrl 不以 / 结尾
      baseUrl = baseUrl.replace(/\/$/, '');
      // 添加 /v1/realtime/calls 路径（WebRTC 端点）
      const webrtcEndpoint = `${baseUrl}/v1/realtime/calls`;
      
      const transport = new OpenAIRealtimeWebRTC({
        baseUrl: webrtcEndpoint, // 使用完整的端点 URL（例如：https://oneapi.naivehero.top/v1/realtime/calls）
        // 不使用 useInsecureApiKey，因为我们现在有 ephemeral key
        mediaStream: userMediaStream, // 使用我们自己创建的音频流
        audioElement: assistantAudioElement, // 使用我们自己创建的音频元素
      });
      
      // 创建 RealtimeSession
      // 注意：转录配置已经在后端创建 ephemeral token 时完成
      const session = new RealtimeSession(agent, {
        apiKey: realtimeToken.token, // 使用后端生成的 ephemeral key（已包含转录配置）
        transport: transport, // 使用自定义的 WebRTC 传输层
        model: realtimeToken.model, // 使用后端返回的模型名称
      });
      
      // 保存 webrtcEndpoint 到 session 的某个地方，以便在 connect 时使用
      (session as any).__webrtcEndpoint = webrtcEndpoint;
      
      // ========== 正确的事件监听方式 ==========
      // 根据社区讨论：https://community.openai.com/t/input-audio-transcription-in-realtime-api/1007401/5
      // 正确的事件名是：conversation.item.input_audio_transcription.completed
      
      // 1. 用户语音转文本事件（完成）
      (session as any).on('conversation.item.input_audio_transcription.completed', (event: any) => {
        const transcript = event?.transcript;
        if (transcript && typeof transcript === 'string' && transcript.trim() && callbacks?.onUserTranscript) {
          callbacks.onUserTranscript(transcript);
        }
      });
      
      // 2. 从 history_added 和 history_updated 提取文本
      // 用于去重的 Set（存储已处理的消息ID和文本内容）
      const processedMessageIds = new Set<string>();
      const processedTexts = new Set<string>(); // 存储已处理的文本内容（消息ID:文本内容）
      
      // 提取用户转录文本的辅助函数
      const extractUserTranscript = (item: any): string | null => {
        // 1. 首先检查 item 的直接字段
        if (item.transcript && typeof item.transcript === 'string' && item.transcript.trim()) {
          return item.transcript.trim();
        }
        if (item.input_audio_transcript && typeof item.input_audio_transcript === 'string' && item.input_audio_transcript.trim()) {
          return item.input_audio_transcript.trim();
        }
        
        // 2. 检查 content 数组（转录文本在这里）
        if (Array.isArray(item.content)) {
          for (const c of item.content) {
            // 优先检查 input_audio 类型（这是用户语音输入）
            if (c.type === 'input_audio') {
              if (c.transcript && typeof c.transcript === 'string' && c.transcript.trim()) {
                return c.transcript.trim();
              }
              if (c.input_audio_transcript && typeof c.input_audio_transcript === 'string' && c.input_audio_transcript.trim()) {
                return c.input_audio_transcript.trim();
              }
              if (c.text && typeof c.text === 'string' && c.text.trim()) {
                return c.text.trim();
              }
            }
            // 检查任何包含 transcript 的项（备用）
            if (c.transcript && typeof c.transcript === 'string' && c.transcript.trim()) {
              return c.transcript.trim();
            }
            // 检查 text 类型（某些情况下转录可能以 text 形式存在）
            if (c.type === 'text' && c.text && typeof c.text === 'string' && c.text.trim()) {
              return c.text.trim();
            }
          }
        }
        
        // 3. 如果 content 是字符串，直接返回（备用）
        if (typeof item.content === 'string' && item.content.trim()) {
          return item.content.trim();
        }
        
        return null;
      };
      
      // 提取助手文本的辅助函数
      const extractAssistantText = (item: any): string | null => {
        // 检查 content 数组
        if (Array.isArray(item.content)) {
          for (const c of item.content) {
            if (c.type === 'text' && c.text && typeof c.text === 'string') {
              return c.text.trim();
            }
            if (c.type === 'output_audio' && c.transcript && typeof c.transcript === 'string') {
              return c.transcript.trim();
            }
          }
        }
        
        // 检查直接字段
        if (item.text && typeof item.text === 'string') {
          return item.text.trim();
        }
        
        return null;
      };
      
      session.on('history_added', (item: any) => {
        if (item.type === 'message') {
          const messageId = item.itemId || item.id;
          if (!messageId) {
            return; // 没有有效的消息ID，跳过
          }
          
          // 检查是否已处理过这个消息ID
          if (processedMessageIds.has(messageId)) {
            return;
          }
          
          if (item.role === 'user') {
            const transcript = extractUserTranscript(item);
            if (transcript && callbacks?.onUserTranscript) {
              const textKey = `${messageId}:${transcript}`;
              if (!processedTexts.has(textKey)) {
                processedMessageIds.add(messageId);
                processedTexts.add(textKey);
              callbacks.onUserTranscript(transcript);
              }
            }
          } else if (item.role === 'assistant') {
            const text = extractAssistantText(item);
            if (text && callbacks?.onAssistantTranscript) {
              const textKey = `${messageId}:${text}`;
              if (!processedTexts.has(textKey)) {
                processedMessageIds.add(messageId);
                processedTexts.add(textKey);
              callbacks.onAssistantTranscript(text);
              }
            }
          }
        }
      });
      
      session.on('history_updated', (history: any[]) => {
        // 遍历所有消息，检查是否有新的转录文本
        history.forEach((item: any) => {
          if (item.type === 'message') {
            const messageId = item.itemId || item.id;
            if (!messageId) {
              return; // 没有有效的消息ID，跳过
            }
            
            if (item.role === 'user') {
              const transcript = extractUserTranscript(item);
              if (transcript) {
                // 使用消息ID和文本内容作为唯一标识
                const textKey = `${messageId}:${transcript}`;
                
                // 如果之前没有处理过这个文本
                if (!processedTexts.has(textKey) && callbacks?.onUserTranscript) {
                  processedMessageIds.add(messageId);
                  processedTexts.add(textKey);
                callbacks.onUserTranscript(transcript);
                }
              }
            } else if (item.role === 'assistant') {
              const text = extractAssistantText(item);
              if (text) {
                // 使用消息ID和文本内容作为唯一标识
                const textKey = `${messageId}:${text}`;
                
                // 如果之前没有处理过这个文本
                if (!processedTexts.has(textKey) && callbacks?.onAssistantTranscript) {
                  processedMessageIds.add(messageId);
                  processedTexts.add(textKey);
                callbacks.onAssistantTranscript(text);
                }
              }
            }
          }
        });
      });
      
      sessionRef.current = session;
      setIsConnected(true);
      
      console.log('Voice Agent 连接成功');
    } catch (err: any) {
      console.error('连接 Voice Agent 失败:', err);
      setError(err.message || '连接失败');
      throw err;
    }
  }, [loadConfig, personality, callbacks]);

  /**
   * 断开连接
   */
  const disconnect = useCallback(() => {
    try {
      if (sessionRef.current) {
        sessionRef.current.close(); // 使用 close() 方法断开连接
        sessionRef.current = null;
      }
      
      // 停止用户音频流
      if (userMediaStreamRef.current) {
        userMediaStreamRef.current.getTracks().forEach(track => track.stop());
        userMediaStreamRef.current = null;
      }
      
      // 停止助手音频元素
      if (assistantAudioElementRef.current) {
        assistantAudioElementRef.current.pause();
        assistantAudioElementRef.current.src = '';
        assistantAudioElementRef.current = null;
      }
      
      // 停止音频可视化
      if (userAnimationFrameRef.current) {
        clearTimeout(userAnimationFrameRef.current as any);
        userAnimationFrameRef.current = null;
      }
      if (assistantAnimationFrameRef.current) {
        clearTimeout(assistantAnimationFrameRef.current as any);
        assistantAnimationFrameRef.current = null;
      }
      
             setUserFrequencyData(null);
             setAssistantFrequencyData(null);
             setIsConnected(false);
             setIsCalling(false);
             isCallingRef.current = false;
      
      console.log('断开 Voice Agent 连接');
    } catch (err) {
      console.error('断开连接失败:', err);
    }
  }, []);

  /**
   * 开始通话
   */
  const startCall = useCallback(async () => {
    if (!isConnected) {
      await connect();
    }
    
    try {
      if (!sessionRef.current) {
        throw new Error('Voice Agent 未连接');
      }
      
      // 获取 ephemeral key（如果还没有）
      const realtimeToken = await configApi.getRealtimeToken();
      
      // 获取 WebRTC 端点 URL（从 transport 或 session 中获取）
      // 注意：不要传递 url 参数，让 transport 使用它自己的 baseUrl
      // 如果传递了 url，会覆盖 transport 的 baseUrl，导致路径不正确
      const webrtcEndpoint = (sessionRef.current as any).__webrtcEndpoint;
      
      // 检查 transport 的内部状态
      const currentTransport = sessionRef.current?.transport;
      let transportInternalUrl = 'N/A';
      if (currentTransport instanceof OpenAIRealtimeWebRTC) {
        // 尝试获取 transport 的内部 URL（通过反射或直接访问）
        try {
          // @ts-ignore - 访问私有属性
          transportInternalUrl = currentTransport['#url'] || '无法访问';
        } catch (e) {
          transportInternalUrl = '无法访问私有属性';
        }
      }
      
      try {
        await sessionRef.current.connect({
          apiKey: realtimeToken.token,
          model: realtimeToken.model,
        });
      } catch (connectErr: any) {
        console.error('RealtimeSession 连接失败:', {
          error: connectErr,
          message: connectErr?.message,
          stack: connectErr?.stack,
          webrtcEndpoint: webrtcEndpoint,
          errorName: connectErr?.name,
          errorCause: connectErr?.cause,
        });
        
        // 提供更友好的错误信息
        if (connectErr?.message?.includes('Failed to fetch')) {
          // 检查是否是 CORS 问题
          const isCorsError = connectErr?.message?.includes('CORS') || 
                             connectErr?.stack?.includes('CORS') ||
                             connectErr?.cause?.message?.includes('CORS');
          
          const errorMsg = `WebRTC 连接失败 (Failed to fetch)。

可能的原因：
1. CORS 配置问题 - 服务器未设置正确的 CORS 头部
2. 服务器不支持 /v1/realtime/calls 端点
3. 网络连接问题

调试信息：
- WebRTC 端点: ${webrtcEndpoint}
- Transport 内部 URL: ${transportInternalUrl}
- 是否 CORS 错误: ${isCorsError ? '是' : '否'}

请检查：
1. 浏览器开发者工具的 Network 标签页，查看实际请求的 URL 和响应
2. 服务器是否正确配置了 CORS 头部（Access-Control-Allow-Origin 等）
3. 服务器是否支持 /v1/realtime/calls 端点`;
          setError(errorMsg);
          
          console.error('详细错误信息:', {
            error: connectErr,
            webrtcEndpoint,
            transportInternalUrl,
            isCorsError,
            suggestion: '请打开浏览器开发者工具的 Network 标签页，查看实际请求的详细信息',
          });
        }
        
        throw connectErr;
      }
      
      // 等待连接建立后再初始化音频可视化
      const sessionTransport = sessionRef.current.transport;
      if (sessionTransport instanceof OpenAIRealtimeWebRTC) {
        await new Promise<void>((resolve) => {
          const checkConnection = () => {
            if (sessionTransport.status === 'connected') {
              resolve();
            } else {
              setTimeout(checkConnection, 100);
            }
          };
          checkConnection();
        });
        
        // 从 transport 获取实际的音频流
        // OpenAIRealtimeWebRTC 内部会设置 audioElement.srcObject
        // 我们需要等待这个设置完成
        await new Promise<void>((resolve) => {
          const checkAudioElement = () => {
            if (assistantAudioElementRef.current?.srcObject) {
              resolve();
            } else {
              setTimeout(checkAudioElement, 100);
            }
          };
          setTimeout(() => resolve(), 5000);
          checkAudioElement();
        });
      }
      
      // 先设置 isCalling 状态，这样音频可视化才能正常工作
      setIsCalling(true);
      isCallingRef.current = true;
      
      // 初始化音频可视化
      if (userMediaStreamRef.current) {
        await initUserAudioVisualization(userMediaStreamRef.current);
      }
      
      if (assistantAudioElementRef.current) {
        const initAssistantVisualization = () => {
          if (assistantAudioElementRef.current?.srcObject) {
        initAssistantAudioVisualization(assistantAudioElementRef.current);
          } else {
            setTimeout(initAssistantVisualization, 200);
          }
        };
        setTimeout(initAssistantVisualization, 300);
      }
      
      console.log('开始语音通话');
    } catch (err: any) {
      console.error('开始通话失败:', err);
      setError(err.message || '开始通话失败');
      throw err;
    }
  }, [isConnected, connect, loadConfig, initUserAudioVisualization, initAssistantAudioVisualization]);

  /**
   * 结束通话
   */
  const endCall = useCallback(async () => {
    try {
      if (sessionRef.current) {
        sessionRef.current.close();
        sessionRef.current = null;
      }
      
      // 停止音频可视化
      if (userAnimationFrameRef.current) {
        cancelAnimationFrame(userAnimationFrameRef.current);
        userAnimationFrameRef.current = null;
      }
      if (assistantAnimationFrameRef.current) {
        cancelAnimationFrame(assistantAnimationFrameRef.current);
        assistantAnimationFrameRef.current = null;
      }
      
      // 清理助手音频源和上下文
      if (assistantSourceRef.current) {
        try {
          assistantSourceRef.current.disconnect();
        } catch (e) {
          // 忽略断开连接错误
        }
        assistantSourceRef.current = null;
      }
      
      if (assistantAudioContextRef.current) {
        try {
          assistantAudioContextRef.current.close();
        } catch (e) {
          // 忽略关闭错误
        }
        assistantAudioContextRef.current = null;
      }
      
      // 清理音频流
      if (userMediaStreamRef.current) {
        userMediaStreamRef.current.getTracks().forEach((track) => track.stop());
        userMediaStreamRef.current = null;
      }
      
      setIsCalling(false);
      isCallingRef.current = false;
      setUserFrequencyData(null);
      setAssistantFrequencyData(null);
      
      console.log('结束语音通话');
    } catch (err: any) {
      console.error('结束通话失败:', err);
      setError(err.message || '结束通话失败');
    }
  }, []);

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
