/**
 * 打字机效果配置
 */
export interface TypewriterConfig {
  /** 打字速度（毫秒/字符） */
  speed?: number;
  /** 是否显示光标 */
  showCursor?: boolean;
  /** 光标字符 */
  cursorChar?: string;
  /** 完成回调 */
  onComplete?: () => void;
  /** 更新回调 */
  onUpdate?: (text: string) => void;
}

/**
 * 打字机效果类
 *
 * 实现打字机效果，逐字符显示文本。
 */
export class Typewriter {
  private text: string;
  private currentIndex: number;
  private config: Required<TypewriterConfig>;
  private timer: number | null = null;
  private isPaused: boolean = false;

  constructor(text: string, config: TypewriterConfig = {}) {
    this.text = text;
    this.currentIndex = 0;
    this.config = {
      speed: config.speed || 50,
      showCursor: config.showCursor ?? true,
      cursorChar: config.cursorChar || '|',
      onComplete: config.onComplete || (() => {}),
      onUpdate: config.onUpdate || (() => {}),
    };
  }

  /**
   * 开始打字
   */
  start(): void {
    if (this.timer) {
      return;
    }

    this.isPaused = false;
    this.type();
  }

  /**
   * 暂停
   */
  pause(): void {
    this.isPaused = true;
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  /**
   * 恢复
   */
  resume(): void {
    if (!this.isPaused) {
      return;
    }

    this.isPaused = false;
    this.type();
  }

  /**
   * 停止
   */
  stop(): void {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    this.isPaused = false;
    this.currentIndex = 0;
  }

  /**
   * 完成（立即显示所有文本）
   */
  complete(): void {
    this.stop();
    this.currentIndex = this.text.length;
    this.update();
    this.config.onComplete();
  }

  /**
   * 打字
   */
  private type(): void {
    if (this.isPaused || this.currentIndex >= this.text.length) {
      if (this.currentIndex >= this.text.length) {
        this.config.onComplete();
      }
      return;
    }

    this.update();
    this.currentIndex++;

    this.timer = window.setTimeout(() => {
      this.type();
    }, this.config.speed);
  }

  /**
   * 更新显示
   */
  private update(): void {
    const displayedText = this.text.slice(0, this.currentIndex);
    const finalText = this.config.showCursor
      ? displayedText + this.config.cursorChar
      : displayedText;
    this.config.onUpdate(finalText);
  }

  /**
   * 获取当前文本
   */
  getCurrentText(): string {
    return this.text.slice(0, this.currentIndex);
  }

  /**
   * 是否完成
   */
  isComplete(): boolean {
    return this.currentIndex >= this.text.length;
  }
}

