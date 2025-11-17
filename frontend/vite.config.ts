import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// 日志级别配置
// 可选值: 'debug' | 'info' | 'warn' | 'error' | 'none'
// debug: 显示所有日志（开发环境推荐）
// info: 显示信息、警告和错误（生产环境推荐）
// warn: 只显示警告和错误
// error: 只显示错误
// none: 不显示任何日志
const LOG_LEVEL = 'debug'; // 修改这里来控制日志级别

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

