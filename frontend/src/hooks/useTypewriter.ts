import { useState, useCallback, useRef, useEffect } from 'react';
import { Typewriter, type TypewriterConfig } from '@/utils/typewriter';

/**
 * 打字机效果Hook返回值
 */
export interface UseTypewriterReturn {
  /** 当前显示的文本 */
  text: string;
  /** 是否正在打字 */
  isTyping: boolean;
  /** 是否完成 */
  isComplete: boolean;
  /** 开始打字 */
  start: (text: string, config?: TypewriterConfig) => void;
  /** 暂停 */
  pause: () => void;
  /** 恢复 */
  resume: () => void;
  /** 停止 */
  stop: () => void;
  /** 完成（立即显示所有文本） */
  complete: () => void;
}

/**
 * 打字机效果Hook
 *
 * 提供打字机效果，逐字符显示文本。
 */
export const useTypewriter = (): UseTypewriterReturn => {
  const [text, setText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  const typewriterRef = useRef<Typewriter | null>(null);

  /**
   * 开始打字
   */
  const start = useCallback((text: string, config?: TypewriterConfig) => {
    // 停止之前的打字机
    if (typewriterRef.current) {
      typewriterRef.current.stop();
    }

    setIsComplete(false);
    setIsTyping(true);

    const typewriter = new Typewriter(text, {
      ...config,
      onUpdate: (displayedText) => {
        setText(displayedText);
      },
      onComplete: () => {
        setIsTyping(false);
        setIsComplete(true);
        config?.onComplete?.();
      },
    });

    typewriterRef.current = typewriter;
    typewriter.start();
  }, []);

  /**
   * 暂停
   */
  const pause = useCallback(() => {
    if (typewriterRef.current) {
      typewriterRef.current.pause();
      setIsTyping(false);
    }
  }, []);

  /**
   * 恢复
   */
  const resume = useCallback(() => {
    if (typewriterRef.current) {
      typewriterRef.current.resume();
      setIsTyping(true);
    }
  }, []);

  /**
   * 停止
   */
  const stop = useCallback(() => {
    if (typewriterRef.current) {
      typewriterRef.current.stop();
      setText('');
      setIsTyping(false);
      setIsComplete(false);
    }
  }, []);

  /**
   * 完成
   */
  const complete = useCallback(() => {
    if (typewriterRef.current) {
      typewriterRef.current.complete();
      setIsTyping(false);
      setIsComplete(true);
    }
  }, []);

  // 清理
  useEffect(() => {
    return () => {
      if (typewriterRef.current) {
        typewriterRef.current.stop();
      }
    };
  }, []);

  return {
    text,
    isTyping,
    isComplete,
    start,
    pause,
    resume,
    stop,
    complete,
  };
};

