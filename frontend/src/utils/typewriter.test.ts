import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Typewriter } from './typewriter';

describe('Typewriter', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('应该创建Typewriter实例', () => {
    const typewriter = new Typewriter('Hello');
    expect(typewriter).toBeInstanceOf(Typewriter);
  });

  it('应该逐字符显示文本', () => {
    const onUpdate = vi.fn();
    const onComplete = vi.fn();
    const typewriter = new Typewriter('Hi', {
      speed: 10,
      onUpdate,
      onComplete,
    });

    typewriter.start();

    // start()立即调用type()，type()先update再增加索引
    // 所以第一次显示空文本（currentIndex=0）
    expect(onUpdate).toHaveBeenCalledWith('|');

    // 第一次定时器触发，显示第一个字符（currentIndex=1）
    vi.advanceTimersByTime(10);
    expect(onUpdate).toHaveBeenCalledWith('H|');

    // 第二次定时器触发时，currentIndex=2，等于text.length，直接完成
    vi.advanceTimersByTime(10);
    expect(typewriter.isComplete()).toBe(true);
    expect(onComplete).toHaveBeenCalled();
  });

  it('应该支持暂停和恢复', () => {
    const onUpdate = vi.fn();
    const typewriter = new Typewriter('Hello', {
      speed: 10,
      onUpdate,
    });

    typewriter.start();
    vi.advanceTimersByTime(20);

    typewriter.pause();
    const pausedText = typewriter.getCurrentText();

    typewriter.resume();
    vi.advanceTimersByTime(10);

    expect(typewriter.getCurrentText().length).toBeGreaterThan(pausedText.length);
  });

  it('应该支持停止', () => {
    const typewriter = new Typewriter('Hello', { speed: 10 });
    typewriter.start();
    typewriter.stop();

    expect(typewriter.getCurrentText()).toBe('');
    expect(typewriter.isComplete()).toBe(false);
  });

  it('应该支持立即完成', () => {
    const onComplete = vi.fn();
    const typewriter = new Typewriter('Hello', {
      speed: 10,
      onComplete,
    });

    typewriter.start();
    typewriter.complete();

    expect(typewriter.getCurrentText()).toBe('Hello');
    expect(typewriter.isComplete()).toBe(true);
    expect(onComplete).toHaveBeenCalled();
  });

  it('应该隐藏光标', () => {
    const onUpdate = vi.fn();
    const typewriter = new Typewriter('Hi', {
      speed: 10,
      showCursor: false,
      onUpdate,
    });

    typewriter.start();
    vi.advanceTimersByTime(10);

    expect(onUpdate).toHaveBeenCalledWith('H');
  });
});

