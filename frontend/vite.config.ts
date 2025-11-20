import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

// 日志级别配置
// 可选值: 'debug' | 'info' | 'warn' | 'error' | 'none'
// debug: 显示所有日志（开发环境推荐）
// info: 显示信息、警告和错误（生产环境推荐）
// warn: 只显示警告和错误
// error: 只显示错误
// none: 不显示任何日志
// 从环境变量读取，如果没有设置则使用默认值（开发环境：debug，生产环境：info）
const LOG_LEVEL = process.env.VITE_LOG_LEVEL || (process.env.NODE_ENV === 'production' ? 'info' : 'debug');

// ES module 中获取 __dirname 的替代方案
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // 定义全局常量，供代码中使用
  define: {
    'import.meta.env.VITE_LOG_LEVEL': JSON.stringify(LOG_LEVEL),
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/v1': {
        target: 'http://192.168.32.155:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://192.168.32.155:8000',
        ws: true,
      },
    },
  },
});

