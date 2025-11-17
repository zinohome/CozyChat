/**
 * 日志工具类
 * 
 * 支持通过环境变量控制日志输出级别
 * 
 * 使用方式：
 * import { logger } from '@/utils/logger';
 * logger.debug('调试信息');
 * logger.info('一般信息');
 * logger.warn('警告信息');
 * logger.error('错误信息');
 * 
 * 环境变量：
 * VITE_LOG_LEVEL: 'debug' | 'info' | 'warn' | 'error' | 'none'
 * 默认: 'info' (生产环境) 或 'debug' (开发环境)
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'none';

/**
 * 日志级别优先级（数字越大优先级越高）
 */
const LOG_LEVELS: Record<LogLevel, number> = {
  none: 0,
  debug: 1,
  info: 2,
  warn: 3,
  error: 4,
};

/**
 * 获取当前日志级别
 */
function getLogLevel(): LogLevel {
  // 优先从 vite.config.ts 中定义的 VITE_LOG_LEVEL 读取
  // 如果没有定义，则从环境变量读取
  const configLevel = import.meta.env.VITE_LOG_LEVEL as LogLevel | undefined;
  
  if (configLevel && LOG_LEVELS[configLevel] !== undefined) {
    return configLevel;
  }
  
  // 默认：开发环境使用 debug，生产环境使用 info
  return import.meta.env.DEV ? 'debug' : 'info';
}

/**
 * 日志工具类
 */
class Logger {
  private level: LogLevel;
  private levelValue: number;

  constructor() {
    this.level = getLogLevel();
    this.levelValue = LOG_LEVELS[this.level];
  }

  /**
   * 检查是否应该输出日志
   */
  private shouldLog(level: LogLevel): boolean {
    return LOG_LEVELS[level] >= this.levelValue;
  }

  /**
   * 格式化日志消息
   */
  private formatMessage(prefix: string, ...args: any[]): any[] {
    return [`[${prefix}]`, ...args];
  }

  /**
   * 调试日志（最详细）
   */
  debug(...args: any[]): void {
    if (this.shouldLog('debug')) {
      console.log(...this.formatMessage('DEBUG', ...args));
    }
  }

  /**
   * 信息日志
   */
  info(...args: any[]): void {
    if (this.shouldLog('info')) {
      console.log(...this.formatMessage('INFO', ...args));
    }
  }

  /**
   * 警告日志
   */
  warn(...args: any[]): void {
    if (this.shouldLog('warn')) {
      console.warn(...this.formatMessage('WARN', ...args));
    }
  }

  /**
   * 错误日志（始终输出）
   */
  error(...args: any[]): void {
    if (this.shouldLog('error')) {
      console.error(...this.formatMessage('ERROR', ...args));
    }
  }

  /**
   * 带标签的日志（用于特定模块）
   */
  withTag(tag: string) {
    return {
      debug: (...args: any[]) => {
        if (this.shouldLog('debug')) {
          console.log(...this.formatMessage(`${tag}`, ...args));
        }
      },
      info: (...args: any[]) => {
        if (this.shouldLog('info')) {
          console.log(...this.formatMessage(`${tag}`, ...args));
        }
      },
      warn: (...args: any[]) => {
        if (this.shouldLog('warn')) {
          console.warn(...this.formatMessage(`${tag}`, ...args));
        }
      },
      error: (...args: any[]) => {
        if (this.shouldLog('error')) {
          console.error(...this.formatMessage(`${tag}`, ...args));
        }
      },
    };
  }

  /**
   * 获取当前日志级别
   */
  getLevel(): LogLevel {
    return this.level;
  }

  /**
   * 设置日志级别（运行时动态设置）
   */
  setLevel(level: LogLevel): void {
    this.level = level;
    this.levelValue = LOG_LEVELS[level];
  }
}

// 导出单例
export const logger = new Logger();

// 导出类型
export type { LogLevel };

