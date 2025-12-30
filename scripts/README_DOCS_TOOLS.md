# 文档管理工具使用指南

## 概述

为了解决文档时效性和维护问题，我们开发了一套自动化文档管理工具。

## 核心问题和解决方案

### 问题1: 文档看不出最后更新时间

**解决方案**: 文档元数据规范

每个文档开头添加YAML front matter：

```yaml
---
title: 文档标题
version: 1.0.0
created: 2024-11-15
last_updated: 2024-12-22
status: active  # active | outdated | deprecated | draft | archived
author: 张军
reviewers: []
related_code:
  - backend/app/xxx.py
tags: [标签1, 标签2]
---
```

### 问题2: 项目更新后，旧文档没有同步更新

**解决方案**: 自动化检查机制

1. **定期扫描**: 自动发现超过30天未更新的文档
2. **Pre-commit检查**: 提交时自动验证文档元数据
3. **文档索引**: 自动生成文档索引，清晰展示文档状态

## 工具集

### 1. 文档管理器 (`docs_manager.py`)

#### 功能

- 扫描所有文档，提取元数据
- 生成文档索引 (`docs/INDEX.md`)
- 检查过期文档（超过30天未更新）
- 生成详细报告 (`docs/DOCS_REPORT.json`)

#### 使用方法

```bash
# 1. 扫描文档
python3 scripts/docs_manager.py scan

# 2. 生成索引（推荐每天运行）
python3 scripts/docs_manager.py index

# 3. 检查过期文档（推荐每周运行）
python3 scripts/docs_manager.py check

# 4. 生成详细报告
python3 scripts/docs_manager.py report
```

#### 输出示例

**扫描文档**:
```
🔍 扫描文档目录...
✅ 找到 269 个文档
```

**检查过期文档**:
```
🔍 检查过期文档...

⚠️  发现 167 个过期文档（超过30天未更新）:

  - 前端架构设计
    路径: architecture/03-前端架构设计.md
    最后更新: 45天前
    关联代码: frontend/src/
```

**生成索引**:
- 生成 `docs/INDEX.md`
- 按分类组织所有文档
- 显示文档状态、版本、最后更新时间
- 标记过期文档（⏰ 符号）

### 2. 元数据检查器 (`check_docs_metadata.py`)

#### 功能

- 检查文档是否包含必要的元数据
- 验证元数据格式（日期、版本号、状态等）
- 可集成到Git pre-commit hook

#### 使用方法

```bash
# 手动检查单个文件
python3 scripts/check_docs_metadata.py docs/my-doc.md

# 手动检查多个文件
python3 scripts/check_docs_metadata.py docs/file1.md docs/file2.md

# 集成到pre-commit（自动检查）
# 见下方"Git集成"部分
```

#### 输出示例

```
🔍 检查 2 个文档的元数据...

✅ docs/guides/文档管理指南.md
❌ docs/old-doc.md
   - 缺少YAML元数据区块（---开头和结尾）
   - 缺少必需字段: title
   - 缺少必需字段: version

⚠️  发现文档元数据问题！

💡 修复建议:
   1. 参考 docs/.template.md 添加元数据
   2. 确保包含所有必需字段: title, version, last_updated, status
```

### 3. 文档模板 (`.template.md`)

#### 功能

- 提供标准的文档结构
- 包含所有必需的元数据字段
- 作为创建新文档的起点

#### 使用方法

```bash
# 复制模板创建新文档
cp docs/.template.md docs/category/新文档.md

# 编辑新文档，填写元数据和内容
```

## 快速开始

### 第一次使用

1. **查看现有文档状态**

```bash
cd /path/to/CozyChat

# 生成文档索引
python3 scripts/docs_manager.py index

# 查看索引
open docs/INDEX.md  # macOS
# 或
cat docs/INDEX.md   # Linux
```

2. **检查过期文档**

```bash
python3 scripts/docs_manager.py check
```

3. **更新过期文档**

对于每个过期文档：
- 阅读文档内容
- 验证是否准确
- 更新过时信息
- 更新 `last_updated` 字段
- 如有重大变更，更新 `version` 和变更历史

### 创建新文档

1. **复制模板**

```bash
cp docs/.template.md docs/guides/我的新文档.md
```

2. **填写元数据**

```yaml
---
title: 我的新文档
version: 1.0.0
created: 2024-12-22
last_updated: 2024-12-22
status: draft
author: 张军
reviewers: []
related_code:
  - backend/app/my_module/
tags: [新功能, 后端]
---
```

3. **编写内容**

4. **完成后更新状态**

```yaml
status: active  # 从draft改为active
```

### 更新现有文档

1. **小修改（不更新版本号）**

- 修改内容
- 更新 `last_updated: 2024-12-22`
- 在变更历史中简要记录

2. **大修改（更新版本号）**

- 修改内容
- 更新 `version: 1.1.0`（次版本号+1）
- 更新 `last_updated: 2024-12-22`
- 在变更历史中详细记录

## Git集成

### Pre-commit Hook

1. **安装pre-commit**

```bash
pip install pre-commit
```

2. **配置 `.pre-commit-config.yaml`**

```yaml
repos:
  - repo: local
    hooks:
      - id: check-docs-metadata
        name: 检查文档元数据
        entry: python3 scripts/check_docs_metadata.py
        language: system
        files: \.md$
        pass_filenames: true
```

3. **安装hook**

```bash
pre-commit install
```

4. **提交时自动检查**

```bash
git add docs/my-doc.md
git commit -m "docs: 更新文档"

# 自动运行元数据检查
检查文档元数据...................................................✅
```

## 定期维护

### 每天

```bash
# 生成最新索引（可设置cron job）
python3 scripts/docs_manager.py index
```

### 每周

```bash
# 检查过期文档
python3 scripts/docs_manager.py check

# 更新至少1-2个过期文档
```

### 每月

```bash
# 完整审查所有核心文档
python3 scripts/docs_manager.py report

# 根据报告更新过期文档
# 清理临时文档
# 归档废弃文档
```

## 文档状态说明

| 状态 | 标记 | 含义 | 何时使用 |
|------|------|------|----------|
| `active` | ✅ | 活跃 | 文档与代码完全同步，可放心使用 |
| `outdated` | ⚠️ | 过时 | 部分内容过时，需要更新 |
| `deprecated` | ❌ | 废弃 | 已被新文档替代，不应再使用 |
| `draft` | 🚧 | 草稿 | 文档正在编写中，内容不完整 |
| `archived` | 📦 | 归档 | 历史文档，仅供参考 |

## 最佳实践

### 1. 代码变更时同步更新文档

```markdown
修改代码的检查清单:
[ ] 修改代码
[ ] 运行测试
[ ] 更新相关文档:
    [ ] 更新文档内容
    [ ] 更新 last_updated 字段
    [ ] 更新版本号（如需要）
    [ ] 在变更历史中记录
[ ] 提交（代码 + 文档）
```

### 2. 提交PR时的文档检查

```markdown
PR检查清单:
[ ] 所有相关文档已更新
[ ] 文档元数据完整
[ ] 变更历史已记录
[ ] 状态标记正确
[ ] Pre-commit检查通过
```

### 3. 处理过期文档

**临时方案（如果没时间立即更新）**:

1. 更新状态为 `outdated`
2. 添加警告提示
3. 创建TODO issue

**长期方案**:

1. 定期审查和更新
2. 设置提醒（每周/每月）
3. 分配责任人

### 4. 文档生命周期

```
创建 (draft)
    ↓
完成 (active)
    ↓
代码变更 → 更新文档 (active)
    ↓
内容过时 (outdated)
    ↓
重写或废弃 (deprecated)
    ↓
归档 (archived)
```

## 常见问题

### Q1: 如何快速查找文档？

**方法1**: 查看文档索引
```bash
open docs/INDEX.md
```

**方法2**: 使用标签搜索
```bash
grep -r "tags:.*功能名" docs/
```

**方法3**: 使用代码关联
```bash
grep -r "related_code:.*文件路径" docs/
```

### Q2: 文档过期了但没时间更新？

临时方案：
1. 更新状态为 `outdated`
2. 添加警告提示
3. 创建TODO issue

### Q3: 如何处理临时文档？

建议：
1. 临时笔记放在 `docs/temp/`
2. 不需要完整元数据
3. 定期清理（每月）

### Q4: 文档太多，如何维护？

策略：
1. **优先级分类**:
   - 核心文档（架构、API）: 必须保持最新
   - 功能文档: 重要功能需更新
   - 参考文档: 可容忍一定滞后

2. **自动化提醒**:
   ```bash
   # 每周运行
   python3 scripts/docs_manager.py check
   ```

3. **团队协作**:
   - 谁改代码谁更新文档
   - Code Review时检查文档

## 工具输出文件

| 文件 | 说明 | 更新频率 |
|------|------|----------|
| `docs/INDEX.md` | 文档索引，按分类列出所有文档 | 每天自动生成 |
| `docs/DOCS_REPORT.json` | 详细报告，包含所有元数据和统计 | 按需生成 |
| `docs/.template.md` | 文档模板，创建新文档时使用 | 手动维护 |

## 相关文档

- [文档管理指南](../docs/guides/文档管理指南.md) - 完整详细的使用指南
- [开发规范](../docs/core/06-开发规范.md) - 项目开发规范（包含文档规范）
- [文档模板](../docs/.template.md) - 创建新文档的模板

## 贡献

如发现工具Bug或有改进建议，请：
1. 创建Issue描述问题或建议
2. 提交PR修复或改进工具
3. 更新本文档

---

**维护者**: 张军  
**创建时间**: 2024-12-22  
**最后更新**: 2024-12-22

