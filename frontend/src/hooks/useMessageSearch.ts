import { useState, useMemo } from 'react';
import type { Message } from '@/types/chat';

/**
 * 消息搜索Hook返回值
 */
export interface UseMessageSearchReturn {
  /** 搜索关键词 */
  keyword: string;
  /** 设置搜索关键词 */
  setKeyword: (keyword: string) => void;
  /** 搜索结果 */
  results: Message[];
  /** 当前结果索引 */
  currentIndex: number;
  /** 是否正在搜索 */
  isSearching: boolean;
  /** 下一个结果 */
  next: () => void;
  /** 上一个结果 */
  previous: () => void;
  /** 清除搜索 */
  clear: () => void;
}

/**
 * 消息搜索Hook
 *
 * 提供消息搜索功能，支持关键词搜索、高亮显示等。
 */
export const useMessageSearch = (messages: Message[]): UseMessageSearchReturn => {
  const [keyword, setKeyword] = useState('');
  const [currentIndex, setCurrentIndex] = useState(-1);

  /**
   * 搜索结果
   */
  const results = useMemo(() => {
    if (!keyword.trim()) {
      return [];
    }

    const lowerKeyword = keyword.toLowerCase();
    return messages.filter((msg) => {
      const content = typeof msg.content === 'string' ? msg.content : (msg.content as any)?.text || '';
      return content.toLowerCase().includes(lowerKeyword);
    });
  }, [messages, keyword]);

  /**
   * 下一个结果
   */
  const next = () => {
    if (results.length === 0) return;
    setCurrentIndex((prev) => (prev + 1) % results.length);
  };

  /**
   * 上一个结果
   */
  const previous = () => {
    if (results.length === 0) return;
    setCurrentIndex((prev) => (prev - 1 + results.length) % results.length);
  };

  /**
   * 清除搜索
   */
  const clear = () => {
    setKeyword('');
    setCurrentIndex(-1);
  };

  return {
    keyword,
    setKeyword,
    results,
    currentIndex,
    isSearching: keyword.trim().length > 0,
    next,
    previous,
    clear,
  };
};

