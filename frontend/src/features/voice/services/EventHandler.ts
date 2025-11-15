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

    const handleUserTranscript = (event: any) => {
      const transcript = event.transcript || event.text;
      if (transcript && this.callbacks.onUserTranscript) {
        this.callbacks.onUserTranscript(transcript);
      }
    };

    // 监听用户转录事件
    (this.session as any).on(
      'conversation.item.input_audio_transcription.completed',
      handleUserTranscript
    );

    this.cleanupFunctions.push(() => {
      (this.session as any).off(
        'conversation.item.input_audio_transcription.completed',
        handleUserTranscript
      );
    });
  }

  /**
   * 设置助手转录事件监听
   */
  setupAssistantTranscriptListener(): void {
    if (!this.session) {
      console.error('[EventHandler] Session 未设置，无法设置助手转录监听');
      return;
    }

    const handleAssistantTranscript = (event: any) => {
      const transcript = event.transcript || event.text || event.delta;
      if (transcript && this.callbacks.onAssistantTranscript) {
        this.callbacks.onAssistantTranscript(transcript);
      }
    };

    // 监听助手转录事件
    (this.session as any).on('response.text.done', handleAssistantTranscript);
    (this.session as any).on('response.audio_transcript.done', handleAssistantTranscript);

    this.cleanupFunctions.push(() => {
      (this.session as any).off('response.text.done', handleAssistantTranscript);
      (this.session as any).off('response.audio_transcript.done', handleAssistantTranscript);
    });
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

