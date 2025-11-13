/**
 * 时区工具函数
 * 
 * 提供时区转换和格式化功能。
 */

import { formatInTimeZone } from 'date-fns-tz';

/**
 * 支持的时区列表
 */
export const TIMEZONES = [
  { value: 'Asia/Shanghai', label: '上海 (UTC+8)' },
  { value: 'Asia/Tokyo', label: '东京 (UTC+9)' },
  { value: 'Asia/Hong_Kong', label: '香港 (UTC+8)' },
  { value: 'Asia/Singapore', label: '新加坡 (UTC+8)' },
  { value: 'America/New_York', label: '纽约 (UTC-5)' },
  { value: 'America/Los_Angeles', label: '洛杉矶 (UTC-8)' },
  { value: 'Europe/London', label: '伦敦 (UTC+0)' },
  { value: 'Europe/Paris', label: '巴黎 (UTC+1)' },
  { value: 'Australia/Sydney', label: '悉尼 (UTC+10)' },
] as const;

/**
 * 默认时区
 */
export const DEFAULT_TIMEZONE = 'Asia/Shanghai';

/**
 * 格式化时间（带时区）
 * 
 * @param date 日期对象、字符串或时间戳
 * @param timezone 时区（默认：Asia/Shanghai）
 * @param formatStr 格式化字符串（默认：'YYYY-MM-DD HH:mm:ss'）
 * @returns 格式化后的时间字符串
 */
export function formatDateTime(
  date: Date | string | number | undefined | null,
  timezone: string = DEFAULT_TIMEZONE,
  formatStr: string = 'yyyy-MM-dd HH:mm:ss'
): string {
  if (!date) {
    return '--';
  }

  try {
    let dateObj: Date;
    
    if (typeof date === 'string') {
      // 如果字符串以 'Z' 结尾或包含时区信息，new Date() 会正确解析为 UTC 时间
      // 如果字符串没有时区信息，假设它是 UTC 时间（后端返回的时间都是 UTC）
      if (date.endsWith('Z') || date.includes('+') || date.includes('-', 10)) {
        // ISO 格式字符串（包含时区信息），直接解析
        dateObj = new Date(date);
      } else {
        // 没有时区信息的 ISO 格式字符串，假设是 UTC 时间，添加 'Z' 后缀
        // 例如: "2025-11-13T03:00:21.054693" -> "2025-11-13T03:00:21.054693Z"
        dateObj = new Date(date + 'Z');
      }
    } else if (typeof date === 'number') {
      dateObj = new Date(date);
    } else {
      dateObj = date;
    }

    // 检查日期是否有效
    if (isNaN(dateObj.getTime())) {
      console.warn('Invalid date:', date);
      return '--';
    }

    // 使用 date-fns-tz 格式化时区时间
    // formatInTimeZone 会将 UTC 时间转换为指定时区的时间
    return formatInTimeZone(dateObj, timezone, formatStr);
  } catch (error) {
    console.warn('Failed to format date:', date, error);
    return '--';
  }
}

/**
 * 格式化时间（简短格式，仅时间）
 * 
 * @param date 日期对象、字符串或时间戳
 * @param timezone 时区（默认：Asia/Shanghai）
 * @returns 格式化后的时间字符串（HH:mm）
 */
export function formatTime(
  date: Date | string | number | undefined | null,
  timezone: string = DEFAULT_TIMEZONE
): string {
  return formatDateTime(date, timezone, 'HH:mm');
}

/**
 * 格式化日期（仅日期）
 * 
 * @param date 日期对象、字符串或时间戳
 * @param timezone 时区（默认：Asia/Shanghai）
 * @returns 格式化后的日期字符串（YYYY-MM-DD）
 */
export function formatDate(
  date: Date | string | number | undefined | null,
  timezone: string = DEFAULT_TIMEZONE
): string {
  return formatDateTime(date, timezone, 'yyyy-MM-dd');
}

