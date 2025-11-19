/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  /** 高德地图 API Key（用于前端天气工具） */
  readonly VITE_AMAP_MAPS_API_KEY?: string;
  /** Tavily 搜索 API Key（用于前端搜索工具） */
  readonly VITE_TAVILY_API_KEY?: string;
  // 可以在这里添加其他环境变量
  // readonly VITE_APP_TITLE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

