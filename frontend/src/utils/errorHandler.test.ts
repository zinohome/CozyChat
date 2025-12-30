import { describe, it, expect, vi, beforeEach } from 'vitest';
import { showError, showSuccess } from './errorHandler';
import { message } from 'antd';

// Mock antd message
vi.mock('antd', () => ({
  message: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

describe('errorHandler', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('showError', () => {
    it('应该显示字符串错误消息', () => {
      const error = { message: '测试错误' };
      showError(error);
      expect(message.error).toHaveBeenCalledWith('测试错误');
    });

    it('应该从Error对象提取消息', () => {
      const error = new Error('错误消息');
      showError(error);
      expect(message.error).toHaveBeenCalledWith('错误消息');
    });

    it('应该从Axios错误响应提取消息', () => {
      const error = {
        response: {
          data: {
            message: '后端错误',
          },
          status: 400,
        },
      };
      showError(error);
      expect(message.error).toHaveBeenCalledWith('后端错误');
    });

    it('应该使用默认消息', () => {
      showError(null, '默认错误');
      expect(message.error).toHaveBeenCalledWith('默认错误');
    });
  });

  describe('showSuccess', () => {
    it('应该显示成功消息', () => {
      showSuccess('操作成功');
      expect(message.success).toHaveBeenCalledWith('操作成功');
    });
  });
});

