import { describe, it, expect, beforeEach } from 'vitest';
import { useUIStore } from './uiSlice';

describe('uiSlice', () => {
  beforeEach(() => {
    // 重置store状态
    useUIStore.setState({
      sidebarOpen: true,
      mobileMenuOpen: false,
      theme: 'light',
      language: 'zh-CN',
    });
  });

  it('应该初始化默认状态', () => {
    const state = useUIStore.getState();
    expect(state.sidebarOpen).toBe(true);
    expect(state.mobileMenuOpen).toBe(false);
    expect(state.theme).toBe('auto');
    expect(state.language).toBe('zh-CN');
  });

  it('应该切换侧边栏', () => {
    useUIStore.getState().setSidebarOpen(false);
    expect(useUIStore.getState().sidebarOpen).toBe(false);

    useUIStore.getState().setSidebarOpen(true);
    expect(useUIStore.getState().sidebarOpen).toBe(true);
  });

  it('应该切换移动端菜单', () => {
    useUIStore.getState().setMobileMenuOpen(true);
    expect(useUIStore.getState().mobileMenuOpen).toBe(true);
  });

  it('应该设置主题', () => {
    useUIStore.getState().setTheme('dark');
    expect(useUIStore.getState().theme).toBe('dark');
  });

  it('应该设置语言', () => {
    useUIStore.getState().setLanguage('en-US');
    expect(useUIStore.getState().language).toBe('en-US');
  });
});

