/**
 * 文本转换工具
 * 
 * 提供繁体中文转简体中文等功能
 */

import { toSimplified } from 'chinese-simple2traditional';

/**
 * 将繁体中文转换为简体中文
 * 
 * @param text - 输入文本（可能是繁体或简体）
 * @returns 转换后的简体中文文本
 * 
 * @example
 * ```ts
 * toSimplifiedChinese('繁體中文') // '繁体中文'
 * ```
 */
export function toSimplifiedChinese(text: string): string {
  if (!text) {
    return text;
  }

  try {
    // chinese-simple2traditional 会自动检测并转换繁体到简体
    // 如果文本已经是简体，不会改变
    const converted = toSimplified(text);
    return converted;
  } catch (error) {
    // 转换失败时返回原文本
    console.warn('Failed to convert text to simplified Chinese:', error);
    return text;
  }
}

/**
 * 检测文本是否包含繁体中文
 * 
 * @param text - 输入文本
 * @returns 如果包含繁体中文返回true，否则返回false
 */
export function isTraditionalChinese(text: string): boolean {
  if (!text) {
    return false;
  }

  try {
    // 如果转换后文本有变化，说明包含繁体
    const converted = toSimplified(text);
    return converted !== text;
  } catch {
    return false;
  }
}

