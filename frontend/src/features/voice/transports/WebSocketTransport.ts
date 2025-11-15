/**
 * WebSocket 传输层
 * 
 * 实现 ITransport 接口，封装 WebSocket 连接相关逻辑
 * 
 * 注意：OpenAI Agents SDK 可能没有提供 OpenAIRealtimeWebSocket 类
 * 这里需要自己实现一个符合 SDK 要求的 transport 对象
 */

import type { ITransport, TransportStatus } from './TransportInterface';

/**
 * WebSocket 传输层配置
 */
export interface WebSocketTransportConfig {
  /** WebSocket URL（从后端获取） */
  wsUrl?: string;
  /** 基础 URL（用于构建 WebSocket URL） */
  baseUrl?: string;
  /** API密钥（ephemeral token） */
  apiKey?: string;
  /** 用户媒体流 */
  mediaStream?: MediaStream;
  /** 助手音频元素 */
  audioElement?: HTMLAudioElement;
}

/**
 * WebSocket 传输层类
 * 
 * 注意：这是一个临时实现，需要根据 OpenAI Agents SDK 的实际要求调整
 */
export class WebSocketTransport implements ITransport {
  public readonly type = 'websocket' as const;
  public status: TransportStatus = 'disconnected';

  private websocket: WebSocket | null = null;
  private mediaStream: MediaStream | null = null;
  private audioElement: HTMLAudioElement | null = null;
  private config: WebSocketTransportConfig;
  private eventListeners: Map<string, Set<(...args: any[]) => void>> = new Map();

  constructor(config: WebSocketTransportConfig) {
    this.config = config;
  }

  /**
   * 连接传输层
   */
  async connect(config: Record<string, any>): Promise<void> {
    try {
      this.status = 'connecting';

      // 1. 获取 WebSocket URL
      let wsUrl = this.config.wsUrl;
      if (!wsUrl && this.config.baseUrl) {
        // 从 baseUrl 构建 WebSocket URL
        let baseUrl = this.config.baseUrl;
        // 移除尾部 /v1 或 /v1/
        if (baseUrl.endsWith('/v1')) {
          baseUrl = baseUrl.slice(0, -3);
        } else if (baseUrl.endsWith('/v1/')) {
          baseUrl = baseUrl.slice(0, -4);
        }
        // 转换为 WebSocket URL
        baseUrl = baseUrl.replace(/^https?:\/\//, 'wss://');
        baseUrl = baseUrl.replace(/^ws:\/\//, 'wss://');
        // 添加 /v1/realtime 路径
        wsUrl = `${baseUrl.replace(/\/$/, '')}/v1/realtime`;
      }

      if (!wsUrl) {
        throw new Error('WebSocket URL 未提供');
      }

      // 2. 创建用户音频流（如果未提供）
      if (!this.config.mediaStream) {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: 1,
            sampleRate: 24000,
            echoCancellation: true,
            noiseSuppression: true,
          },
        });
      } else {
        this.mediaStream = this.config.mediaStream;
      }

      // 3. 创建助手音频元素（如果未提供）
      if (!this.config.audioElement) {
        this.audioElement = new Audio();
        this.audioElement.autoplay = true; // WebSocket 需要手动播放
        this.audioElement.muted = false;   // WebSocket 需要播放音频
      } else {
        this.audioElement = this.config.audioElement;
      }

      // 4. 创建 WebSocket 连接
      // 注意：OpenAI Realtime API 的 WebSocket 连接需要使用特定的协议和认证方式
      const apiKey = this.config.apiKey || config.apiKey;
      if (!apiKey) {
        throw new Error('API key 未提供');
      }

      // 构建 WebSocket URL
      // 注意：OpenAI Realtime API 的 WebSocket URL 格式：
      // wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-...
      // API key 通过 WebSocket 子协议传递，而不是 URL 参数
      // 参考：https://platform.openai.com/docs/api-reference/realtime
      const finalWsUrl = wsUrl; // 使用后端返回的完整 URL（已包含 model 参数）

      console.log('[WebSocketTransport] 准备连接 WebSocket:', {
        url: finalWsUrl,
        hasApiKey: !!apiKey,
        apiKeyPrefix: apiKey ? apiKey.substring(0, 10) + '...' : 'none',
      });

      // 创建 WebSocket 连接，使用 API key 作为子协议
      // 注意：OpenAI Realtime API 使用 'openai-insecure-api-key.{apiKey}' 格式
      // 参考：https://platform.openai.com/docs/guides/realtime-conversations#handling-audio-with-websockets
      // 正确的格式是：'openai-insecure-api-key.{apiKey}'，而不是两个独立的字符串
      try {
        // ✅ 关键修复：使用正确的子协议格式
        // 格式：'openai-insecure-api-key.{apiKey}'，而不是 ['openai-insecure-api-key', apiKey]
        const protocols = [
          'realtime',
          `openai-insecure-api-key.${apiKey}`,
          'openai-beta.realtime-v1',
        ];
        this.websocket = new WebSocket(finalWsUrl, protocols);
        console.log('[WebSocketTransport] 使用子协议创建 WebSocket:', protocols.map(p => p.substring(0, 30) + '...'));
      } catch (error) {
        console.error('[WebSocketTransport] 创建 WebSocket 失败:', error);
        throw new Error(`创建 WebSocket 失败: ${error}`);
      }

      // 等待连接建立
      await new Promise<void>((resolve, reject) => {
        if (!this.websocket) {
          reject(new Error('WebSocket 未创建'));
          return;
        }

        const timeout = setTimeout(() => {
          console.error('[WebSocketTransport] WebSocket 连接超时');
          if (this.websocket) {
            this.websocket.close();
          }
          reject(new Error('WebSocket 连接超时'));
        }, 10000);

        this.websocket.onopen = () => {
          console.log('[WebSocketTransport] WebSocket 连接已建立');
          clearTimeout(timeout);
          resolve();
        };

        this.websocket.onerror = (error) => {
          console.error('[WebSocketTransport] WebSocket 连接错误:', {
            error,
            readyState: this.websocket?.readyState,
            url: finalWsUrl,
          });
          clearTimeout(timeout);
          // 获取更详细的错误信息
          const errorMessage = error instanceof Error 
            ? error.message 
            : `WebSocket 连接失败 (readyState: ${this.websocket?.readyState})`;
          reject(new Error(errorMessage));
        };

        this.websocket.onclose = (event) => {
          console.error('[WebSocketTransport] WebSocket 连接已关闭:', {
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean,
          });
          if (event.code !== 1000) {
            // 非正常关闭
            clearTimeout(timeout);
            reject(new Error(`WebSocket 连接关闭: ${event.code} ${event.reason || '未知原因'}`));
          }
        };
      });

      // 5. 设置事件监听
      this.setupEventListeners();

      this.status = 'connected';
      console.log('[WebSocketTransport] WebSocket传输层已连接');
    } catch (error) {
      this.status = 'error';
      console.error('[WebSocketTransport] 连接失败:', error);
      throw error;
    }
  }

  /**
   * 设置事件监听
   */
  private setupEventListeners(): void {
    if (!this.websocket) {
      return;
    }

    this.websocket.onmessage = (event) => {
      // 处理接收到的消息
      // 注意：需要根据 OpenAI Realtime API 的消息格式解析
      console.log('[WebSocketTransport] 收到 WebSocket 消息:', {
        type: typeof event.data,
        isString: typeof event.data === 'string',
        isArrayBuffer: event.data instanceof ArrayBuffer,
        isBlob: event.data instanceof Blob,
        dataLength: event.data?.length || event.data?.byteLength || 'unknown',
        preview: typeof event.data === 'string' ? event.data.substring(0, 100) : 'binary',
      });
      
      try {
        // 尝试解析为 JSON
        const data = typeof event.data === 'string' 
          ? JSON.parse(event.data)
          : JSON.parse(new TextDecoder().decode(event.data));
        console.log('[WebSocketTransport] 解析为 JSON:', data);
        // 触发相应的事件
        this.emit('message', data);
      } catch (error) {
        // 可能是二进制数据（音频数据）
        console.log('[WebSocketTransport] 解析为二进制数据（音频）');
        this.emit('audio', event.data);
        
        // 如果是音频数据，需要播放
        if (this.audioElement && event.data instanceof ArrayBuffer) {
          // 将 ArrayBuffer 转换为 Blob 并播放
          const blob = new Blob([event.data], { type: 'audio/pcm' });
          const url = URL.createObjectURL(blob);
          this.audioElement.src = url;
          this.audioElement.play().catch((err) => {
            console.error('[WebSocketTransport] 播放音频失败:', err);
          });
        }
      }
    };

    this.websocket.onerror = (error) => {
      console.error('[WebSocketTransport] WebSocket 错误:', error);
      this.emit('error', error);
    };

    this.websocket.onclose = () => {
      console.log('[WebSocketTransport] WebSocket 连接已关闭');
      this.status = 'disconnected';
      this.emit('close');
    };
  }

  /**
   * 触发事件
   */
  private emit(event: string, ...args: any[]): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach((listener) => {
        try {
          listener(...args);
        } catch (error) {
          console.error(`[WebSocketTransport] 事件监听器错误 (${event}):`, error);
        }
      });
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    // 停止用户音频流
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    // 停止助手音频
    if (this.audioElement) {
      this.audioElement.pause();
      this.audioElement.src = '';
      this.audioElement = null;
    }

    // 关闭 WebSocket 连接
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }

    // 清理事件监听器
    this.eventListeners.clear();

    this.status = 'disconnected';
    console.log('[WebSocketTransport] 已断开连接');
  }

  /**
   * 获取用户音频流
   */
  getUserMediaStream(): MediaStream | null {
    return this.mediaStream;
  }

  /**
   * 获取助手音频流
   */
  getAssistantAudioStream(): HTMLAudioElement | MediaStream | null {
    return this.audioElement;
  }

  /**
   * 监听事件
   */
  on(event: string, callback: (...args: any[]) => void): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, new Set());
    }
    this.eventListeners.get(event)!.add(callback);
  }

  /**
   * 取消监听事件
   */
  off(event: string, callback: (...args: any[]) => void): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.delete(callback);
    }
  }

  /**
   * 获取底层传输对象
   * 
   * 注意：这个对象需要符合 OpenAI Agents SDK 的要求
   * RealtimeSession.connect() 会调用 transport.connect() 方法
   */
  getUnderlyingTransport(): any {
    // 返回一个符合 SDK 要求的 transport 对象
    // 必须实现 connect() 方法，因为 RealtimeSession.connect() 会调用它
    // 注意：这个对象需要模拟 OpenAIRealtimeWebRTC 的接口
    
    // 使用闭包保存 WebSocketTransport 实例的引用
    const self = this;
    
    const transport = {
      type: 'websocket',
      websocket: this.websocket,
      // ✅ 关键：必须实现 connect() 方法
      // RealtimeSession.connect() 会调用这个方法
      connect: async (_config?: any) => {
        console.log('[WebSocketTransport] getUnderlyingTransport().connect() 被调用');
        // 如果 WebSocket 已经连接，直接返回
        if (self.websocket && self.websocket.readyState === WebSocket.OPEN) {
          console.log('[WebSocketTransport] WebSocket 已连接，跳过连接');
          return;
        }
        
        // 如果 WebSocket 未连接或正在连接，等待连接完成
        if (self.websocket && self.websocket.readyState === WebSocket.CONNECTING) {
          console.log('[WebSocketTransport] WebSocket 正在连接，等待完成...');
          await new Promise<void>((resolve, reject) => {
            if (!self.websocket) {
              reject(new Error('WebSocket 未创建'));
              return;
            }
            
            const timeout = setTimeout(() => {
              reject(new Error('WebSocket 连接超时'));
            }, 10000);
            
            // 保存原有的事件处理器
            const originalOnOpen = self.websocket.onopen;
            const originalOnError = self.websocket.onerror;
            
            self.websocket.onopen = function(event) {
              clearTimeout(timeout);
              if (originalOnOpen && self.websocket) {
                originalOnOpen.call(self.websocket, event);
              }
              resolve();
            };
            
            self.websocket.onerror = function(error) {
              clearTimeout(timeout);
              if (originalOnError && self.websocket) {
                originalOnError.call(self.websocket, error);
              }
              reject(error);
            };
          });
          return;
        }
        
        // 如果 WebSocket 已关闭，需要重新连接
        if (!self.websocket || self.websocket.readyState === WebSocket.CLOSED) {
          console.log('[WebSocketTransport] WebSocket 已关闭，重新连接...');
          await self.connect({ apiKey: self.config.apiKey });
        }
      },
      send: (data: any) => {
        console.log('[WebSocketTransport] transport.send() 被调用:', {
          type: typeof data,
          isString: typeof data === 'string',
          isArrayBuffer: data instanceof ArrayBuffer,
          isBlob: data instanceof Blob,
          dataLength: data?.length || data?.byteLength || 'unknown',
        });
        if (self.websocket && self.websocket.readyState === WebSocket.OPEN) {
          if (typeof data === 'string') {
            self.websocket.send(data);
          } else if (data instanceof ArrayBuffer || data instanceof Blob) {
            // 二进制数据（音频数据）
            self.websocket.send(data);
          } else {
            // JSON 数据
            self.websocket.send(JSON.stringify(data));
          }
        } else {
          console.warn('[WebSocketTransport] WebSocket 未连接，无法发送数据');
        }
      },
      on: (event: string, callback: (...args: any[]) => void) => {
        self.on(event, callback);
      },
      off: (event: string, callback: (...args: any[]) => void) => {
        self.off(event, callback);
      },
      // 可能需要的其他方法
      close: () => {
        self.disconnect();
      },
      // 可能需要的状态属性（使用闭包访问实例状态）
      get status() {
        return self.status;
      },
    };
    
    // 使用 Proxy 来捕获所有属性访问，便于调试
    return new Proxy(transport, {
      get(target, prop) {
        if (prop in target) {
          const value = target[prop as keyof typeof target];
          // 如果是 getter，需要调用它
          if (typeof value === 'function' && prop !== 'connect' && prop !== 'send' && prop !== 'on' && prop !== 'off' && prop !== 'close') {
            return value;
          }
          return value;
        }
        console.warn(`[WebSocketTransport] 访问了不存在的属性: ${String(prop)}`);
        return undefined;
      },
    });
  }
}

