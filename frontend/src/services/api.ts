import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  AxiosError,
} from 'axios';
import type { ApiResponse } from '@/types/api';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://192.168.32.155:8000';

/**
 * API客户端类
 *
 * 封装Axios，提供统一的API调用接口。
 */
class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * 是否正在刷新Token
   */
  private isRefreshing = false;

  /**
   * 待重试的请求队列
   */
  private failedQueue: Array<{
    resolve: (value?: any) => void;
    reject: (error?: any) => void;
  }> = [];

  /**
   * 处理队列中的请求
   */
  private processQueue(error: any, token: string | null = null): void {
    this.failedQueue.forEach((prom) => {
      if (error) {
        prom.reject(error);
      } else {
        prom.resolve(token);
      }
    });
    this.failedQueue = [];
  }

  /**
   * 刷新Token
   */
  private async refreshToken(): Promise<string | null> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      return null;
    }

    try {
      // 使用原始axios客户端，避免拦截器循环
      const response = await axios.post<{
        access_token: string;
        expires_in: number;
      }>(
        `${API_BASE_URL}/v1/auth/refresh`,
        { refresh_token: refreshToken },
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      const newAccessToken = response.data.access_token;
      if (newAccessToken) {
        localStorage.setItem('access_token', newAccessToken);
        return newAccessToken;
      }
      return null;
    } catch (error) {
      // 刷新失败，清除所有token
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      return null;
    }
  }

  /**
   * 设置请求和响应拦截器
   */
  private setupInterceptors(): void {
    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        // 如果是401错误且不是刷新token的请求
        if (error.response?.status === 401 && !originalRequest._retry) {
          // 如果正在刷新，将请求加入队列
          if (this.isRefreshing) {
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            })
              .then((token) => {
                originalRequest.headers.Authorization = `Bearer ${token}`;
                return this.client(originalRequest);
              })
              .catch((err) => {
                return Promise.reject(err);
              });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            const newToken = await this.refreshToken();
            if (newToken) {
              // 处理队列中的请求
              this.processQueue(null, newToken);
              // 重试原始请求
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              this.isRefreshing = false;
              return this.client(originalRequest);
            } else {
              // 刷新失败，处理队列并跳转登录
              this.processQueue(new Error('Token refresh failed'));
              this.isRefreshing = false;
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              if (window.location.pathname !== '/login') {
                window.location.href = '/login';
              }
              return Promise.reject(error);
            }
          } catch (refreshError) {
            // 刷新失败，处理队列并跳转登录
            this.processQueue(refreshError);
            this.isRefreshing = false;
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            if (window.location.pathname !== '/login') {
              window.location.href = '/login';
            }
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  /**
   * GET请求
   */
  async get<T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.get<ApiResponse<T>>(url, config);
    return this.handleResponse<T>(response);
  }

  /**
   * POST请求
   */
  async post<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.post<ApiResponse<T>>(url, data, config);
    return this.handleResponse<T>(response);
  }

  /**
   * PUT请求
   */
  async put<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.put<ApiResponse<T>>(url, data, config);
    return this.handleResponse<T>(response);
  }

  /**
   * DELETE请求
   */
  async delete<T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.delete<ApiResponse<T>>(url, config);
    return this.handleResponse<T>(response);
  }

  /**
   * 处理响应
   */
  private handleResponse<T>(response: AxiosResponse<ApiResponse<T>>): T {
    if (response.data.data !== undefined) {
      return response.data.data;
    }
    return response.data as T;
  }

  /**
   * 获取原始客户端（用于特殊需求）
   */
  getRawClient(): AxiosInstance {
    return this.client;
  }
}

export const apiClient = new ApiClient();

