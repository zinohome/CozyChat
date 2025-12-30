import { useEffect } from 'react';
import { useUIStore, type ThemeName } from '@/store/slices/uiSlice';

/**
 * 主题Hook
 * 
 * 管理主题切换和应用。
 */
export const useTheme = () => {
  const { theme } = useUIStore();

  useEffect(() => {
    const root = document.documentElement;
    
    // 应用主题
    root.setAttribute('data-theme', theme);
  }, [theme]);
};

