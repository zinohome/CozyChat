# CozyChat 文档和测试快速开始指南

> **快速参考**: 文档同步和测试开发的操作步骤

## 🚀 快速开始

### 1. 更新项目完成度（3步）

```bash
# 步骤1: 编辑数据源
vim docs/PROJECT_STATUS.json

# 步骤2: 预览更改
python3 scripts/sync_docs.py --dry-run

# 步骤3: 同步文档
python3 scripts/sync_docs.py
```

### 2. 运行前端测试（2步）

```bash
# 步骤1: 运行测试
cd frontend && pnpm test

# 步骤2: 查看覆盖率
cd frontend && pnpm test:coverage
```

### 3. 编写新测试（示例）

```typescript
// MyComponent.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('应该正常渲染', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

## 📋 常用命令

### 文档同步
```bash
# 预览更改
python3 scripts/sync_docs.py --dry-run

# 实际更新
python3 scripts/sync_docs.py
```

### 前端测试
```bash
# 运行所有测试
cd frontend && pnpm test

# 运行测试（单次）
cd frontend && pnpm test --run

# 生成覆盖率
cd frontend && pnpm test:coverage

# 运行特定测试
cd frontend && pnpm test MyComponent
```

### 更新测试覆盖率
```bash
# 更新前端覆盖率到数据源
python3 scripts/update_test_coverage.py --frontend

# 更新后端覆盖率到数据源
python3 scripts/update_test_coverage.py --backend
```

## 📁 重要文件

- `docs/PROJECT_STATUS.json` - **唯一数据源**（只更新这个文件）
- `scripts/sync_docs.py` - 文档同步脚本
- `scripts/update_test_coverage.py` - 覆盖率更新脚本

## ⚠️ 注意事项

1. **只更新数据源**: 不要直接编辑自动同步的文档
2. **先预览**: 使用 `--dry-run` 预览更改
3. **定期同步**: 完成功能后及时更新

## 📚 详细文档

- [文档同步机制说明](20-文档同步机制说明.md)
- [前端测试开发指南](21-前端测试开发指南.md)
- [实施总结](22-实施总结-文档同步和测试开发.md)

