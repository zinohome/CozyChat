import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
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

