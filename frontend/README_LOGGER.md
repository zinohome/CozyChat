# 前端日志工具使用指南

## 快速配置

### 在 vite.config.ts 中配置（推荐）

直接修改 `frontend/vite.config.ts` 文件中的 `LOG_LEVEL` 常量：

```typescript
// 日志级别配置
const LOG_LEVEL = 'warn'; // 修改这里来控制日志级别
```

可选值：
- `'debug'` - 显示所有日志（开发环境推荐）
- `'info'` - 显示信息、警告和错误（生产环境推荐）
- `'warn'` - 只显示警告和错误（推荐用于减少日志）
- `'error'` - 只显示错误
- `'none'` - 不显示任何日志

修改后需要重启开发服务器：

```bash
npm run dev
# 或
pnpm dev
```

## 使用方式

### 在代码中使用

```typescript
import { logger } from '@/utils/logger';

// 方式1：直接使用
logger.debug('调试信息');
logger.info('一般信息');
logger.warn('警告信息');
logger.error('错误信息');

// 方式2：使用标签（推荐）
const log = logger.withTag('MyModule');
log.debug('调试信息');
log.info('一般信息');
log.warn('警告信息');
log.error('错误信息');
```

## 日志级别说明

| 级别 | 说明 | 显示内容 |
|------|------|----------|
| `debug` | 最详细 | 所有日志 |
| `info` | 一般信息 | info、warn、error |
| `warn` | 警告 | warn、error |
| `error` | 错误 | 只显示 error |
| `none` | 静默 | 不显示任何日志 |

## 默认行为

- **开发环境**（`npm run dev`）: `debug`（显示所有日志）
- **生产环境**（`npm run build`）: `info`（只显示重要信息）

## 已替换的文件

以下文件已经使用新的日志工具：

- ✅ `frontend/src/features/voice/services/ConfigManager.ts`
- ✅ `frontend/src/features/voice/services/VoiceAgentService.ts`

## 其他文件

其他文件仍在使用 `console.log`，可以根据需要逐步替换。参考 `docs/frontend-logger-usage.md` 了解详细的使用说明和迁移指南。

