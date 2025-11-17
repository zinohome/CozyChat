/**
 * XSS防护工具
 * 
 * 使用DOMPurify清理HTML内容，防止XSS攻击
 */

import DOMPurify from 'dompurify';

/**
 * 清理HTML内容
 * 
 * @param html - 要清理的HTML字符串
 * @param options - DOMPurify配置选项
 * @returns 清理后的HTML字符串
 */
export const sanitizeHtml = (
  html: string,
  options?: DOMPurify.Config
): string => {
  if (!html) {
    return '';
  }

  // 默认配置：只允许安全的HTML标签和属性
  const defaultOptions: DOMPurify.Config = {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'em', 'u', 's', 'code', 'pre',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li', 'blockquote',
      'a', 'img', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
      'hr', 'del', 'ins', 'sub', 'sup'
    ],
    ALLOWED_ATTR: [
      'href', 'title', 'alt', 'src', 'width', 'height',
      'class', 'id', 'target', 'rel'
    ],
    ALLOW_DATA_ATTR: false, // 不允许data-*属性
    ALLOW_UNKNOWN_PROTOCOLS: false, // 不允许未知协议
    SAFE_FOR_TEMPLATES: false, // 不使用模板模式（更严格）
    ...options, // 允许覆盖默认配置
  };

  return DOMPurify.sanitize(html, defaultOptions);
};

/**
 * 清理Markdown渲染后的HTML
 * 
 * 专门用于清理react-markdown渲染后的HTML内容
 * 
 * @param html - Markdown渲染后的HTML
 * @returns 清理后的HTML字符串
 */
export const sanitizeMarkdownHtml = (html: string): string => {
  return sanitizeHtml(html, {
    // Markdown允许的标签
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'em', 'u', 's', 'code', 'pre',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li', 'blockquote',
      'a', 'img', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
      'hr', 'del', 'ins', 'sub', 'sup', 'span'
    ],
    // Markdown允许的属性
    ALLOWED_ATTR: [
      'href', 'title', 'alt', 'src', 'width', 'height',
      'class', 'id', 'target', 'rel', 'data-line'
    ],
    // 允许data-line属性（代码高亮使用）
    ALLOW_DATA_ATTR: true,
  });
};

/**
 * 清理纯文本（移除所有HTML标签）
 * 
 * @param text - 包含HTML的文本
 * @returns 纯文本
 */
export const sanitizeText = (text: string): string => {
  if (!text) {
    return '';
  }
  
  return DOMPurify.sanitize(text, {
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: [],
  });
};

/**
 * 清理URL
 * 
 * 确保URL是安全的（只允许http、https、mailto等协议）
 * 
 * @param url - URL字符串
 * @returns 清理后的URL或空字符串
 */
export const sanitizeUrl = (url: string): string => {
  if (!url) {
    return '';
  }

  // 只允许安全的协议
  const allowedProtocols = ['http:', 'https:', 'mailto:', 'tel:'];
  
  try {
    const urlObj = new URL(url);
    if (allowedProtocols.includes(urlObj.protocol)) {
      return url;
    }
  } catch {
    // 如果不是有效URL，返回空字符串
  }

  return '';
};

