# Android APK 快速开始

## 快速构建 APK

### 前置要求

1. 安装 **Android Studio**：https://developer.android.com/studio
2. 在 Android Studio 中安装 Android SDK

### 构建步骤

#### 1. 同步配置（首次或配置变更后）

```bash
cd frontend
pnpm cap:sync
```

#### 2. 打开 Android Studio

```bash
pnpm cap:open
```

这会自动打开 Android Studio 并加载 Android 项目。

#### 3. 在 Android Studio 中构建 APK

1. 等待 Gradle 同步完成（首次可能需要几分钟）
2. 点击菜单：**Build** → **Build Bundle(s) / APK(s)** → **Build APK(s)**
3. 构建完成后，点击通知中的 **locate** 链接，或手动找到：
   ```
   frontend/android/app/build/outputs/apk/debug/app-debug.apk
   ```

#### 4. 安装到设备测试

```bash
# 通过 ADB 安装（需要连接设备并开启USB调试）
adb install frontend/android/app/build/outputs/apk/debug/app-debug.apk
```

## 常用命令

```bash
# 同步配置到 Android 项目
pnpm cap:sync

# 打开 Android Studio
pnpm cap:open

# 构建前端并同步（如果修改了前端代码）
pnpm cap:build
```

## 应用配置

应用已配置为加载远程 URL：`https://chat.naivehero.top/`

如需修改，编辑 `frontend/capacitor.config.ts`：

```typescript
server: {
  url: 'https://chat.naivehero.top',  // 修改这里
}
```

然后运行 `pnpm cap:sync` 同步配置。

## 详细文档

完整文档请参考：[Android APK 打包指南](./android-apk-build-guide.md)

