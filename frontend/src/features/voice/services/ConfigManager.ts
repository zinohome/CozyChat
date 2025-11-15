/**
 * 配置管理器
 * 
 * 负责：
 * - 加载全局配置
 * - 加载 Personality 配置
 * - 合并配置（personality > global > default）
 * - 配置缓存
 */

import { configApi } from '@/services/config';
import { personalityApi } from '@/services/personality';
import type { OpenAIConfig } from '@/services/config';

/**
 * Voice Agent 配置
 */
export interface VoiceAgentConfig {
  /** 语音 */
  voice: string;
  /** 指令（system prompt） */
  instructions: string;
  /** 模型名称 */
  model: string;
  /** API密钥（ephemeral token） */
  apiKey: string;
  /** 基础 URL */
  baseUrl: string;
  /** WebSocket URL（用于 WebSocket 传输层） */
  wsUrl?: string;
  /** 工具列表 */
  tools: any[];
  /** OpenAI 配置（完整） */
  openai: OpenAIConfig;
  /** 音频转录配置 */
  inputAudioTranscription?: {
    model: string;
  };
  /** 传输层类型 */
  transportType?: 'webrtc' | 'websocket';
  /** WebSocket配置（包括音频缓冲区等） */
  websocket?: {
    audio_buffer?: {
      min_size?: number;
      max_size?: number;
    };
  };
}

/**
 * 配置管理器类
 */
export class ConfigManager {
  private cachedConfig: VoiceAgentConfig | null = null;
  private personalityId: string | undefined;

  constructor(personalityId?: string) {
    this.personalityId = personalityId;
  }

  /**
   * 加载并合并配置
   * 
   * @returns 合并后的配置
   */
  async loadConfig(): Promise<VoiceAgentConfig> {
    // 如果有缓存，直接返回
    if (this.cachedConfig) {
      console.log('[ConfigManager] 使用缓存的配置');
      return this.cachedConfig;
    }

    try {
      console.log('[ConfigManager] 开始加载配置...');

      // 1. 获取 OpenAI 配置
      const openaiConfig = await configApi.getOpenAIConfig();
      console.log('[ConfigManager] OpenAI 配置已加载');

      // 2. 获取 ephemeral client key (临时密钥)
      const realtimeToken = await configApi.getRealtimeToken();
      console.log('[ConfigManager] Ephemeral key 已获取');

      // 3. 获取全局默认配置（来自 realtime.yaml）
      const globalConfig = await configApi.getRealtimeConfig();
      console.log('[ConfigManager] 全局配置已加载');

      // 4. 获取 personality 配置（如果有）
      let personalityConfig: any = {};
      if (this.personalityId) {
        try {
          const personality = await personalityApi.getPersonality(this.personalityId);
          // Personality 类型没有 config 属性，直接使用 personality 对象本身
          personalityConfig = personality || {};
          console.log('[ConfigManager] Personality 配置已加载');
        } catch (error) {
          console.warn('[ConfigManager] 加载 personality 配置失败:', error);
        }
      }

      // 5. 合并配置：personality 配置 > 全局配置 > 代码默认值
      const voiceConfig = personalityConfig?.voice || {};
      const personalityRealtimeConfig = voiceConfig?.realtime || {};

      const voice = personalityRealtimeConfig.voice || globalConfig.voice || 'shimmer';
      const instructions =
        personalityRealtimeConfig.instructions ||
        personalityConfig?.ai?.system_prompt ||
        'You are a helpful assistant.';

      // 音频转录配置（从全局配置或personality配置读取）
      const inputAudioTranscription = 
        personalityRealtimeConfig.input_audio_transcription || 
        globalConfig.input_audio_transcription || 
        { model: 'whisper-1' }; // 默认启用 whisper-1

      // 传输层类型（从全局配置或personality配置读取）
      const transportType = 
        personalityRealtimeConfig.transport?.type || 
        globalConfig.transport?.type || 
        'webrtc'; // 默认使用 WebRTC

      // WebSocket配置（从全局配置或personality配置读取）
      const websocketConfig = 
        personalityRealtimeConfig.websocket || 
        globalConfig.websocket || 
        undefined;

      console.log('[ConfigManager] 配置合并完成:', {
        global: globalConfig.voice,
        personality: personalityRealtimeConfig.voice,
        final: voice,
        inputAudioTranscription,
        transportType,
        websocket: websocketConfig,
      });

      // 6. 构建完整配置
      const config: VoiceAgentConfig = {
        voice,
        instructions,
        model: realtimeToken.model,
        apiKey: realtimeToken.token,
        baseUrl: openaiConfig.base_url,
        wsUrl: realtimeToken.url, // WebSocket URL（用于 WebSocket 传输层）
        tools: [], // 工具列表将由 VoiceAgentService 加载
        openai: openaiConfig,
        inputAudioTranscription,
        transportType,
        websocket: websocketConfig,
      };

      // 缓存配置
      this.cachedConfig = config;

      console.log('[ConfigManager] 配置加载完成:', {
        voice,
        model: config.model,
        inputAudioTranscription,
      });
      return config;
    } catch (error) {
      console.error('[ConfigManager] 加载配置失败:', error);
      throw error;
    }
  }

  /**
   * 清除缓存
   */
  clearCache(): void {
    this.cachedConfig = null;
    console.log('[ConfigManager] 缓存已清除');
  }
}

