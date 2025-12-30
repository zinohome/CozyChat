/**
 * 事件处理器
 * 
 * 负责：
 * - 监听工具调用事件
 * - 执行工具调用
 * - 返回工具执行结果给 RealtimeSession
 * - 处理用户/助手转录事件
 */

import type { RealtimeSession } from '@openai/agents/realtime';
import { toolManager } from './ToolManager';
import { logger } from '@/utils/logger';
import { toSimplifiedChinese } from '@/utils/textConverter';

const log = logger.withTag('EventHandler');

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
   * 监听多个事件以捕获工具调用：
   * 1. conversation.item.created - 工具调用项创建时
   * 2. history_added - 历史记录添加时（可能包含工具调用）
   * 3. history_updated - 历史记录更新时（可能包含工具调用）
   */
  setupToolCallListeners(): void {
    if (!this.session) {
      log.error('Session 未设置，无法设置工具调用监听');
      return;
    }

    // 用于去重，避免重复处理同一个工具调用
    const processedToolCallIds = new Set<string>();

    // 检查并处理工具调用的辅助函数
    const checkAndHandleToolCall = (item: any, eventName: string) => {
      if (!item) return;

      // 详细日志：记录所有 item 的完整内容（仅对 assistant 消息）
      if (item.role === 'assistant' || item.type === 'message') {
        log.debug(`🔍 [工具调用检查] ${eventName} - item 详情:`, {
          itemId: item.itemId || item.id,
          type: item.type,
          role: item.role,
          status: item.status,
          content: item.content,
          hasContent: !!item.content,
          contentLength: Array.isArray(item.content) ? item.content.length : 0,
          contentTypes: Array.isArray(item.content)
            ? item.content.map((c: any) => c.type)
            : [],
          fullItem: JSON.stringify(item, null, 2),
        });
      }

      // 检查是否为工具调用
      // 根据 OpenAI Realtime API 文档，工具调用可能有以下类型：
      // - item.type === 'function_call'
      // - item.type === 'tool_call'
      // - item.call?.type === 'function'
      // - item.type === 'message' && item.role === 'assistant' && item.content 包含 function_call
      const isToolCall =
        item.type === 'function_call' ||
        item.type === 'tool_call' ||
        item.call?.type === 'function' ||
        (item.type === 'message' &&
          item.role === 'assistant' &&
          Array.isArray(item.content) &&
          item.content.some((c: any) => c.type === 'function_call' || c.type === 'tool_call'));

      if (isToolCall) {
        const itemId = item.itemId || item.id || item.call_id;
        if (itemId && !processedToolCallIds.has(itemId)) {
          processedToolCallIds.add(itemId);
          log.debug(`🔧 ✅ 检测到工具调用 (${eventName}):`, item);
          this.handleToolCall(item);
        }
      }

      // 检查 content 数组中是否包含工具调用
      if (Array.isArray(item.content)) {
        for (const contentItem of item.content) {
          // 详细日志：记录所有 content 项
          if (contentItem.type === 'function_call' || contentItem.type === 'tool_call' || contentItem.function_call) {
            log.debug(`🔍 [工具调用检查] ${eventName} - content 项详情:`, {
              type: contentItem.type,
              fullContent: JSON.stringify(contentItem, null, 2),
            });
          }

          if (
            contentItem.type === 'function_call' ||
            contentItem.type === 'tool_call' ||
            contentItem.function_call
          ) {
            const callId = contentItem.id || contentItem.call_id || item.itemId || item.id;
            if (callId && !processedToolCallIds.has(callId)) {
              processedToolCallIds.add(callId);
              log.debug(`🔧 ✅ 检测到工具调用 (${eventName}, content):`, contentItem);
              this.handleToolCall(contentItem);
            }
          }
        }
      }
    };

    // 1. 监听 conversation.item.created 事件
    const handleItemCreated = (event: any) => {
      log.debug('conversation.item.created:', event);
      checkAndHandleToolCall(event.item, 'conversation.item.created');
    };

    // 2. 监听 history_added 事件
    const handleHistoryAdded = (item: any) => {
      log.debug('🔧 history_added 事件（工具调用检查）:', item);
      checkAndHandleToolCall(item, 'history_added');
    };

    // 3. 监听 history_updated 事件
    const handleHistoryUpdated = (items: any) => {
      if (Array.isArray(items)) {
        for (const item of items) {
          checkAndHandleToolCall(item, 'history_updated');
        }
      } else if (items) {
        checkAndHandleToolCall(items, 'history_updated');
      }
    };

    // 添加事件监听
    (this.session as any).on('conversation.item.created', handleItemCreated);
    (this.session as any).on('history_added', handleHistoryAdded);
    (this.session as any).on('history_updated', handleHistoryUpdated);

    // 保存清理函数
    this.cleanupFunctions.push(() => {
      (this.session as any).off('conversation.item.created', handleItemCreated);
      (this.session as any).off('history_added', handleHistoryAdded);
      (this.session as any).off('history_updated', handleHistoryUpdated);
    });

    log.debug('工具调用事件监听已设置（监听 conversation.item.created, history_added, history_updated）');
  }

  /**
   * 处理工具调用
   * 
   * @param item - 工具调用项
   */
  private async handleToolCall(item: any): Promise<void> {
    try {
      log.debug('🔧 处理工具调用，item:', JSON.stringify(item, null, 2));

      // 提取工具名称和参数
      // 支持多种格式：
      // 1. item.name / item.function?.name / item.call?.function?.name
      // 2. item.function_call?.name
      // 3. item.content[].function_call?.name (如果 item 是 message，工具调用在 content 中)
      const toolName =
        item.name ||
        item.function?.name ||
        item.call?.function?.name ||
        item.function_call?.name ||
        item.tool_name;

      let parameters =
        item.arguments ||
        item.function?.arguments ||
        item.call?.function?.arguments ||
        item.function_call?.arguments ||
        item.parameters ||
        {};

      // 如果参数是字符串，尝试解析为 JSON
      if (typeof parameters === 'string') {
        try {
          parameters = JSON.parse(parameters);
        } catch (e) {
          log.error('参数解析失败:', e);
        }
      }

      if (!toolName) {
        log.error('❌ 无法提取工具名称，item:', JSON.stringify(item, null, 2));
        return;
      }

      log.debug(`🔧 处理工具调用: ${toolName}`, parameters);

      // 触发回调
      if (this.callbacks.onToolCall) {
        this.callbacks.onToolCall(toolName, parameters);
      }

      // 执行工具
      const result = await toolManager.executeTool(toolName, parameters);

      log.debug(`工具执行结果: ${toolName}`, result);

      // 触发回调
      if (this.callbacks.onToolResult) {
        this.callbacks.onToolResult(toolName, result);
      }

      // 返回结果给 RealtimeSession
      await this.submitToolResult(item.id || item.call_id, toolName, result);
    } catch (error) {
      log.error('工具调用处理失败:', error);
      
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
   * 注意：如果工具是通过 tool() 函数创建的，并且有 execute 函数，
   * 那么工具执行结果会自动返回，不需要手动提交。
   * 此方法仅作为备用方案，用于手动提交工具结果。
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
      log.error('Session 未设置，无法提交工具结果');
      return;
    }

    try {
      // 根据 OpenAI Agents SDK，如果工具是通过 tool() 创建的，
      // 工具执行结果会自动返回，不需要手动提交。
      // 这里仅作为备用方案，尝试手动提交。

      // 方法1: 尝试使用 createItem 创建 function_call_output
      if (typeof (this.session as any).createItem === 'function') {
        try {
          await (this.session as any).createItem({
            type: 'function_call_output',
            call_id: callId,
            output: typeof result === 'string' ? result : JSON.stringify(result),
          });
          log.debug(`工具结果已提交 (createItem): ${toolName}`);
          return;
        } catch (e) {
          log.debug('createItem 方法失败，尝试其他方法:', e);
        }
      }

      // 方法2: 尝试使用 submitToolOutput
      if (typeof (this.session as any).submitToolOutput === 'function') {
        await (this.session as any).submitToolOutput(callId, result);
        log.debug(`工具结果已提交 (submitToolOutput): ${toolName}`);
        return;
      }

      // 方法3: 尝试使用 submitToolResult
      if (typeof (this.session as any).submitToolResult === 'function') {
        await (this.session as any).submitToolResult(callId, result);
        log.debug(`工具结果已提交 (submitToolResult): ${toolName}`);
        return;
      }

      // 方法4: 尝试使用 send
      if (typeof (this.session as any).send === 'function') {
        await (this.session as any).send({
          type: 'conversation.item.create',
          item: {
            type: 'function_call_output',
            call_id: callId,
            output: typeof result === 'string' ? result : JSON.stringify(result),
          },
        });
        log.debug(`工具结果已提交 (send): ${toolName}`);
        return;
      }

      // 如果所有方法都失败，记录警告（但不报错，因为工具可能已经自动提交）
      log.warn('无法找到提交工具结果的方法，工具可能已自动提交（如果使用 tool() 创建）');
    } catch (error) {
      log.error('提交工具结果失败:', error);
    }
  }

  /**
   * 设置用户转录事件监听
   */
  setupUserTranscriptListener(): void {
    if (!this.session) {
      log.error('Session 未设置，无法设置用户转录监听');
      return;
    }
    
    log.debug('🔍 设置用户转录监听，session:', this.session);

    // 用于去重（所有监听器共享，避免重复处理）
    const processedMessageIds = new Set<string>();
    const processedTexts = new Set<string>();
    
    // 辅助函数：检查并处理用户转录（统一去重逻辑）
    const processUserTranscript = (messageId: string, transcript: string, source: string): boolean => {
      if (!transcript || !transcript.trim()) {
        return false;
      }
      
      const key = `${messageId}:${transcript}`;
      if (processedTexts.has(key)) {
        log.debug(`⚠️ 转录已处理过，跳过 (${source}):`, key);
        return false;
      }
      
      processedMessageIds.add(messageId);
      processedTexts.add(key);
      log.debug(`✅ 从 ${source} 提取用户转录:`, transcript);
      
      if (this.callbacks.onUserTranscript) {
        // 将繁体中文转换为简体中文
        const simplifiedTranscript = toSimplifiedChinese(transcript);
        if (simplifiedTranscript !== transcript) {
          log.debug(`✅ 繁体转简体: "${transcript}" -> "${simplifiedTranscript}"`);
        }
        log.debug('✅ 调用用户转录回调，文本:', simplifiedTranscript);
        this.callbacks.onUserTranscript(simplifiedTranscript);
        return true;
      } else {
        log.debug('❌ 用户转录回调不存在！');
        return false;
      }
    };

    // 提取用户转录文本的辅助函数
    const extractUserTranscript = (item: any): string | null => {
      log.debug('🔍 尝试提取用户转录，item:', JSON.stringify(item, null, 2));
      
      // 1. 首先检查 item 的直接字段
      if (item.transcript && typeof item.transcript === 'string' && item.transcript.trim()) {
        log.debug('✅ 从 item.transcript 提取:', item.transcript.trim());
        return item.transcript.trim();
      }
      if (item.input_audio_transcript && typeof item.input_audio_transcript === 'string' && item.input_audio_transcript.trim()) {
        log.debug('✅ 从 item.input_audio_transcript 提取:', item.input_audio_transcript.trim());
        return item.input_audio_transcript.trim();
      }

      // 2. 检查 content 数组（转录文本通常在这里）
      if (Array.isArray(item.content)) {
        log.debug('🔍 content 是数组，长度:', item.content.length);
        for (const c of item.content) {
          log.debug('🔍 检查 content 项:', c.type, c);
          // 优先检查 input_audio 类型（这是用户语音输入）
          if (c.type === 'input_audio') {
            if (c.transcript && typeof c.transcript === 'string' && c.transcript.trim()) {
              log.debug('✅ 从 content[].input_audio.transcript 提取:', c.transcript.trim());
              return c.transcript.trim();
            }
            if (c.input_audio_transcript && typeof c.input_audio_transcript === 'string' && c.input_audio_transcript.trim()) {
              log.debug('✅ 从 content[].input_audio.input_audio_transcript 提取:', c.input_audio_transcript.trim());
              return c.input_audio_transcript.trim();
            }
            if (c.text && typeof c.text === 'string' && c.text.trim()) {
              log.debug('✅ 从 content[].input_audio.text 提取:', c.text.trim());
              return c.text.trim();
            }
          }
          // 检查任何包含 transcript 的项（备用）
          if (c.transcript && typeof c.transcript === 'string' && c.transcript.trim()) {
            log.debug('✅ 从 content[].transcript 提取:', c.transcript.trim());
            return c.transcript.trim();
          }
          // 检查 text 类型（某些情况下转录可能以 text 形式存在）
          if (c.type === 'text' && c.text && typeof c.text === 'string' && c.text.trim()) {
            log.debug('✅ 从 content[].text 提取:', c.text.trim());
            return c.text.trim();
          }
        }
      } else if (item.content) {
        log.debug('🔍 content 不是数组:', typeof item.content, item.content);
      }

      // 3. 如果 content 是字符串，直接返回（备用）
      if (typeof item.content === 'string' && item.content.trim()) {
        log.debug('✅ 从 item.content (字符串) 提取:', item.content.trim());
        return item.content.trim();
      }

      log.debug('❌ 未能提取到转录文本');
      return null;
    };

    // 1. conversation.item.input_audio_transcription.completed 事件
    const handleUserTranscript = (event: any) => {
      log.debug('🔍 用户转录事件触发 (completed):', event);
      const transcript = event?.transcript;
      const itemId = event?.item_id || event?.itemId || event?.id;
      
      if (transcript && typeof transcript === 'string' && transcript.trim()) {
        // 使用统一的处理函数（如果 itemId 存在）
        if (itemId) {
          processUserTranscript(itemId, transcript.trim(), 'input_audio_transcription.completed');
        } else {
          // 如果没有 itemId，直接调用回调（但可能重复）
          if (this.callbacks.onUserTranscript) {
            // 将繁体中文转换为简体中文
            const originalTranscript = transcript.trim();
            const simplifiedTranscript = toSimplifiedChinese(originalTranscript);
            if (simplifiedTranscript !== originalTranscript) {
              log.debug(`✅ 繁体转简体 (无ID): "${originalTranscript}" -> "${simplifiedTranscript}"`);
            }
            log.debug('✅ 触发用户转录回调 (无ID):', simplifiedTranscript);
            this.callbacks.onUserTranscript(simplifiedTranscript);
          }
        }
      } else {
        log.debug('❌ 用户转录回调未触发:', {
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
      log.debug('🔍 history_added 事件触发:', item);
      
      if (!item || item.type !== 'message') {
        return;
      }

      const messageId = item.itemId || item.id;
      if (!messageId) {
        return;
      }

      // 去重检查（提前检查，避免不必要的提取）
      if (processedMessageIds.has(messageId)) {
        log.debug('⚠️ 消息已处理过，跳过 (history_added):', messageId);
        return;
      }

      if (item.role === 'user') {
        const transcript = extractUserTranscript(item);
        if (transcript) {
          processUserTranscript(messageId, transcript, 'history_added');
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
      log.debug('🔍 history_updated 事件触发，项数:', items?.length);
      if (items?.length > 0) {
        log.debug('🔍 history_updated items:', JSON.stringify(items, null, 2));
      }
      
      if (!Array.isArray(items)) {
        log.warn('❌ history_updated 参数不是数组:', typeof items, items);
        return;
      }

      if (items.length === 0) {
        log.debug('⚠️ history_updated 数组为空，跳过处理');
        return;
      }

      for (const item of items) {
        if (!item || item.type !== 'message') {
          log.debug('⚠️ 跳过非消息项:', item?.type, item);
          continue;
        }

        const messageId = item.itemId || item.id;
        if (!messageId) {
          log.debug('⚠️ 消息无 ID，跳过');
          continue;
        }

        // 处理用户消息
        if (item.role === 'user') {
          log.debug('🔍 处理用户消息:', messageId);
          
          // 去重检查（提前检查，避免不必要的提取）
          if (processedMessageIds.has(messageId)) {
            log.debug('⚠️ 消息已处理过，跳过 (history_updated):', messageId);
            continue;
          }
          
          const transcript = extractUserTranscript(item);
          if (transcript) {
            processUserTranscript(messageId, transcript, 'history_updated');
          } else {
            log.debug('❌ 未能提取用户转录，item:', JSON.stringify(item, null, 2));
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

    log.debug('用户转录事件监听已设置 (3个事件)');
  }

  /**
   * 设置助手转录事件监听
   */
  setupAssistantTranscriptListener(): void {
    if (!this.session) {
      log.error('Session 未设置，无法设置助手转录监听');
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
            log.debug('✅ 从 history_updated 提取助手文本:', text);
            if (this.callbacks.onAssistantTranscript) {
              this.callbacks.onAssistantTranscript(text);
            }
          }
        }
      }
    };

    // 注意：复用用户的 history_updated 监听器，修改 setupUserTranscriptListener
    // 暂时先不在这里添加监听，避免重复监听

    log.debug('助手转录事件监听已设置 (2个事件)');
  }

  /**
   * 清理事件监听
   */
  cleanup(): void {
    log.debug('清理事件监听');
    this.cleanupFunctions.forEach((cleanup) => cleanup());
    this.cleanupFunctions = [];
    this.session = null;
  }
}

