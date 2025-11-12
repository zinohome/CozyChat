/**
 * 用户相关类型定义
 */

/**
 * 用户角色
 */
export type UserRole = 'admin' | 'user' | 'guest';

/**
 * 用户
 */
export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  created_at: Date | string;
  updated_at: Date | string;
  is_active?: boolean;
}

/**
 * 用户资料
 */
export interface UserProfile {
  user_id: string;
  display_name?: string;
  avatar_url?: string;
  bio?: string;
  interests?: string[];
  habits?: Record<string, any>;
  preferences?: UserPreferences;
  created_at: Date | string;
  updated_at: Date | string;
}

/**
 * 聊天背景样式类型
 */
export type ChatBackgroundStyle = 'gradient' | 'solid';

/**
 * 用户偏好
 */
export interface UserPreferences {
  theme?: 'blue' | 'green' | 'purple' | 'orange' | 'pink' | 'cyan';
  language?: string;
  chatBackgroundStyle?: ChatBackgroundStyle;
  auto_tts?: boolean; // 自动播放语音
  notifications?: {
    email?: boolean;
    push?: boolean;
    sound?: boolean;
  };
  privacy?: {
    profile_visibility?: 'public' | 'private' | 'friends';
    show_online_status?: boolean;
  };
}

/**
 * 登录请求
 */
export interface LoginRequest {
  username: string;
  password: string;
}

/**
 * 注册请求
 */
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

/**
 * 认证响应
 */
export interface AuthResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  user: User;
}

