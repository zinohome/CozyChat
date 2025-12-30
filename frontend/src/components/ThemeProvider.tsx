import React, { useEffect } from 'react';
import { useTheme } from '@/hooks/useTheme';

/**
 * 主题提供者组件
 * 
 * 在应用启动时初始化主题。
 */
export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  useTheme();
  return <>{children}</>;
};

