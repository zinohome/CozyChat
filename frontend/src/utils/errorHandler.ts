import { message } from 'antd';
import type { AxiosError } from 'axios';
import type { ApiError } from '@/types/api';

/**
 * 错误处理工具
 *
 * 提供统一的错误处理和用户提示。
 */

/**
 * 获取友好的错误消息
 */
export function getErrorMessage(error: any): string {
  // Axios错误
  if (error?.response) {
    const axiosError = error as AxiosError<ApiError>;
    const apiError = axiosError.response?.data;

    // API返回的错误消息
    if (apiError?.message) {
      return apiError.message;
    }

    // HTTP状态码对应的错误消息
    const status = axiosError.response?.status;
    switch (status) {
      case 400:
        return '请求参数错误';
      case 401:
        return '未授权，请重新登录';
      case 403:
        return '没有权限访问';
      case 404:
        return '请求的资源不存在';
      case 500:
        return '服务器内部错误';
      case 502:
        return '网关错误';
      case 503:
        return '服务不可用';
      default:
        return `请求失败 (${status})`;
    }
  }

  // 网络错误（包括 Failed to fetch）
  if (
    error?.message === 'Network Error' ||
    error?.message === 'Failed to fetch' ||
    error?.code === 'ECONNABORTED' ||
    error?.code === 'ERR_NETWORK'
  ) {
    // 检查是否是微信浏览器
    const isWeChat = /MicroMessenger/i.test(navigator.userAgent);
    if (isWeChat) {
      return '网络连接失败，请检查：1) 网络是否正常 2) 后端服务是否可访问 3) 是否使用 HTTPS';
    }
    return '网络连接失败，请检查网络设置';
  }

  // 超时错误
  if (error?.code === 'ETIMEDOUT' || error?.code === 'ECONNABORTED') {
    return '请求超时，请稍后重试';
  }

  // CORS 错误
  if (error?.message?.includes('CORS') || error?.message?.includes('cross-origin')) {
    return '跨域请求被阻止，请联系管理员';
  }

  // 其他错误
  if (error?.message) {
    return error.message;
  }

  return '发生未知错误，请稍后重试';
}

/**
 * 显示错误提示
 */
export function showError(error: any, defaultMessage?: string): void {
  let errorMessage: string;
  if (error === null || error === undefined) {
    errorMessage = defaultMessage || '操作失败';
  } else {
    const extractedMessage = getErrorMessage(error);
    errorMessage = extractedMessage !== '发生未知错误，请稍后重试' 
      ? extractedMessage 
      : (defaultMessage || extractedMessage);
  }
  message.error(errorMessage);
}

/**
 * 显示成功提示
 */
export function showSuccess(messageText: string): void {
  message.success(messageText);
}

/**
 * 显示警告提示
 */
export function showWarning(messageText: string): void {
  message.warning(messageText);
}

/**
 * 显示信息提示
 */
export function showInfo(messageText: string): void {
  message.info(messageText);
}

/**
 * 显示确认对话框
 */
export function showConfirm(
  title: string,
  content: string,
  onOk: () => void | Promise<void>,
  onCancel?: () => void
): void {
  const { Modal } = require('antd');
  Modal.confirm({
    title,
    content,
    onOk,
    onCancel,
  });
}

