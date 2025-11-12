import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

/**
 * 主题类型
 */
export type ThemeName = 'blue' | 'green' | 'purple' | 'orange' | 'pink' | 'cyan';

/**
 * UI状态
 */
interface UIState {
  theme: ThemeName;
  sidebarOpen: boolean;
  mobileMenuOpen: boolean;
  language: string;
}

/**
 * UIActions
 */
interface UIActions {
  setTheme: (theme: ThemeName) => void;
  setSidebarOpen: (open: boolean) => void;
  setMobileMenuOpen: (open: boolean) => void;
  setLanguage: (language: string) => void;
  toggleSidebar: () => void;
  toggleMobileMenu: () => void;
}

/**
 * UIStore
 */
type UIStore = UIState & UIActions;

/**
 * 初始状态
 */
const initialState: UIState = {
  theme: 'blue',
  sidebarOpen: true,
  mobileMenuOpen: false,
  language: 'zh-CN',
};

/**
 * UI状态管理Store
 *
 * 使用Zustand管理UI相关的全局状态。
 */
export const useUIStore = create<UIStore>()(
  devtools(
    persist(
      (set) => ({
        ...initialState,

        setTheme: (theme) =>
          set({
            theme,
          }),

        setSidebarOpen: (open) =>
          set({
            sidebarOpen: open,
          }),

        setMobileMenuOpen: (open) =>
          set({
            mobileMenuOpen: open,
          }),

        setLanguage: (language) =>
          set({
            language,
          }),

        toggleSidebar: () =>
          set((state) => ({
            sidebarOpen: !state.sidebarOpen,
          })),

        toggleMobileMenu: () =>
          set((state) => ({
            mobileMenuOpen: !state.mobileMenuOpen,
          })),
      }),
      {
        name: 'ui-storage',
        partialize: (state) => ({
          theme: state.theme,
          language: state.language,
        }),
      }
    ),
    { name: 'UIStore' }
  )
);

