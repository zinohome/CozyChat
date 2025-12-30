/**
 * 文本转换工具
 * 
 * 提供繁体中文转简体中文等功能
 */

import { toSimplified, customT2SPhrases } from 'chinese-simple2traditional';
import { setupEnhance } from 'chinese-simple2traditional/enhance';

// 初始化短语库（只初始化一次）
let enhanceInitialized = false;

function initializeEnhance() {
  if (!enhanceInitialized) {
    setupEnhance();
    
    // 添加自定义短语修复已知的转换错误
    // 注意：customT2SPhrases 的参数是 [繁体短语, 简体短语] 的数组
    customT2SPhrases([
      // 修复"退休"相关词汇
      ['退休', '退休'],  // 修复：退休 -> 退休（而不是煺休）
      ['退休人員', '退休人员'],  // 修复：退休人员
      ['退休金', '退休金'],  // 修复：退休金
      ['退休工資', '退休工资'],  // 修复：退休工资
      // 修复"怎么"相关词汇
      ['怎麽', '怎么'],  // 修复：怎麽 -> 怎么
      ['怎麼樣', '怎么样'],  // 修复：怎么样 -> 怎么样
      ['怎麽樣', '怎么样'],  // 修复：怎麽样 -> 怎么样（备用）
    ]);
    
    enhanceInitialized = true;
  }
}

// 初始化短语库
initializeEnhance();

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
    // 使用增强模式（第二个参数传 true）以获得更精确的转换
    // 增强模式会使用短语库，避免单个字符转换导致的错误
    const converted = toSimplified(text, true);
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

