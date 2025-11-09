/**
 * 人格相关类型定义
 */

/**
 * 人格
 */
export interface Personality {
  id: string;
  name: string;
  description?: string;
  avatar_url?: string;
  system_prompt?: string;
  ai_config?: {
    provider: string;
    model: string;
    temperature?: number;
    max_tokens?: number;
  };
  memory_config?: {
    enabled: boolean;
    save_mode?: 'user' | 'ai' | 'both';
  };
  tools_config?: {
    enabled: boolean;
    allowed_tools?: string[];
  };
  voice_config?: {
    stt_enabled?: boolean;
    tts_enabled?: boolean;
    realtime_enabled?: boolean;
  };
  created_at?: Date | string;
  updated_at?: Date | string;
}

