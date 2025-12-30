# 前端日志工具使用说明

## 概述

前端使用统一的日志工具 `logger` 来控制调试信息的显示。通过环境变量 `VITE_LOG_LEVEL` 可以控制日志输出级别。

## 快速开始

### 方式1：在 vite.config.ts 中配置（推荐）

直接修改 `frontend/vite.config.ts` 文件中的 `LOG_LEVEL` 常量：

```typescript
// 日志级别配置
const LOG_LEVEL = 'warn'; // 修改这里来控制日志级别
```

可选值：`'debug'` | `'info'` | `'warn'` | `'error'` | `'none'`

修改后需要重启开发服务器。

### 方式2：使用环境变量（可选）

在项目根目录创建 `.env` 文件（或修改现有的），添加：

```bash
# 显示所有日志（开发环境推荐）
VITE_LOG_LEVEL=debug

# 只显示警告和错误（生产环境推荐）
VITE_LOG_LEVEL=warn

# 不显示任何日志
VITE_LOG_LEVEL=none
```

**注意**：`vite.config.ts` 中的配置优先级更高。

### 2. 使用日志工具

```typescript
import { logger } from '@/utils/logger';

// 方式1：直接使用
logger.debug('调试信息');
logger.info('一般信息');
logger.warn('警告信息');
logger.error('错误信息');

// 方式2：使用标签（推荐，便于区分模块）
const log = logger.withTag('MyModule');
log.debug('调试信息');
log.info('一般信息');
log.warn('警告信息');
log.error('错误信息');
```

## 日志级别

| 级别 | 说明 | 使用场景 |
|------|------|----------|
| `debug` | 最详细的调试信息 | 开发调试时使用 |
| `info` | 一般信息 | 正常运行时的重要信息 |
| `warn` | 警告信息 | 潜在问题或异常情况 |
| `error` | 错误信息 | 错误和异常 |
| `none` | 不显示任何日志 | 生产环境静默模式 |

## 日志级别优先级

设置某个级别后，会显示该级别及更高级别的日志：

- `debug`: 显示所有日志
- `info`: 显示 info、warn、error
- `warn`: 显示 warn、error
- `error`: 只显示 error
- `none`: 不显示任何日志

## 替换现有的 console.log

### 批量替换步骤

1. **查找所有 console.log 调用**：
```bash
cd frontend
grep -r "console\.log" src/features/voice/
```

2. **替换模式**：

**替换前：**
```typescript
console.log('[ModuleName] 消息');
console.warn('[ModuleName] 警告');
console.error('[ModuleName] 错误');
```

**替换后：**
```typescript
import { logger } from '@/utils/logger';
const log = logger.withTag('ModuleName');

log.debug('消息');  // 或 log.info() 根据重要性
log.warn('警告');
log.error('错误');
```

### 已替换的文件

以下文件已经使用新的日志工具：

- ✅ `frontend/src/features/voice/services/ConfigManager.ts`
- ✅ `frontend/src/features/voice/services/VoiceAgentService.ts` (部分)

### 待替换的文件

以下文件仍在使用 `console.log`，建议逐步替换：

- `frontend/src/features/voice/strategies/WebRTCStrategy.ts`
- `frontend/src/features/voice/strategies/WebSocketStrategy.ts`
- `frontend/src/features/voice/services/EventHandler.ts`
- `frontend/src/features/voice/services/ToolManager.ts`
- `frontend/src/features/voice/services/SessionManager.ts`
- `frontend/src/features/voice/transports/WebSocketTransport.ts`
- `frontend/src/features/voice/transports/WebRTCTransport.ts`
- `frontend/src/features/voice/visualization/AudioVisualizer.ts`

## 运行时动态设置

```typescript
import { logger } from '@/utils/logger';

// 获取当前日志级别
const currentLevel = logger.getLevel();

// 动态设置日志级别（例如：根据用户设置）
logger.setLevel('warn');
```

## 环境变量配置

### 开发环境

在 `.env.development` 或 `.env` 中设置：

```bash
VITE_LOG_LEVEL=debug
```

### 生产环境

在 `.env.production` 中设置：

```bash
VITE_LOG_LEVEL=warn
```

### 默认行为

- 如果未设置 `VITE_LOG_LEVEL`：
  - 开发环境（`npm run dev`）: `debug`
  - 生产环境（`npm run build`）: `info`

## 注意事项

1. **错误日志始终显示**：`logger.error()` 在日志级别为 `error` 或更高时始终显示
2. **性能考虑**：即使日志不显示，日志参数仍会被计算，避免在日志调用中执行复杂计算
3. **标签使用**：使用 `logger.withTag()` 创建带标签的日志实例，便于区分不同模块

## 示例

### 完整示例

```typescript
import { logger } from '@/utils/logger';

const log = logger.withTag('MyService');

class MyService {
  async doSomething() {
    log.debug('开始执行操作');  // 只在 debug 级别显示
    
    try {
      const result = await someAsyncOperation();
      log.info('操作成功', result);  // 在 info 及以上级别显示
      return result;
    } catch (error) {
      log.error('操作失败', error);  // 始终显示（如果级别 >= error）
      throw error;
    }
  }
}
```

## 迁移指南

### 步骤1：导入 logger

在每个文件顶部添加：

```typescript
import { logger } from '@/utils/logger';
const log = logger.withTag('YourModuleName');
```

### 步骤2：替换 console.log

```typescript
// 替换前
console.log('[YourModule] 消息');

// 替换后
log.debug('消息');  // 或 log.info() 根据重要性
```

### 步骤3：替换 console.warn/error

```typescript
// 替换前
console.warn('[YourModule] 警告');
console.error('[YourModule] 错误');

// 替换后
log.warn('警告');
log.error('错误');
```

## 常见问题

**Q: 如何临时禁用所有日志？**

A: 设置 `VITE_LOG_LEVEL=none`，或使用 `logger.setLevel('none')`

**Q: 如何只显示错误日志？**

A: 设置 `VITE_LOG_LEVEL=error`

**Q: 日志会影响性能吗？**

A: 不会。日志工具会先检查级别，只有满足条件才会调用 console API。但注意不要在日志参数中执行复杂计算。

**Q: 可以在运行时动态改变日志级别吗？**

A: 可以，使用 `logger.setLevel('warn')` 等方法。

