# CozyChat 文档中心

## 📁 文档结构

```
docs/
├── core/              # 核心文档（架构、设计、规范）
├── optimization/      # 优化相关文档
├── testing/           # 测试相关文档
├── features/          # 功能实施报告
├── voice/             # 语音功能文档
├── memory/            # 记忆系统文档
├── guides/            # 使用指南
├── reports/           # 分析报告
├── setup/             # 配置和安装（已存在）
├── troubleshooting/   # 故障排查（已存在）
└── architecture/      # 架构设计（已存在）
```

## 📊 文档统计

| 目录 | 文件数 | 说明 |
|------|--------|------|
| `core/` | 13 | 核心架构、设计、规范文档 |
| `optimization/` | 26 | 性能优化相关文档 |
| `testing/` | 12 | 测试相关文档 |
| `features/` | 12 | 功能实施报告 |
| `voice/` | 13 | 语音功能文档 |
| `memory/` | 7 | 记忆系统文档 |
| `guides/` | 15 | 使用指南和教程 |
| `reports/` | 12 | 分析报告 |
| `setup/` | 11 | 配置和安装文档 |
| `troubleshooting/` | 11 | 故障排查文档 |
| `architecture/` | 8 | 架构设计文档 |

**总计**: ~140个文档

## 📚 快速导航

### 🎯 核心文档（必读）
- [项目概述](core/01-项目概述.md) - 项目整体介绍
- [实施路线图](core/00-实施路线图.md) - 项目规划
- [后端架构设计](core/02-后端架构设计.md) - 后端架构详解
- [前端架构设计](core/03-前端架构设计.md) - 前端架构详解
- [API接口设计](core/04-API接口设计.md) - API规范
- [数据库设计](core/05-数据库设计.md) - 数据库结构
- [开发规范](core/06-开发规范.md) - 编码规范
- [前端开发规范](core/17-前端开发规范.md) - 前端编码规范
- [测试规范](core/07-测试规范.md) - 测试标准
- [开发流程管控](core/08-开发流程管控.md) - 开发流程

### 📖 使用指南
- [Sentry集成指南](guides/72-Sentry集成指南.md) - 错误监控配置
- [ChatUI实施指南](guides/14-ChatUI实施指南.md) - ChatUI组件使用
- [User-Prompt使用指南](guides/60-User-Prompt使用指南.md) - 提示词管理
- [Qdrant快速开始](memory/Qdrant快速开始指南.md) - 向量数据库

### ⚡ 优化文档
- [优化项目总结](optimization/73-优化项目总结.md) - 完整优化总结
- [N+1查询优化](optimization/N+1查询优化说明.md) - 数据库优化
- [缓存策略优化](optimization/35-缓存策略优化总结.md) - 缓存优化
- [前端渲染性能优化](optimization/36-前端渲染性能优化总结.md) - 前端性能

### 🧪 测试文档
- [前端测试修复总结](testing/71-技术债测试修复总结.md) - 测试修复记录
- [测试覆盖率提升总结](testing/28-测试覆盖率提升总结.md) - 覆盖率提升
- [前端测试开发指南](testing/21-前端测试开发指南.md) - 测试开发指南

### 🎤 语音功能
- [腾讯语音SDK接入方案](voice/腾讯语音SDK接入方案.md) - SDK接入
- [语音通话功能设计](voice/语音通话功能设计.md) - 功能设计
- [腾讯语音引擎集成指南](voice/腾讯语音引擎集成指南.md) - 集成指南

### 🧠 记忆系统
- [记忆系统优化方案](memory/50-记忆系统优化方案.md) - 优化方案
- [记忆机制优化实施](memory/54-记忆机制优化实施完成报告.md) - 实施报告
- [Qdrant记忆引擎实施总结](memory/Qdrant记忆引擎实施总结.md) - Qdrant集成

### 📦 功能实施
- [功能模块完成度报告](features/09-功能模块完成度报告.md) - 完成度统计
- [阶段3记忆系统优化](features/42-阶段3记忆系统优化实施报告.md) - 阶段3报告
- [Agent抽象和MCP增强](features/57-Agent抽象和MCP增强实施方案.md) - Agent方案

### 📊 分析报告
- [项目全面分析报告](reports/27-项目全面分析报告.md) - 全面分析
- [项目代码实现分析报告](reports/62-项目代码实现分析报告.md) - 代码分析
- [启动性能优化分析](reports/58-启动性能优化分析报告.md) - 性能分析

## 🔍 文档查找

**按主题查找**：
- 架构设计 → `core/` 或 `architecture/`
- 功能实施 → `features/`
- 性能优化 → `optimization/`
- 测试相关 → `testing/`
- 语音功能 → `voice/`
- 记忆系统 → `memory/`
- 使用指南 → `guides/`
- 问题排查 → `troubleshooting/`

**按阶段查找**：
- Phase 1-2 → `features/phase1-2-*.md`
- Phase 3-4 → `features/phase3-4-*.md`
- 优化项目 → `optimization/73-优化项目总结.md`

## 📝 文档维护

- 新增文档请按分类放入对应目录
- 文档命名规范：`序号-文档标题.md`
- 核心文档保持编号（00-08）
- 其他文档按时间或功能分类

---

**最后更新**: 2025-11-20
