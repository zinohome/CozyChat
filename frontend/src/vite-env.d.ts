/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  /** 高德地图 API Key（用于前端天气工具） */
  readonly VITE_AMAP_MAPS_API_KEY?: string;
  /** Tavily 搜索 API Key（用于前端搜索工具） */
  readonly VITE_TAVILY_API_KEY?: string;
  /** Demo模式（true=启用，自动填入Demo账号） */
  readonly VITE_DEMO_MODE?: string;
  /** Demo用户名 */
  readonly VITE_DEMO_USERNAME?: string;
  /** Demo密码 */
  readonly VITE_DEMO_PASSWORD?: string;
  // 可以在这里添加其他环境变量
  // readonly VITE_APP_TITLE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

