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
      console.log('开始初始化用户音频可视化，stream:', stream, 'tracks:', stream.getTracks().length);
      
      // 检查 AudioContext 状态
      let audioContext: AudioContext;
      try {
        audioContext = new AudioContext({ sampleRate: 24000 });
        if (audioContext.state === 'suspended') {
          await audioContext.resume();
          console.log('AudioContext 已恢复');
        }
      } catch (e) {
        console.error('创建 AudioContext 失败:', e);
        return;
      }
      
      const source = audioContext.createMediaStreamSource(stream);
      
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256; // 增加 fftSize 以获得更好的频率分辨率
      analyser.smoothingTimeConstant = 0.3; // 降低平滑度，提高响应速度
      userAnalyserRef.current = analyser;
      
      source.connect(analyser);
      console.log('用户音频源已连接到分析器');
      
      // 启动用户音频可视化（使用 requestAnimationFrame 提高响应速度）
      const updateUserAudioVisualization = () => {
        if (!userAnalyserRef.current) {
          console.log('用户分析器不存在，停止更新');
          return;
        }
        
        // 检查 isCalling 状态（使用 ref 而不是闭包中的值）
        if (!isCallingRef.current) {
          console.log('不在通话中，停止用户音频可视化');
          return;
        }
        
        try {
          const bufferLength = userAnalyserRef.current.frequencyBinCount;
          const dataArray = new Uint8Array(bufferLength);
          userAnalyserRef.current.getByteFrequencyData(dataArray);
          
          setUserFrequencyData(dataArray);
          
          // 使用 requestAnimationFrame 提高响应速度（约 60fps）
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
      console.log('开始初始化助手音频可视化，audioElement:', audioElement, 'srcObject:', audioElement.srcObject);
      
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
          audioContext.resume().then(() => {
            console.log('助手 AudioContext 已恢复');
          });
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
        console.log('✅ 使用 audioElement.srcObject (MediaStream) 创建音频源', {
          streamId: audioElement.srcObject.id,
          tracks: audioElement.srcObject.getTracks().length,
          active: audioElement.srcObject.active,
        });
        try {
          const streamSource = audioContext.createMediaStreamSource(audioElement.srcObject);
          assistantSourceRef.current = streamSource as any;
          source = streamSource;
        } catch (e: any) {
          console.error('❌ 从 MediaStream 创建音频源失败:', e);
          throw e;
        }
      } else {
        // 如果没有 srcObject，尝试从 audioElement 创建 MediaElementSource
        // 但要注意：如果 audioElement 已经被连接过，会报错
        console.log('⚠️ audioElement 没有 srcObject，尝试创建 MediaElementSource');
        try {
          source = audioContext.createMediaElementSource(audioElement);
          assistantSourceRef.current = source;
        } catch (e: any) {
          if (e.name === 'InvalidStateError' && e.message.includes('already connected')) {
            console.warn('⚠️ 音频元素已被连接，跳过可视化（避免重复播放）');
            // 不抛出错误，只是跳过可视化
            return;
          } else {
            throw e;
          }
        }
      }
      
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 512; // 增加 fftSize 以获得更好的频率分辨率
      analyser.smoothingTimeConstant = 0.1; // 进一步降低平滑度，提高响应速度
      analyser.minDecibels = -90;
      analyser.maxDecibels = -10;
      assistantAnalyserRef.current = analyser;
      
      source.connect(analyser);
      analyser.connect(audioContext.destination);
      console.log('助手音频源已连接到分析器', {
        fftSize: analyser.fftSize,
        frequencyBinCount: analyser.frequencyBinCount,
        smoothingTimeConstant: analyser.smoothingTimeConstant,
      });
      
      // 启动助手音频可视化（使用 requestAnimationFrame 提高响应速度）
      const updateAssistantAudioVisualization = () => {
        if (!assistantAnalyserRef.current) {
          console.log('助手分析器不存在，停止更新');
          return;
        }
        
        // 检查 isCalling 状态（使用 ref 而不是闭包中的值）
        if (!isCallingRef.current) {
          console.log('不在通话中，停止助手音频可视化');
          return;
        }
        
        try {
          const bufferLength = assistantAnalyserRef.current.frequencyBinCount;
          const dataArray = new Uint8Array(bufferLength);
          assistantAnalyserRef.current.getByteFrequencyData(dataArray);
          
          // 计算平均音量和最大值用于调试（仅在开发环境，且节流输出）
          if (process.env.NODE_ENV === 'development') {
            const avgVolume = dataArray.reduce((sum, val) => sum + val, 0) / bufferLength;
            const maxVolume = Math.max(...Array.from(dataArray));
            
            // 节流日志输出（每 500ms 输出一次，或音量变化超过 20%）
            const now = Date.now();
            const lastLogTime = (assistantAnalyserRef.current as any).__lastLogTime || 0;
            const lastAvgVolume = (assistantAnalyserRef.current as any).__lastAvgVolume || 0;
            const volumeChange = Math.abs(avgVolume - lastAvgVolume) / (lastAvgVolume || 1);
            
            if (now - lastLogTime > 500 || volumeChange > 0.2) {
              if (avgVolume > 1 || maxVolume > 5) {
                console.log('🎵 助手音频数据更新:', {
                  平均音量: avgVolume.toFixed(2),
                  最大值: maxVolume,
                  数据长度: bufferLength,
                });
                (assistantAnalyserRef.current as any).__lastLogTime = now;
                (assistantAnalyserRef.current as any).__lastAvgVolume = avgVolume;
              }
            }
          }
          
          setAssistantFrequencyData(dataArray);
          
          // 使用 requestAnimationFrame 提高响应速度（约 60fps）
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
      
      // 立即启动可视化循环（不延迟）
      // 因为 isCallingRef 已经在 startCall 中设置了
      if (isCallingRef.current && assistantAnalyserRef.current) {
        console.log('✅ 立即启动助手音频可视化');
        updateAssistantAudioVisualization();
      } else {
        console.warn('⚠️ 助手音频可视化启动条件不满足，延迟启动', {
          isCalling: isCallingRef.current,
          hasAnalyser: !!assistantAnalyserRef.current,
        });
        // 延迟启动，等待条件满足
        setTimeout(() => {
          if (isCallingRef.current && assistantAnalyserRef.current) {
            console.log('✅ 延迟启动助手音频可视化');
            updateAssistantAudioVisualization();
          } else {
            console.error('❌ 助手音频可视化启动失败', {
              isCalling: isCallingRef.current,
              hasAnalyser: !!assistantAnalyserRef.current,
            });
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
      console.log('获取 Realtime Token 成功:', {
        tokenPrefix: realtimeToken.token.substring(0, 10) + '...',
        url: realtimeToken.url,
        model: realtimeToken.model,
      });
      
      // 获取 personality 配置
      const personalityConfig = (personality as any)?.config || {};
      const voiceConfig = personalityConfig?.voice || {};
      const realtimeConfig = voiceConfig?.realtime || {};
      
      // 获取 instructions（优先使用 realtime.instructions，否则使用 system_prompt）
      const instructions = realtimeConfig.instructions || personalityConfig?.ai?.system_prompt || 'You are a helpful assistant.';
      
      // 创建 RealtimeAgent
      const agent = new RealtimeAgent({
        name: 'cozychat-agent',
        instructions: instructions,
        voice: realtimeConfig.voice || 'shimmer',
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
      const assistantAudioElement = new Audio();
      assistantAudioElement.autoplay = false; // 禁用自动播放，避免重复播放
      assistantAudioElement.muted = false; // 不静音，但由 transport 控制播放
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
      
      console.log('WebRTC Transport 配置:', {
        baseUrl: baseUrl,
        webrtcEndpoint: webrtcEndpoint,
        hasMediaStream: !!userMediaStream,
        hasAudioElement: !!assistantAudioElement,
        useEphemeralKey: true, // 使用 ephemeral key
      });
      
      const transport = new OpenAIRealtimeWebRTC({
        baseUrl: webrtcEndpoint, // 使用完整的端点 URL（例如：https://oneapi.naivehero.top/v1/realtime/calls）
        // 不使用 useInsecureApiKey，因为我们现在有 ephemeral key
        mediaStream: userMediaStream, // 使用我们自己创建的音频流
        audioElement: assistantAudioElement, // 使用我们自己创建的音频元素
      });
      
      // 创建 RealtimeSession，配置输入音频转录
      // 注意：配置格式必须正确，否则转录功能不会启用
      const sessionConfig = {
        inputAudioTranscription: {
          model: 'whisper-1', // 使用 Whisper 模型进行转录
        },
        // 其他可能的配置项
        inputAudioFormat: 'pcm16',
        outputAudioFormat: 'pcm16',
      };
      
      console.log('📋 创建 RealtimeSession，配置:', JSON.stringify(sessionConfig, null, 2));
      
      const session = new RealtimeSession(agent, {
        apiKey: realtimeToken.token, // 使用 ephemeral key 而不是 API key
        transport: transport, // 使用自定义的 WebRTC 传输层
        model: realtimeToken.model,
        // 配置输入音频转录（关键！）
        config: sessionConfig,
      });
      
      // 验证配置是否正确设置
      console.log('📋 Session 创建后，检查配置:', {
        hasConfig: !!(session as any).config,
        config: (session as any).config,
        hasInputAudioTranscription: !!(session as any).config?.inputAudioTranscription,
        sessionKeys: Object.keys(session as any),
      });
      
      // 保存 webrtcEndpoint 到 session 的某个地方，以便在 connect 时使用
      (session as any).__webrtcEndpoint = webrtcEndpoint;
      
      // ========== 正确的事件监听方式 ==========
      // 根据 OpenAI Realtime API 文档，应该使用以下事件：
      
      // 1. 用户语音转文本事件（完成）
      // 注意：这个事件可能不会触发，如果配置不正确或 SDK 版本不支持
      session.on('input_audio_transcription.done', (event: any) => {
        const transcript = event?.transcript || event?.text || event?.content;
        console.log('🎤 input_audio_transcription.done 事件触发:', { 
          transcript, 
          event,
          eventKeys: Object.keys(event || {}),
          fullEvent: JSON.stringify(event, null, 2),
        });
        if (transcript && typeof transcript === 'string' && transcript.trim() && callbacks?.onUserTranscript) {
          console.log('✅ 获取用户转录文本:', transcript);
          callbacks.onUserTranscript(transcript);
        } else {
          console.warn('⚠️ input_audio_transcription.done 事件中没有有效的转录文本:', {
            transcript,
            transcriptType: typeof transcript,
            hasCallback: !!callbacks?.onUserTranscript,
          });
        }
      });
      
      // 监听所有可能的事件，用于调试
      // 注意：某些事件可能不存在，但监听它们不会报错
      const debugEvents = [
        'input_audio_transcription.done',
        'input_audio_transcription.delta',
        'input_audio_transcription.partial',
        'conversation.item.input_audio_transcription.completed',
        'conversation.item.input_audio_transcription.delta',
      ];
      
      debugEvents.forEach((eventName) => {
        try {
          session.on(eventName as any, (event: any) => {
            console.log(`🔍 调试事件 ${eventName} 触发:`, event);
          });
        } catch (e) {
          // 忽略不存在的监听器
        }
      });
      
      // 2. 用户语音转文本事件（增量，可选，用于实时显示）
      session.on('input_audio_transcription.delta', (event: any) => {
        const delta = event?.delta;
        console.log('🎤 input_audio_transcription.delta 事件:', { delta, event });
        // 可以用于实时显示转录过程
      });
      
      // 3. 助手文本回复事件（完成）
      session.on('response.text.done', (event: any) => {
        const text = event?.text || event?.content;
        console.log('🤖 response.text.done 事件:', { text, event });
              if (text && typeof text === 'string' && text.trim() && callbacks?.onAssistantTranscript) {
          console.log('✅ 获取助手文本:', text);
                callbacks.onAssistantTranscript(text);
              }
      });
      
      // 4. 助手文本回复事件（增量，可选）
      session.on('response.text.delta', (event: any) => {
        const delta = event?.delta;
        console.log('🤖 response.text.delta 事件:', { delta, event });
        // 可以用于实时显示文本生成过程
      });
      
      // 5. 从 history_added 和 history_updated 提取文本（主要方式，因为专用事件可能不工作）
      // 用于去重的 Set（存储已处理的消息ID和文本内容）
      const processedMessageIds = new Set<string>();
      const processedTexts = new Set<string>(); // 存储已处理的文本内容（消息ID:文本内容）
      
      // 提取用户转录文本的辅助函数
      const extractUserTranscript = (item: any): string | null => {
        // 首先检查 item 的直接字段
        if (item.transcript && typeof item.transcript === 'string' && item.transcript.trim()) {
          return item.transcript.trim();
        }
        if (item.input_audio_transcript && typeof item.input_audio_transcript === 'string' && item.input_audio_transcript.trim()) {
          return item.input_audio_transcript.trim();
        }
        
        // 检查 content 数组
        if (Array.isArray(item.content)) {
          for (const c of item.content) {
            // 优先检查 input_audio 类型
            if (c.type === 'input_audio') {
              if (c.transcript && typeof c.transcript === 'string' && c.transcript.trim()) {
                return c.transcript.trim();
              }
              // 检查 input_audio 的其他可能字段
              if (c.input_audio_transcript && typeof c.input_audio_transcript === 'string' && c.input_audio_transcript.trim()) {
                return c.input_audio_transcript.trim();
              }
            }
            // 检查任何包含 transcript 的项
            if (c.transcript && typeof c.transcript === 'string' && c.transcript.trim()) {
              return c.transcript.trim();
            }
            // 检查 text 类型（某些情况下转录可能以 text 形式存在）
            if (c.type === 'text' && c.text && typeof c.text === 'string' && c.text.trim()) {
              return c.text.trim();
            }
          }
        }
        
        // 如果 content 是字符串，直接返回
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
                console.log('✅ 从 history_added 获取用户转录:', transcript, '消息ID:', messageId);
                callbacks.onUserTranscript(transcript);
              }
            } else {
              // 如果没有转录文本，输出调试信息
              console.log('⚠️ history_added - 用户消息没有转录文本:', {
                messageId,
                content: item.content,
                status: item.status,
                item: JSON.stringify(item, null, 2),
              });
            }
          } else if (item.role === 'assistant') {
            const text = extractAssistantText(item);
            if (text && callbacks?.onAssistantTranscript) {
              const textKey = `${messageId}:${text}`;
              if (!processedTexts.has(textKey)) {
                processedMessageIds.add(messageId);
                processedTexts.add(textKey);
                console.log('✅ 从 history_added 获取助手文本:', text, '消息ID:', messageId);
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
                  console.log('✅ 从 history_updated 获取用户转录:', transcript, '消息ID:', messageId);
                  callbacks.onUserTranscript(transcript);
                }
              } else {
                // 如果没有转录文本，输出调试信息
                console.log('⚠️ 用户消息没有转录文本:', {
                  messageId,
                  content: item.content,
                  status: item.status,
                });
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
                  console.log('✅ 从 history_updated 获取助手文本:', text, '消息ID:', messageId);
                  callbacks.onAssistantTranscript(text);
                }
              }
            }
          }
        });
      });
      
      // 音频转录文本增量更新事件（如果 SDK 支持）
      // 注意：这个事件在文本还在生成时触发，可以用于实时显示
      // 但最终文本会在 history_added 或 history_updated 中获取
      // session.on('audio_transcript_delta', (_event: any) => {
      //   // event.deltaEvent 包含 itemId, delta, responseId
      //   // 可以根据 itemId 判断是用户还是助手
      // });
      
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
      
      console.log('准备连接 RealtimeSession:', {
        hasEphemeralKey: !!realtimeToken.token,
        tokenPrefix: realtimeToken.token.substring(0, 10) + '...',
        model: realtimeToken.model,
        webrtcEndpoint: webrtcEndpoint,
        transportInternalUrl: transportInternalUrl,
        transportType: currentTransport?.constructor?.name,
      });
      
      try {
        console.log('开始连接 RealtimeSession...');
        console.log('Transport 状态:', {
          status: currentTransport instanceof OpenAIRealtimeWebRTC ? currentTransport.status : 'N/A',
          hasTransport: !!currentTransport,
        });
        
        // 不传递 url 参数，让 transport 使用它自己的 baseUrl（webrtcEndpoint）
        // 尝试在 connect 时也传递配置（某些 SDK 版本可能需要这样做）
        const connectConfig = {
          input_audio_transcription: {
            model: 'whisper-1',
          },
        };
        
        console.log('📋 连接时传递配置:', JSON.stringify(connectConfig, null, 2));
        
        await sessionRef.current.connect({
          apiKey: realtimeToken.token, // 使用 ephemeral key
          model: realtimeToken.model,
          // 尝试在 connect 时传递配置
          config: connectConfig as any,
          // 不传递 url，使用 transport 的 baseUrl
        });
        console.log('RealtimeSession 连接成功');
        
        // 输出当前 session 的配置，用于调试
        console.log('📋 Session 连接后配置检查:', {
          hasConfig: !!(sessionRef.current as any).config,
          config: (sessionRef.current as any).config,
          hasInputAudioTranscription: !!(sessionRef.current as any).config?.inputAudioTranscription,
          sessionKeys: Object.keys(sessionRef.current as any),
          // 检查是否有其他配置相关的属性
          hasSessionConfig: !!(sessionRef.current as any).sessionConfig,
          hasSettings: !!(sessionRef.current as any).settings,
        });
        
        // 尝试通过 transport 发送 session.update 消息来启用转录
        // 注意：这是直接操作 transport，可能不是标准方式，但值得尝试
        try {
          const currentTransport = sessionRef.current?.transport;
          if (currentTransport && typeof (currentTransport as any).send === 'function') {
            const updateMessage = {
              type: 'session.update',
              session: {
                input_audio_transcription: {
                  model: 'whisper-1',
                },
              },
            };
            console.log('📤 尝试通过 transport.send 发送 session.update:', updateMessage);
            (currentTransport as any).send(updateMessage);
            console.log('✅ session.update 消息已发送');
          } else {
            console.warn('⚠️ transport 没有 send 方法，无法发送 session.update');
            // 尝试其他方式
            if (currentTransport && typeof (currentTransport as any).dispatch === 'function') {
              console.log('📤 尝试通过 transport.dispatch 发送 session.update');
              (currentTransport as any).dispatch({
                type: 'session.update',
                session: {
                  input_audio_transcription: {
                    model: 'whisper-1',
                  },
                },
              });
            }
          }
        } catch (updateErr: any) {
          console.warn('⚠️ 发送 session.update 失败:', {
            error: updateErr,
            message: updateErr?.message,
          });
        }
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
              console.log('助手音频元素已设置 srcObject');
              resolve();
            } else {
              setTimeout(checkAudioElement, 100);
            }
          };
          // 最多等待 5 秒
          setTimeout(() => {
            console.warn('等待助手音频元素超时');
            resolve();
          }, 5000);
          checkAudioElement();
        });
      }
      
      // 先设置 isCalling 状态，这样音频可视化才能正常工作
      setIsCalling(true);
      isCallingRef.current = true;
      
      // 初始化音频可视化
      // 使用我们之前创建的 mediaStream（用户音频）
      if (userMediaStreamRef.current) {
        console.log('初始化用户音频可视化，stream tracks:', userMediaStreamRef.current.getTracks().length);
        await initUserAudioVisualization(userMediaStreamRef.current);
      }
      
      // 使用 transport 设置的 audioElement（助手音频）
      // 延迟一点，确保音频流已经设置好
      if (assistantAudioElementRef.current) {
        console.log('初始化助手音频可视化，srcObject:', !!assistantAudioElementRef.current.srcObject);
        
        // 等待音频流设置完成，然后初始化可视化
        const initAssistantVisualization = () => {
          if (assistantAudioElementRef.current?.srcObject) {
            console.log('助手音频流已准备好，开始初始化可视化');
        initAssistantAudioVisualization(assistantAudioElementRef.current);
          } else {
            // 如果还没有 srcObject，等待一下再试
            console.log('助手音频流尚未准备好，等待...');
            setTimeout(initAssistantVisualization, 200);
          }
        };
        
        // 延迟初始化，确保 isCallingRef 已设置且音频流已准备好
        setTimeout(initAssistantVisualization, 300);
      }
      
      // 另外，尝试从 transport 直接获取音频流（如果支持）
      if (sessionTransport instanceof OpenAIRealtimeWebRTC) {
        try {
          // 检查 transport 是否有 getMediaStream 方法
          const transportStream = (sessionTransport as any).getMediaStream?.();
          if (transportStream instanceof MediaStream) {
            console.log('从 transport 获取音频流成功，tracks:', transportStream.getTracks().length);
            // 可以尝试使用这个流进行可视化（作为备选方案）
          }
        } catch (e) {
          console.warn('无法从 transport 获取音频流:', e);
        }
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
