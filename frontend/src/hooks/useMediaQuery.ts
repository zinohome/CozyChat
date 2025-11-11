import { useState, useEffect } from 'react';

/**
 * 媒体查询Hook
 *
 * 用于响应式设计，检测屏幕尺寸。
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    // 服务端渲染时返回false
    if (typeof window === 'undefined') {
      return;
    }

    const media = window.matchMedia(query);
    
    // 设置初始值
    if (media.matches !== matches) {
      setMatches(media.matches);
    }

    // 监听变化
    const listener = () => setMatches(media.matches);
    media.addEventListener('change', listener);

    return () => media.removeEventListener('change', listener);
  }, [matches, query]);

  return matches;
}

/**
 * 检测是否为移动端
 */
export function useIsMobile(): boolean {
  return useMediaQuery('(max-width: 767px)');
}

/**
 * 检测是否为平板端
 */
export function useIsTablet(): boolean {
  return useMediaQuery('(min-width: 768px) and (max-width: 1023px)');
}

/**
 * 检测是否为桌面端
 */
export function useIsDesktop(): boolean {
  return useMediaQuery('(min-width: 1024px)');
}

