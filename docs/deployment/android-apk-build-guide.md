# Android APK 打包指南

本指南说明如何将 CozyChat Web 应用打包成 Android APK。

## 方案概述

使用 **Capacitor** 将 Web 应用打包为原生 Android 应用。Capacitor 支持两种运行模式：

### 模式一：远程 URL 模式（当前默认）

应用在运行时从服务器加载 Web 应用，类似于浏览器访问网页。

**优点**：
- ✅ Web 应用更新无需重新发布 APK
- ✅ 可以快速修复问题并立即生效
- ✅ APK 体积小（不包含前端资源）

**缺点**：
- ❌ 需要网络连接才能使用
- ❌ 首次加载可能较慢
- ❌ 依赖服务器可用性

### 模式二：本地打包模式（推荐用于离线场景）

将前端构建产物直接打包到 APK 中，应用完全离线运行。

**优点**：
- ✅ 完全离线运行，无需网络
- ✅ 启动速度快（本地资源）
- ✅ 不依赖服务器可用性
- ✅ 更好的原生应用体验

**缺点**：
- ❌ 前端更新需要重新发布 APK
- ❌ APK 体积较大（包含所有前端资源）

## 详细对比分析

### 技术架构对比

| 维度 | 远程 URL 模式 | 本地打包模式 |
|------|-------------|-------------|
| **资源加载方式** | 运行时从服务器下载 HTML/JS/CSS | 打包时嵌入到 APK 中 |
| **网络依赖** | 必需（首次和每次启动） | 仅 API 调用需要 |
| **资源存储** | 服务器 | APK 内部（assets） |
| **更新机制** | 服务器端更新，客户端自动获取 | 需要重新构建和发布 APK |

### 性能对比

| 维度 | 远程 URL 模式 | 本地打包模式 |
|------|-------------|-------------|
| **首次启动速度** | ⚠️ 较慢（需要下载资源，通常 2-5 秒） | ✅ 快（本地资源，通常 <1 秒） |
| **后续启动速度** | ⚠️ 中等（可能仍有网络请求） | ✅ 快（完全本地） |
| **页面切换速度** | ✅ 快（资源已缓存） | ✅ 快（本地资源） |
| **网络流量消耗** | ⚠️ 每次启动需要下载（约 1-5 MB） | ✅ 仅 API 调用消耗流量 |
| **内存占用** | ✅ 较低（按需加载） | ⚠️ 较高（所有资源在内存中） |
| **APK 体积** | ✅ 小（通常 5-15 MB） | ⚠️ 大（通常 20-50 MB，取决于前端大小） |

### 开发体验对比

| 维度 | 远程 URL 模式 | 本地打包模式 |
|------|-------------|-------------|
| **开发迭代速度** | ✅ 极快（修改后立即生效，无需重新打包） | ⚠️ 较慢（需要重新构建和打包） |
| **调试便利性** | ✅ 方便（可以直接在浏览器调试） | ⚠️ 需要 Android Studio 或远程调试 |
| **构建复杂度** | ✅ 简单（只需构建一次，后续更新服务器） | ⚠️ 复杂（每次更新都需要完整构建流程） |
| **CI/CD 集成** | ✅ 简单（只需部署 Web 应用） | ⚠️ 复杂（需要构建 APK 并发布） |
| **版本管理** | ✅ 简单（Web 版本和 APK 版本解耦） | ⚠️ 复杂（前端版本和 APK 版本绑定） |

### 用户体验对比

| 维度 | 远程 URL 模式 | 本地打包模式 |
|------|-------------|-------------|
| **离线可用性** | ❌ 完全不可用（无网络无法启动） | ✅ 界面可用（但 API 调用会失败） |
| **弱网环境** | ⚠️ 体验差（加载慢或失败） | ✅ 体验好（界面正常，仅 API 慢） |
| **更新体验** | ✅ 无感更新（用户无感知） | ⚠️ 需要用户手动更新 APK |
| **启动体验** | ⚠️ 需要等待加载（有加载提示） | ✅ 即时启动（无等待感） |
| **数据安全** | ⚠️ 依赖服务器安全 | ✅ 前端代码在本地，相对更安全 |
| **隐私保护** | ⚠️ 服务器可能记录访问 | ✅ 前端代码本地运行，隐私更好 |

### 维护成本对比

| 维度 | 远程 URL 模式 | 本地打包模式 |
|------|-------------|-------------|
| **服务器成本** | ⚠️ 需要稳定的 CDN/服务器 | ✅ 仅需要 API 服务器 |
| **更新成本** | ✅ 低（只需更新服务器） | ⚠️ 高（需要重新构建、测试、发布） |
| **回滚成本** | ✅ 低（服务器端快速回滚） | ⚠️ 高（需要重新发布 APK） |
| **Bug 修复** | ✅ 快速（修复后立即生效） | ⚠️ 慢（需要重新发布，用户更新） |
| **版本兼容性** | ✅ 简单（服务器统一版本） | ⚠️ 复杂（需要处理多版本共存） |
| **测试成本** | ✅ 低（只需测试 Web 应用） | ⚠️ 高（需要测试 APK 构建和安装） |

### 安全性对比

| 维度 | 远程 URL 模式 | 本地打包模式 |
|------|-------------|-------------|
| **代码保护** | ⚠️ 代码在服务器，可能被分析 | ✅ 代码在 APK 中，相对更安全 |
| **中间人攻击** | ⚠️ 风险较高（网络传输） | ✅ 风险较低（本地资源） |
| **内容篡改** | ⚠️ 服务器可能被篡改 | ✅ APK 签名保护，难以篡改 |
| **HTTPS 要求** | ✅ 必需（现代 Android 要求） | ✅ 仅 API 调用需要 |
| **证书固定** | ⚠️ 需要配置（防止中间人攻击） | ✅ 不需要（本地资源） |

### 适用场景对比

#### 远程 URL 模式适合：

✅ **快速迭代的产品**
- 需要频繁更新功能
- Bug 修复需要快速响应
- A/B 测试需求

✅ **内容驱动的应用**
- 内容经常变化
- 需要实时更新内容
- 多租户 SaaS 应用

✅ **开发/测试阶段**
- 快速验证功能
- 减少构建和发布成本

✅ **网络条件良好的场景**
- 用户主要在 Wi-Fi 环境使用
- 网络稳定可靠

#### 本地打包模式适合：

✅ **离线优先的应用**
- 需要离线使用
- 弱网环境使用
- 数据敏感的应用

✅ **稳定成熟的产品**
- 功能相对稳定
- 更新频率低
- 版本发布周期长

✅ **性能敏感的应用**
- 要求快速启动
- 要求流畅体验
- 对网络延迟敏感

✅ **企业内部分发**
- 内部应用
- 不需要应用商店审核
- 可以快速分发更新

### 混合方案

也可以考虑**混合方案**，结合两种模式的优点：

1. **主要功能本地打包**：核心 UI 和功能打包到 APK
2. **动态内容远程加载**：部分内容从服务器加载
3. **渐进式更新**：通过 Service Worker 缓存策略，实现类似原生体验

### 成本效益分析

| 项目 | 远程 URL 模式 | 本地打包模式 |
|------|-------------|-------------|
| **初期开发成本** | 低 | 中等 |
| **持续维护成本** | 低（服务器成本） | 中等（构建和发布成本） |
| **用户获取成本** | 低（APK 体积小，下载快） | 中等（APK 体积大，下载慢） |
| **更新成本** | 极低（服务器更新） | 高（需要用户更新） |
| **服务器成本** | 高（需要 CDN/服务器） | 低（仅 API 服务器） |

## 选择模式

根据需求选择合适的模式：

### 快速决策树

```
需要离线使用？
├─ 是 → 本地打包模式
└─ 否 → 继续判断

需要快速更新？
├─ 是 → 远程 URL 模式
└─ 否 → 继续判断

网络条件如何？
├─ 不稳定/弱网 → 本地打包模式
└─ 稳定 → 继续判断

更新频率如何？
├─ 频繁（每周多次）→ 远程 URL 模式
└─ 不频繁（每月1-2次）→ 本地打包模式
```

### 推荐方案

- **开发/测试阶段**：推荐使用远程 URL 模式，便于快速迭代
- **MVP/早期版本**：推荐使用远程 URL 模式，快速响应反馈
- **稳定生产版本**：根据用户场景选择
  - 需要离线使用 → 本地打包模式
  - 需要快速更新 → 远程 URL 模式
  - 两者都需要 → 可以同时提供两个版本（如：CozyChat 和 CozyChat Offline）
- **企业内部分发**：推荐本地打包模式，更好的控制和安全性

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

### 2. 配置模式切换

#### 模式一：远程 URL 模式配置

**capacitor.config.ts** 配置（当前默认）：

```typescript
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
  android: {
    allowMixedContent: true,
    captureInput: true,
  },
};

export default config;
```

#### 模式二：本地打包模式配置

**capacitor.config.ts** 配置（本地打包）：

```typescript
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.cozychat.app',
  appName: 'CozyChat',
  webDir: 'dist', // 前端构建产物目录
  // 不配置 server.url，Capacitor 会自动使用本地资源
  android: {
    allowMixedContent: true,
    captureInput: true,
  },
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
```

**关键区别**：
- **远程模式**：配置 `server.url`，应用加载远程 URL
- **本地模式**：**不配置** `server.url`，应用使用本地打包的资源

### 3. API 基础 URL 配置

在本地打包模式下，前端需要知道后端 API 的地址。需要在构建时配置：

**方式一：环境变量（推荐）**

在 `frontend/.env.production` 中配置：

```bash
VITE_API_BASE_URL=https://api.naivehero.top
```

**方式二：构建时注入**

修改 `frontend/vite.config.ts`：

```typescript
export default defineConfig({
  define: {
    'import.meta.env.VITE_API_BASE_URL': JSON.stringify(
      process.env.VITE_API_BASE_URL || 'https://api.naivehero.top'
    ),
  },
});
```

## 构建步骤

### 模式一：远程 URL 模式构建

#### 1. 同步 Capacitor 配置

```bash
cd frontend
# 确保 capacitor.config.ts 中配置了 server.url
npx cap sync android  # 同步配置到Android项目
```

**注意**：远程模式不需要构建前端，因为加载的是远程 URL。

#### 2. 打开 Android 项目

```bash
npx cap open android
```

#### 3. 在 Android Studio 中构建

按照下面的"通用构建步骤"进行构建。

### 模式二：本地打包模式构建

#### 1. 构建前端

```bash
cd frontend
# 确保 capacitor.config.ts 中没有配置 server.url
pnpm build  # 构建前端到 dist 目录
```

#### 2. 同步到 Android 项目

```bash
npx cap sync android  # 将 dist 目录内容复制到 Android 项目
```

这一步会将 `dist/` 目录中的所有文件复制到 `android/app/src/main/assets/public/`。

#### 3. 打开 Android 项目

```bash
npx cap open android
```

#### 4. 在 Android Studio 中构建

按照下面的"通用构建步骤"进行构建。

### 通用构建步骤（两种模式通用）

#### 方式一：使用 Android Studio（推荐）

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

### 远程 URL 模式更新

当 Web 应用更新后，**无需重新打包 APK**（因为加载的是远程 URL）。但如果需要更新应用配置（如应用名称、图标等），需要：

1. 修改配置
2. 同步到 Android 项目：`npx cap sync android`
3. 重新构建 APK

### 本地打包模式更新

当需要更新前端功能时，需要：

1. **修改前端代码**
2. **重新构建前端**：`pnpm build`
3. **同步到 Android**：`npx cap sync android`
4. **重新构建 APK**：在 Android Studio 中构建或使用命令行

**自动化脚本**：

```bash
#!/bin/bash
# build-local-apk.sh - 本地打包模式构建脚本

cd frontend

# 1. 构建前端
echo "构建前端..."
pnpm build

# 2. 同步到 Android
echo "同步到 Android 项目..."
npx cap sync android

# 3. 构建 APK
echo "构建 APK..."
cd android
./gradlew assembleRelease

echo "✅ APK 构建完成！"
echo "位置: app/build/outputs/apk/release/app-release.apk"
```

## 测试 APK

### 1. 安装到设备

```bash
# 通过 ADB 安装
adb install frontend/android/app/build/outputs/apk/debug/app-debug.apk

# 或直接传输到设备安装
```

### 2. 测试要点

#### 远程 URL 模式测试

- ✅ 应用能正常启动
- ✅ 能加载远程 URL（https://chat.naivehero.top/）
- ✅ 网络请求正常（检查网络权限）
- ✅ 返回键、多任务切换正常
- ✅ 横竖屏切换正常

#### 本地打包模式测试

- ✅ 应用能正常启动（无需网络）
- ✅ 前端界面正常显示
- ✅ API 请求正常（检查网络权限和 API 地址配置）
- ✅ 返回键、多任务切换正常
- ✅ 横竖屏切换正常
- ✅ **离线测试**：关闭网络后应用仍能正常显示界面（但 API 请求会失败）

## 常见问题

### 1. Gradle 同步失败

**问题**：Android Studio 中 Gradle 同步失败

**解决**：
- 检查网络连接（需要下载依赖）
- 检查 `frontend/android/gradle/wrapper/gradle-wrapper.properties` 中的 Gradle 版本
- 尝试清理：`cd frontend/android && ./gradlew clean`

### 1.1. 缺少 cordova.variables.gradle 文件

**问题**：构建时出现错误：
```
Could not read script '.../capacitor-cordova-android-plugins/cordova.variables.gradle' as it does not exist.
```

**原因**：Capacitor 同步不完整，缺少必要的目录和文件。

**解决**：

1. **创建 assets 目录**（如果不存在）：
   ```bash
   cd frontend
   mkdir -p android/app/src/main/assets
   ```

2. **运行 Capacitor 同步**：
   ```bash
   npx cap sync android
   ```

3. **验证文件已创建**：
   ```bash
   ls -la android/capacitor-cordova-android-plugins/cordova.variables.gradle
   ```

4. **如果仍然失败，尝试清理并重新同步**：
   ```bash
   cd frontend/android
   ./gradlew clean
   cd ..
   npx cap sync android
   ```

**预防措施**：
- 首次设置 Android 项目时，务必运行 `npx cap sync android`
- 修改 `capacitor.config.ts` 后，需要重新运行 `npx cap sync android`
- 不要手动删除 `android/capacitor-cordova-android-plugins/` 目录

### 2. 无法加载远程 URL（仅远程模式）

**问题**：应用启动后显示空白或无法加载

**解决**：
- 检查 `capacitor.config.ts` 中的 `server.url` 配置
- 检查 AndroidManifest.xml 中的 INTERNET 权限
- 检查网络连接

### 2.1. 本地打包模式显示空白

**问题**：本地打包模式下应用启动后显示空白

**解决**：
- 确认 `capacitor.config.ts` 中**没有**配置 `server.url`
- 确认已执行 `pnpm build` 构建前端
- 确认已执行 `npx cap sync android` 同步资源
- 检查 `android/app/src/main/assets/public/` 目录是否有文件
- 检查浏览器控制台错误（在 Android Studio 的 Logcat 中查看）
- 检查 API 基础 URL 配置是否正确

### 3. 构建失败：找不到 Java

**问题**：命令行构建时提示找不到 Java

**解决**：
- 安装 Java JDK 11+
- 配置 JAVA_HOME 环境变量
- 或在 Android Studio 中构建

### 4. APK 文件过大

**问题**：生成的 APK 文件很大

**解决**：
- **本地打包模式**：APK 会包含所有前端资源，体积较大是正常的
  - 启用代码混淆（ProGuard）
  - 使用 AAB（Android App Bundle）格式替代 APK
  - 移除未使用的资源
  - 启用 Vite 构建优化（代码分割、压缩等）
- **远程 URL 模式**：如果 APK 仍然很大，检查是否误打包了前端资源

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

### 远程 URL 模式构建脚本

```bash
#!/bin/bash
# build-remote-apk.sh - 远程 URL 模式

cd frontend

# 同步到 Android（不需要构建前端）
npx cap sync android

# 构建 APK
cd android
./gradlew assembleRelease

echo "✅ APK 构建完成！"
echo "位置: app/build/outputs/apk/release/app-release.apk"
```

### 本地打包模式构建脚本

```bash
#!/bin/bash
# build-local-apk.sh - 本地打包模式

cd frontend

# 1. 构建前端
echo "📦 构建前端..."
pnpm build

# 2. 同步到 Android
echo "🔄 同步到 Android 项目..."
npx cap sync android

# 3. 构建 APK
echo "🔨 构建 APK..."
cd android
./gradlew assembleRelease

echo "✅ APK 构建完成！"
echo "位置: app/build/outputs/apk/release/app-release.apk"
```

### 通用构建脚本（自动检测模式）

```bash
#!/bin/bash
# build-apk.sh - 自动检测模式

cd frontend

# 检查配置文件中是否有 server.url
if grep -q "server:" capacitor.config.ts && grep -q "url:" capacitor.config.ts; then
  echo "🌐 检测到远程 URL 模式"
  MODE="remote"
else
  echo "📱 检测到本地打包模式"
  MODE="local"
fi

if [ "$MODE" = "local" ]; then
  # 本地模式：需要构建前端
  echo "📦 构建前端..."
  pnpm build
fi

# 同步到 Android
echo "🔄 同步到 Android 项目..."
npx cap sync android

# 构建 APK
echo "🔨 构建 APK..."
cd android
./gradlew assembleRelease

echo "✅ APK 构建完成！"
echo "位置: app/build/outputs/apk/release/app-release.apk"
```

## 参考资源

- [Capacitor 官方文档](https://capacitorjs.com/docs)
- [Android 开发文档](https://developer.android.com/)
- [Capacitor Android 指南](https://capacitorjs.com/docs/android)

## 注意事项

### 远程 URL 模式注意事项

1. **网络依赖**：应用依赖网络加载远程 Web 应用，确保设备有网络连接
2. **HTTPS 要求**：现代 Android 要求 HTTPS，确保服务器支持 HTTPS
3. **权限管理**：根据功能需求添加相应权限（如相机、麦克风等）
4. **性能优化**：WebView 性能可能不如原生应用，注意优化 Web 应用性能
5. **更新机制**：由于加载远程 URL，Web 应用更新无需重新发布 APK

### 本地打包模式注意事项

1. **API 配置**：确保前端正确配置了 API 基础 URL（`VITE_API_BASE_URL`）
2. **构建顺序**：必须先构建前端（`pnpm build`），再同步到 Android（`npx cap sync android`）
3. **资源路径**：前端代码中的资源路径需要使用相对路径，避免绝对路径
4. **APK 体积**：本地打包模式 APK 体积较大（包含所有前端资源），这是正常的
5. **更新机制**：前端更新需要重新构建并发布 APK
6. **离线功能**：前端界面可以离线显示，但 API 请求仍需要网络连接
7. **缓存策略**：考虑实现 Service Worker 或缓存策略，提升离线体验

### 通用注意事项

1. **权限管理**：根据功能需求添加相应权限（如相机、麦克风、网络等）
2. **性能优化**：WebView 性能可能不如原生应用，注意优化 Web 应用性能
3. **测试覆盖**：在不同 Android 版本和设备上测试应用
4. **错误处理**：实现完善的错误处理和用户提示

