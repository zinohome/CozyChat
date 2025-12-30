# CozyChat Frontend

CozyChat 前端应用，基于 React + TypeScript 构建的现代化 AI 对话界面。

## 🛠 技术栈

- **React 18+** - 函数组件 + Hooks
- **TypeScript 5+** - 严格类型检查
- **Vite** - 快速构建工具
- **Ant Design** - UI组件库
- **@chatui/core** - 聊天专用组件
- **Zustand** - 轻量级状态管理
- **React Query** - 服务端状态管理
- **React Router** - 路由管理

## 📁 项目结构

```
frontend/src/
├── components/       # 通用组件
│   ├── ui/          # UI基础组件
│   ├── layout/      # 布局组件
│   └── chat/        # 聊天组件
├── features/        # 功能模块
│   ├── auth/        # 认证模块
│   ├── chat/        # 聊天模块
│   └── settings/    # 设置模块
├── hooks/           # 自定义Hooks
├── services/        # API服务
├── store/           # Zustand状态管理
├── types/           # TypeScript类型
├── utils/           # 工具函数
└── App.tsx          # 应用入口
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 使用pnpm（推荐）
pnpm install

# 或使用npm
npm install
```

### 2. 配置环境变量

```bash
# 创建.env文件
cp .env.example .env

# 配置API地址
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
pnpm dev
# 或
npm run dev
```

访问 http://localhost:5173

## 🧪 测试

```bash
# 运行测试
pnpm test

# 生成覆盖率报告
pnpm test:coverage
```

## 🏗️ 构建

```bash
# 生产构建
pnpm build

# 预览构建结果
pnpm preview
```

## 📚 文档

- [前端架构设计](../docs/03-前端架构设计.md)
- [前端开发规范](../docs/17-前端开发规范.md)
- [ChatUI实施指南](../docs/14-ChatUI实施指南.md)

## 🤝 贡献

请参考根目录的 [开发规范](../docs/06-开发规范.md)

---

**CozyChat Frontend** - 现代化AI对话平台前端应用

