/**
 * 事件处理器
 * 
 * 负责：
 * - 监听工具调用事件
 * - 执行工具调用
 * - 返回工具执行结果给 RealtimeSession
 * - 处理用户/助手转录事件
 */

import type { RealtimeSession } from '@openai/agents';
import { toolManager } from './ToolManager';

/**
 * 事件处理器回调接口
 */
export interface EventHandlerCallbacks {
  /** 用户转录回调 */
  onUserTranscript?: (text: string) => void;
  /** 助手转录回调 */
  onAssistantTranscript?: (text: string) => void;
  /** 工具调用回调 */
  onToolCall?: (toolName: string, parameters: Record<string, any>) => void;
  /** 工具结果回调 */
  onToolResult?: (toolName: string, result: any) => void;
}

/**
 * 事件处理器类
 */
export class EventHandler {
  private session: RealtimeSession | null = null;
  private callbacks: EventHandlerCallbacks = {};
  private cleanupFunctions: Array<() => void> = [];

  /**
   * 设置 RealtimeSession
   * 
   * @param session - RealtimeSession 实例
   */
  setSession(session: RealtimeSession): void {
    this.session = session;
  }

  /**
   * 设置回调函数
   * 
   * @param callbacks - 回调函数集合
   */
  setCallbacks(callbacks: EventHandlerCallbacks): void {
    this.callbacks = callbacks;
  }

  /**
   * 设置工具调用事件监听
   * 
   * 监听 conversation.item.created 事件，检查是否为工具调用
   */
  setupToolCallListeners(): void {
    if (!this.session) {
      console.error('[EventHandler] Session 未设置，无法设置工具调用监听');
      return;
    }

    // 监听 conversation.item.created 事件
    const handleItemCreated = (event: any) => {
      console.log('[EventHandler] conversation.item.created:', event);

      const item = event.item;
      if (!item) return;

      // 检查是否为工具调用
      // 根据 OpenAI Realtime API 文档，工具调用可能有以下类型：
      // - item.type === 'function_call'
      // - item.type === 'tool_call'
      // - item.call?.type === 'function'
      if (
        item.type === 'function_call' ||
        item.type === 'tool_call' ||
        item.call?.type === 'function'
      ) {
        this.handleToolCall(item);
      }
    };

    // 添加事件监听
    (this.session as any).on('conversation.item.created', handleItemCreated);

    // 保存清理函数
    this.cleanupFunctions.push(() => {
      (this.session as any).off('conversation.item.created', handleItemCreated);
    });

    console.log('[EventHandler] 工具调用事件监听已设置');
  }

  /**
   * 处理工具调用
   * 
   * @param item - 工具调用项
   */
  private async handleToolCall(item: any): Promise<void> {
    try {
      // 提取工具名称和参数
      const toolName =
        item.name ||
        item.function?.name ||
        item.call?.function?.name ||
        item.tool_name;

      let parameters =
        item.arguments ||
        item.function?.arguments ||
        item.call?.function?.arguments ||
        item.parameters ||
        {};

      // 如果参数是字符串，尝试解析为 JSON
      if (typeof parameters === 'string') {
        try {
          parameters = JSON.parse(parameters);
        } catch (e) {
          console.error('[EventHandler] 参数解析失败:', e);
        }
      }

      if (!toolName) {
        console.error('[EventHandler] 无法提取工具名称:', item);
        return;
      }

      console.log(`[EventHandler] 处理工具调用: ${toolName}`, parameters);

      // 触发回调
      if (this.callbacks.onToolCall) {
        this.callbacks.onToolCall(toolName, parameters);
      }

      // 执行工具
      const result = await toolManager.executeTool(toolName, parameters);

      console.log(`[EventHandler] 工具执行结果: ${toolName}`, result);

      // 触发回调
      if (this.callbacks.onToolResult) {
        this.callbacks.onToolResult(toolName, result);
      }

      // 返回结果给 RealtimeSession
      await this.submitToolResult(item.id || item.call_id, toolName, result);
    } catch (error) {
      console.error('[EventHandler] 工具调用处理失败:', error);
      
      // 即使失败，也应该返回错误信息给 RealtimeSession
      const errorResult = {
        error: error instanceof Error ? error.message : 'Unknown error',
      };
      
      await this.submitToolResult(
        item.id || item.call_id,
        item.name || 'unknown',
        errorResult
      );
    }
  }

  /**
   * 提交工具执行结果给 RealtimeSession
   * 
   * @param callId - 工具调用ID
   * @param toolName - 工具名称
   * @param result - 执行结果
   */
  private async submitToolResult(
    callId: string,
    toolName: string,
    result: any
  ): Promise<void> {
    if (!this.session) {
      console.error('[EventHandler] Session 未设置，无法提交工具结果');
      return;
    }

    try {
      // 根据 OpenAI Agents SDK 文档，提交工具结果的方法可能是：
      // 1. session.submitToolResult(callId, result)
      // 2. session.send({ type: 'conversation.item.create', item: { ... } })
      // 3. session.addMessage({ role: 'tool', tool_call_id: callId, content: result })

      // 尝试方法1
      if (typeof (this.session as any).submitToolResult === 'function') {
        await (this.session as any).submitToolResult(callId, result);
        console.log(`[EventHandler] 工具结果已提交 (submitToolResult): ${toolName}`);
        return;
      }

      // 尝试方法2
      if (typeof (this.session as any).send === 'function') {
        await (this.session as any).send({
          type: 'conversation.item.create',
          item: {
            type: 'function_call_output',
            call_id: callId,
            output: JSON.stringify(result),
          },
        });
        console.log(`[EventHandler] 工具结果已提交 (send): ${toolName}`);
        return;
      }

      // 尝试方法3
      if (typeof (this.session as any).addMessage === 'function') {
        await (this.session as any).addMessage({
          role: 'tool',
          tool_call_id: callId,
          content: JSON.stringify(result),
        });
        console.log(`[EventHandler] 工具结果已提交 (addMessage): ${toolName}`);
        return;
      }

      console.error('[EventHandler] 无法找到提交工具结果的方法');
    } catch (error) {
      console.error('[EventHandler] 提交工具结果失败:', error);
    }
  }

  /**
   * 设置用户转录事件监听
   */
  setupUserTranscriptListener(): void {
    if (!this.session) {
      console.error('[EventHandler] Session 未设置，无法设置用户转录监听');
      return;
    }
    
    console.log('[EventHandler] 🔍 设置用户转录监听，session:', this.session);

    // 用于去重
    const processedMessageIds = new Set<string>();
    const processedTexts = new Set<string>();

    // 提取用户转录文本的辅助函数
    const extractUserTranscript = (item: any): string | null => {
      console.log('[EventHandler] 🔍 尝试提取用户转录，item:', JSON.stringify(item, null, 2));
      
      // 1. 首先检查 item 的直接字段
      if (item.transcript && typeof item.transcript === 'string' && item.transcript.trim()) {
        console.log('[EventHandler] ✅ 从 item.transcript 提取:', item.transcript.trim());
        return item.transcript.trim();
      }
      if (item.input_audio_transcript && typeof item.input_audio_transcript === 'string' && item.input_audio_transcript.trim()) {
        console.log('[EventHandler] ✅ 从 item.input_audio_transcript 提取:', item.input_audio_transcript.trim());
        return item.input_audio_transcript.trim();
      }

      // 2. 检查 content 数组（转录文本通常在这里）
      if (Array.isArray(item.content)) {
        console.log('[EventHandler] 🔍 content 是数组，长度:', item.content.length);
        for (const c of item.content) {
          console.log('[EventHandler] 🔍 检查 content 项:', c.type, c);
          // 优先检查 input_audio 类型（这是用户语音输入）
          if (c.type === 'input_audio') {
            if (c.transcript && typeof c.transcript === 'string' && c.transcript.trim()) {
              console.log('[EventHandler] ✅ 从 content[].input_audio.transcript 提取:', c.transcript.trim());
              return c.transcript.trim();
            }
            if (c.input_audio_transcript && typeof c.input_audio_transcript === 'string' && c.input_audio_transcript.trim()) {
              console.log('[EventHandler] ✅ 从 content[].input_audio.input_audio_transcript 提取:', c.input_audio_transcript.trim());
              return c.input_audio_transcript.trim();
            }
            if (c.text && typeof c.text === 'string' && c.text.trim()) {
              console.log('[EventHandler] ✅ 从 content[].input_audio.text 提取:', c.text.trim());
              return c.text.trim();
            }
          }
          // 检查任何包含 transcript 的项（备用）
          if (c.transcript && typeof c.transcript === 'string' && c.transcript.trim()) {
            console.log('[EventHandler] ✅ 从 content[].transcript 提取:', c.transcript.trim());
            return c.transcript.trim();
          }
          // 检查 text 类型（某些情况下转录可能以 text 形式存在）
          if (c.type === 'text' && c.text && typeof c.text === 'string' && c.text.trim()) {
            console.log('[EventHandler] ✅ 从 content[].text 提取:', c.text.trim());
            return c.text.trim();
          }
        }
      } else if (item.content) {
        console.log('[EventHandler] 🔍 content 不是数组:', typeof item.content, item.content);
      }

      // 3. 如果 content 是字符串，直接返回（备用）
      if (typeof item.content === 'string' && item.content.trim()) {
        console.log('[EventHandler] ✅ 从 item.content (字符串) 提取:', item.content.trim());
        return item.content.trim();
      }

      console.log('[EventHandler] ❌ 未能提取到转录文本');
      return null;
    };

    // 1. conversation.item.input_audio_transcription.completed 事件
    const handleUserTranscript = (event: any) => {
      console.log('[EventHandler] 🔍 用户转录事件触发 (completed):', event);
      const transcript = event?.transcript;
      if (transcript && typeof transcript === 'string' && transcript.trim() && this.callbacks.onUserTranscript) {
        console.log('[EventHandler] ✅ 触发用户转录回调:', transcript);
        this.callbacks.onUserTranscript(transcript.trim());
      } else {
        console.log('[EventHandler] ❌ 用户转录回调未触发:', {
          hasTranscript: !!transcript,
          hasCallback: !!this.callbacks.onUserTranscript,
        });
      }
    };

    (this.session as any).on('conversation.item.input_audio_transcription.completed', handleUserTranscript);
    this.cleanupFunctions.push(() => {
      (this.session as any).off('conversation.item.input_audio_transcription.completed', handleUserTranscript);
    });

    // 2. history_added 事件（从历史记录中提取转录）
    // 注意：参数本身就是 item 对象，不是 event.item！
    const handleHistoryAdded = (item: any) => {
      console.log('[EventHandler] 🔍 history_added 事件触发:', item);
      
      if (!item || item.type !== 'message') {
        // console.log('[EventHandler] 跳过非消息项');
        return;
      }

      const messageId = item.itemId || item.id;
      if (!messageId) {
        // console.log('[EventHandler] 消息无 ID');
        return;
      }

      // 去重检查
      if (processedMessageIds.has(messageId)) {
        // console.log('[EventHandler] 消息已处理:', messageId);
        return;
      }

      if (item.role === 'user') {
        // console.log('[EventHandler] 处理用户消息');
        const transcript = extractUserTranscript(item);
        if (transcript) {
          const key = `${messageId}:${transcript}`;
          if (!processedTexts.has(key)) {
            processedMessageIds.add(messageId);
            processedTexts.add(key);
            console.log('[EventHandler] ✅ 从 history_added 提取用户转录:', transcript);
            if (this.callbacks.onUserTranscript) {
              console.log('[EventHandler] ✅ 调用用户转录回调');
              this.callbacks.onUserTranscript(transcript);
            } else {
              console.log('[EventHandler] ❌ 用户转录回调不存在！');
            }
          }
        }
      }
    };

    (this.session as any).on('history_added', handleHistoryAdded);
    this.cleanupFunctions.push(() => {
      (this.session as any).off('history_added', handleHistoryAdded);
    });

    // 提取助手文本的辅助函数
    const extractAssistantText = (item: any): string | null => {
      // 检查 content 数组
      if (Array.isArray(item.content)) {
        for (const c of item.content) {
          // 文本内容
          if (c.type === 'text' && c.text && typeof c.text === 'string') {
            return c.text.trim();
          }
          // 音频转录
          if (c.type === 'output_audio' && c.transcript && typeof c.transcript === 'string') {
            return c.transcript.trim();
          }
          // 音频转录（备用字段）
          if (c.type === 'audio' && c.transcript && typeof c.transcript === 'string') {
            return c.transcript.trim();
          }
        }
      }

      // 检查直接字段
      if (item.text && typeof item.text === 'string') {
        return item.text.trim();
      }
      if (item.transcript && typeof item.transcript === 'string') {
        return item.transcript.trim();
      }

      return null;
    };

    const processedAssistantIds = new Set<string>();
    const processedAssistantTexts = new Set<string>();

    // 3. history_updated 事件（从更新的历史中提取转录）
    // 注意：参数是历史数组，不是单个 item！同时处理用户和助手消息
    const handleHistoryUpdated = (items: any[]) => {
      console.log('[EventHandler] 🔍 history_updated 事件触发，项数:', items?.length);
      if (items?.length > 0) {
        console.log('[EventHandler] 🔍 history_updated items:', JSON.stringify(items, null, 2));
      }
      
      if (!Array.isArray(items)) {
        console.log('[EventHandler] ❌ history_updated 参数不是数组:', typeof items, items);
        return;
      }

      if (items.length === 0) {
        console.log('[EventHandler] ⚠️ history_updated 数组为空，跳过处理');
        return;
      }

      for (const item of items) {
        if (!item || item.type !== 'message') {
          console.log('[EventHandler] ⚠️ 跳过非消息项:', item?.type, item);
          continue;
        }

        const messageId = item.itemId || item.id;
        if (!messageId) {
          console.log('[EventHandler] ⚠️ 消息无 ID，跳过');
          continue;
        }

        // 处理用户消息
        if (item.role === 'user') {
          console.log('[EventHandler] 🔍 处理用户消息:', messageId);
          const transcript = extractUserTranscript(item);
          if (transcript) {
            const key = `${messageId}:${transcript}`;
            if (!processedTexts.has(key)) {
              processedMessageIds.add(messageId);
              processedTexts.add(key);
              console.log('[EventHandler] ✅ 从 history_updated 提取用户转录:', transcript);
              if (this.callbacks.onUserTranscript) {
                console.log('[EventHandler] ✅ 调用用户转录回调');
                this.callbacks.onUserTranscript(transcript);
              } else {
                console.log('[EventHandler] ❌ 用户转录回调不存在！');
              }
            } else {
              console.log('[EventHandler] ⚠️ 转录已处理过，跳过:', key);
            }
          } else {
            console.log('[EventHandler] ❌ 未能提取用户转录，item:', JSON.stringify(item, null, 2));
          }
        }
        // 处理助手消息
        else if (item.role === 'assistant') {
          const text = extractAssistantText(item);
          if (text) {
            const key = `${messageId}:${text}`;
            if (!processedAssistantTexts.has(key)) {
              processedAssistantIds.add(messageId);
              processedAssistantTexts.add(key);
              // console.log('[EventHandler] ✅ 从 history_updated 提取助手文本:', text);
              if (this.callbacks.onAssistantTranscript) {
                this.callbacks.onAssistantTranscript(text);
              }
            }
          }
        }
      }
    };

    (this.session as any).on('history_updated', handleHistoryUpdated);
    this.cleanupFunctions.push(() => {
      (this.session as any).off('history_updated', handleHistoryUpdated);
    });

    console.log('[EventHandler] 用户转录事件监听已设置 (3个事件)');
  }

  /**
   * 设置助手转录事件监听
   */
  setupAssistantTranscriptListener(): void {
    if (!this.session) {
      console.error('[EventHandler] Session 未设置，无法设置助手转录监听');
      return;
    }

    // 用于去重
    const processedAssistantIds = new Set<string>();
    const processedAssistantTexts = new Set<string>();

    // 提取助手文本的辅助函数
    const extractAssistantText = (item: any): string | null => {
      // console.log('[EventHandler] 尝试提取助手文本，item:', JSON.stringify(item, null, 2));
      
      // 检查 content 数组
      if (Array.isArray(item.content)) {
        for (const c of item.content) {
          // 文本内容
          if (c.type === 'text' && c.text && typeof c.text === 'string') {
            return c.text.trim();
          }
          // 音频转录
          if (c.type === 'output_audio' && c.transcript && typeof c.transcript === 'string') {
            return c.transcript.trim();
          }
          // 音频转录（备用字段）
          if (c.type === 'audio' && c.transcript && typeof c.transcript === 'string') {
            return c.transcript.trim();
          }
        }
      }

      // 检查直接字段
      if (item.text && typeof item.text === 'string') {
        return item.text.trim();
      }
      if (item.transcript && typeof item.transcript === 'string') {
        return item.transcript.trim();
      }

      // console.log('[EventHandler] 未能提取到助手文本');
      return null;
    };

    // 1. response.text.done 和 response.audio_transcript.done 事件
    const handleAssistantTranscript = (event: any) => {
      // console.log('[EventHandler] 助手转录事件 (response):', event);
      const transcript = event.transcript || event.text || event.delta;
      if (transcript && this.callbacks.onAssistantTranscript) {
        // console.log('[EventHandler] ✅ 从 response 事件提取助手文本:', transcript);
        this.callbacks.onAssistantTranscript(transcript);
      }
    };

    (this.session as any).on('response.text.done', handleAssistantTranscript);
    (this.session as any).on('response.audio_transcript.done', handleAssistantTranscript);
    this.cleanupFunctions.push(() => {
      (this.session as any).off('response.text.done', handleAssistantTranscript);
      (this.session as any).off('response.audio_transcript.done', handleAssistantTranscript);
    });

    // 2. history_added 事件（提取助手回复）
    const handleAssistantHistoryAdded = (item: any) => {
      if (!item || item.type !== 'message' || item.role !== 'assistant') return;

      const messageId = item.itemId || item.id;
      if (!messageId) return;

      // 去重检查
      if (processedAssistantIds.has(messageId)) return;

      const text = extractAssistantText(item);
      if (text) {
        const key = `${messageId}:${text}`;
        if (!processedAssistantTexts.has(key)) {
          processedAssistantIds.add(messageId);
          processedAssistantTexts.add(key);
          // console.log('[EventHandler] ✅ 从 history_added 提取助手文本:', text);
          if (this.callbacks.onAssistantTranscript) {
            this.callbacks.onAssistantTranscript(text);
          }
        }
      }
    };

    // 注意：复用用户的 history_added 监听器会导致冲突，这里不单独监听，而是在 setupUserTranscriptListener 中处理

    // 3. history_updated 事件（提取助手回复）
    const handleAssistantHistoryUpdated = (items: any[]) => {
      if (!Array.isArray(items)) return;

      for (const item of items) {
        if (!item || item.type !== 'message' || item.role !== 'assistant') continue;

        const messageId = item.itemId || item.id;
        if (!messageId) continue;

        const text = extractAssistantText(item);
        if (text) {
          const key = `${messageId}:${text}`;
          if (!processedAssistantTexts.has(key)) {
            processedAssistantIds.add(messageId);
            processedAssistantTexts.add(key);
            console.log('[EventHandler] ✅ 从 history_updated 提取助手文本:', text);
            if (this.callbacks.onAssistantTranscript) {
              this.callbacks.onAssistantTranscript(text);
            }
          }
        }
      }
    };

    // 注意：复用用户的 history_updated 监听器，修改 setupUserTranscriptListener
    // 暂时先不在这里添加监听，避免重复监听

    console.log('[EventHandler] 助手转录事件监听已设置 (2个事件)');
  }

  /**
   * 清理事件监听
   */
  cleanup(): void {
    console.log('[EventHandler] 清理事件监听');
    this.cleanupFunctions.forEach((cleanup) => cleanup());
    this.cleanupFunctions = [];
    this.session = null;
  }
}

