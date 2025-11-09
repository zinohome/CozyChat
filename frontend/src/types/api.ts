/**
 * API相关类型定义
 */

/**
 * API响应基础结构
 */
export interface ApiResponse<T = any> {
  data?: T;
  error?: ApiError;
  message?: string;
}

/**
 * API错误结构
 */
export interface ApiError {
  code: string;
  message: string;
  details?: any;
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}

/**
 * 分页请求参数
 */
export interface PaginationParams {
  page?: number;
  page_size?: number;
}

