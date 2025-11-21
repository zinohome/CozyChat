# Android APK 打包指南

本指南说明如何将 CozyChat Web 应用打包成 Android APK。

## 方案概述

使用 **Capacitor** 将 Web 应用打包为原生 Android 应用。Capacitor 会在 Android 应用中嵌入 WebView，加载远程 Web 应用（https://chat.naivehero.top/）。

## 前置要求

### 1. 开发环境

- **Node.js** 18+ 和 **pnpm**
- **Java JDK** 11 或更高版本
- **Android Studio**（用于构建 APK）
- **Android SDK**（通过 Android Studio 安装）

### 2. 安装 Android Studio

1. 下载并安装 [Android Studio](https://developer.android.com/studio)
2. 打开 Android Studio，安装 Android SDK
3. 配置环境变量（可选，但推荐）：

```bash
# ~/.zshrc 或 ~/.bashrc
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/tools/bin
```

## 项目配置

### 1. Capacitor 已配置

项目已配置 Capacitor，配置文件位于：
- `frontend/capacitor.config.ts` - Capacitor 主配置
- `frontend/android/` - Android 项目目录

### 2. 配置说明

**capacitor.config.ts** 关键配置：

```typescript
{
  appId: 'com.cozychat.app',
  appName: 'CozyChat',
  webDir: 'dist',
  server: {
    url: 'https://chat.naivehero.top',  // 远程Web应用URL
    cleartext: true,
  },
}
```

## 构建步骤

### 方式一：使用 Android Studio（推荐）

#### 1. 同步 Capacitor 配置

```bash
cd frontend
pnpm build  # 构建前端（如果需要）
npx cap sync android  # 同步配置到Android项目
```

#### 2. 打开 Android 项目

```bash
npx cap open android
```

这会自动打开 Android Studio。

#### 3. 在 Android Studio 中构建

1. 等待 Gradle 同步完成
2. 选择 **Build** → **Build Bundle(s) / APK(s)** → **Build APK(s)**
3. 构建完成后，APK 文件位于：
   ```
   frontend/android/app/build/outputs/apk/debug/app-debug.apk
   ```

#### 4. 生成签名 APK（发布版本）

1. **创建签名密钥**（首次需要）：
   ```bash
   keytool -genkey -v -keystore cozychat-release-key.jks \
     -keyalg RSA -keysize 2048 -validity 10000 \
     -alias cozychat
   ```

2. **配置签名**：
   在 `frontend/android/app/build.gradle` 中添加：

   ```gradle
   android {
       signingConfigs {
           release {
               storeFile file('../../cozychat-release-key.jks')
               storePassword 'your-store-password'
               keyAlias 'cozychat'
               keyPassword 'your-key-password'
           }
       }
       buildTypes {
           release {
               signingConfig signingConfigs.release
               minifyEnabled false
           }
       }
   }
   ```

3. **构建 Release APK**：
   - 在 Android Studio 中选择 **Build** → **Generate Signed Bundle / APK**
   - 选择 **APK**，使用上面的密钥签名
   - 生成的 APK 位于：
     ```
     frontend/android/app/build/outputs/apk/release/app-release.apk
     ```

### 方式二：命令行构建（需要配置好环境）

#### 1. 构建 Debug APK

```bash
cd frontend/android
./gradlew assembleDebug
```

APK 位置：`app/build/outputs/apk/debug/app-debug.apk`

#### 2. 构建 Release APK

```bash
cd frontend/android
./gradlew assembleRelease
```

APK 位置：`app/build/outputs/apk/release/app-release.apk`

## 应用配置

### 修改应用信息

#### 1. 应用名称和版本

编辑 `frontend/android/app/build.gradle`：

```gradle
defaultConfig {
    applicationId "com.cozychat.app"
    versionCode 1  // 每次发布递增
    versionName "1.0"  // 版本号
}
```

#### 2. 应用图标

替换以下文件：
- `frontend/android/app/src/main/res/mipmap-*/ic_launcher.png`
- `frontend/android/app/src/main/res/mipmap-*/ic_launcher_round.png`

可以使用 [Android Asset Studio](https://romannurik.github.io/AndroidAssetStudio/icons-launcher.html) 生成图标。

#### 3. 应用名称（显示名称）

编辑 `frontend/android/app/src/main/res/values/strings.xml`：

```xml
<resources>
    <string name="app_name">CozyChat</string>
    <string name="title_activity_main">CozyChat</string>
</resources>
```

## 更新应用

当 Web 应用更新后，无需重新打包 APK（因为加载的是远程 URL）。但如果需要更新应用配置（如应用名称、图标等），需要：

1. 修改配置
2. 同步到 Android 项目：`npx cap sync android`
3. 重新构建 APK

## 测试 APK

### 1. 安装到设备

```bash
# 通过 ADB 安装
adb install frontend/android/app/build/outputs/apk/debug/app-debug.apk

# 或直接传输到设备安装
```

### 2. 测试要点

- ✅ 应用能正常启动
- ✅ 能加载 https://chat.naivehero.top/
- ✅ 网络请求正常（检查网络权限）
- ✅ 返回键、多任务切换正常
- ✅ 横竖屏切换正常

## 常见问题

### 1. Gradle 同步失败

**问题**：Android Studio 中 Gradle 同步失败

**解决**：
- 检查网络连接（需要下载依赖）
- 检查 `frontend/android/gradle/wrapper/gradle-wrapper.properties` 中的 Gradle 版本
- 尝试清理：`cd frontend/android && ./gradlew clean`

### 2. 无法加载远程 URL

**问题**：应用启动后显示空白或无法加载

**解决**：
- 检查 `capacitor.config.ts` 中的 `server.url` 配置
- 检查 AndroidManifest.xml 中的 INTERNET 权限
- 检查网络连接

### 3. 构建失败：找不到 Java

**问题**：命令行构建时提示找不到 Java

**解决**：
- 安装 Java JDK 11+
- 配置 JAVA_HOME 环境变量
- 或在 Android Studio 中构建

### 4. APK 文件过大

**问题**：生成的 APK 文件很大

**解决**：
- 启用代码混淆（ProGuard）
- 使用 AAB（Android App Bundle）格式替代 APK
- 移除未使用的资源

## 发布到应用商店

### Google Play Store

1. 创建 Google Play 开发者账号
2. 准备应用截图、描述等材料
3. 上传 AAB 文件（推荐）或 APK
4. 填写应用信息并提交审核

### 其他应用商店

- **华为应用市场**：需要华为开发者账号
- **小米应用商店**：需要小米开发者账号
- **应用宝**：需要腾讯开放平台账号

## 自动化构建脚本

可以创建脚本自动化构建过程：

```bash
#!/bin/bash
# build-apk.sh

cd frontend

# 构建前端（如果需要）
# pnpm build

# 同步到 Android
npx cap sync android

# 构建 APK
cd android
./gradlew assembleRelease

echo "APK 构建完成！"
echo "位置: app/build/outputs/apk/release/app-release.apk"
```

## 参考资源

- [Capacitor 官方文档](https://capacitorjs.com/docs)
- [Android 开发文档](https://developer.android.com/)
- [Capacitor Android 指南](https://capacitorjs.com/docs/android)

## 注意事项

1. **网络依赖**：应用依赖网络加载远程 Web 应用，确保设备有网络连接
2. **HTTPS 要求**：现代 Android 要求 HTTPS，确保服务器支持 HTTPS
3. **权限管理**：根据功能需求添加相应权限（如相机、麦克风等）
4. **性能优化**：WebView 性能可能不如原生应用，注意优化 Web 应用性能
5. **更新机制**：由于加载远程 URL，Web 应用更新无需重新发布 APK

