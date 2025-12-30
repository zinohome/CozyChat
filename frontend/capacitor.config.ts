import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.cozychat.app',
  appName: 'CozyChat',
  webDir: 'dist',
  // 配置服务器URL（用于加载远程Web应用）
  server: {
    url: 'https://chat.naivehero.top',
    cleartext: true, // 允许HTTP（如果需要）
  },
  // Android配置
  android: {
    allowMixedContent: true, // 允许混合内容（HTTP和HTTPS）
    captureInput: true, // 捕获输入
  },
  // 插件配置
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      launchAutoHide: true,
      backgroundColor: '#ffffff',
      androidSplashResourceName: 'splash',
      androidScaleType: 'CENTER_CROP',
      showSpinner: false,
    },
  },
};

export default config;
