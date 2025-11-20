# Zustand、React Query 和数据库之间的关系分析

## 一、三者定位

### 1.1 数据库（PostgreSQL）
**角色**：**唯一真实数据源（Single Source of Truth）**
- 存储所有会话和消息的持久化数据
- 数据不会因为页面刷新而丢失
- 跨设备、跨会话的数据存储
- 后端通过 SQLAlchemy ORM 操作数据库

**存储内容**：
- `sessions` 表：会话信息（id, title, message_count, created_at等）
- `messages` 表：消息内容（id, session_id, role, content, created_at等）

### 1.2 React Query（@tanstack/react-query）
**角色**：**服务端状态缓存层（Server State Cache）**
- 缓存从后端 API 获取的数据
- 管理数据获取、缓存、同步、失效
- 自动处理加载状态、错误状态
- 提供乐观更新、自动重试等功能

**存储内容**：
- `['sessions']`：会话列表缓存
- `['chat', 'messages', sessionId]`：每个会话的消息缓存
- `['user', 'preferences']`：用户偏好缓存

**特点**：
- **临时存储**：页面刷新后缓存清空（除非配置了持久化）
- **按需加载**：只在需要时从后端获取数据
- **自动同步**：可以配置自动刷新、失效策略

### 1.3 Zustand（状态管理）
**角色**：**客户端状态管理（Client State）**
- 管理 UI 状态、用户交互状态
- 可以持久化到 localStorage
- 跨组件共享状态
- 轻量级，适合简单的全局状态

**存储内容**（当前实现）：
- `currentSessionId`：当前选中的会话ID
- `messages`：所有会话的消息（⚠️ 设计问题）
- `isLoading`：加载状态
- `error`：错误信息

**特点**：
- **客户端状态**：不直接与数据库交互
- **可以持久化**：通过 `persist` middleware 保存到 localStorage
- **快速访问**：不需要网络请求，直接读取内存

## 二、数据流向

### 2.1 读取数据流程

```
用户操作
  ↓
React 组件
  ↓
React Query Hook (useQuery)
  ↓
API 服务 (axios)
  ↓
后端 API (FastAPI)
  ↓
数据库 (PostgreSQL)
  ↓
返回数据
  ↓
React Query 缓存
  ↓
React 组件渲染
```

**示例**：加载会话列表
```typescript
// 1. 组件中使用 React Query Hook
const { data: sessions } = useQuery({
  queryKey: ['sessions'],
  queryFn: () => sessionApi.getSessions(),  // 2. 调用 API 服务
});

// 3. API 服务发送 HTTP 请求
// sessionApi.getSessions() → GET /v1/sessions

// 4. 后端查询数据库
// db.query(Session).filter(user_id=current_user.id)

// 5. 返回数据到前端
// React Query 自动缓存到内存

// 6. 组件自动重新渲染
```

### 2.2 写入数据流程

```
用户操作（发送消息）
  ↓
React 组件
  ↓
Zustand Store (addMessage) ← 立即更新 UI（乐观更新）
  ↓
React Query Mutation (sendStreamMessage)
  ↓
API 服务 (axios)
  ↓
后端 API (FastAPI)
  ↓
数据库 (PostgreSQL) ← 持久化保存
  ↓
返回响应
  ↓
React Query 更新缓存
  ↓
Zustand Store 同步更新
  ↓
React 组件重新渲染
```

**示例**：发送消息
```typescript
// 1. 用户点击发送
handleSend() {
  // 2. 立即添加到 Zustand Store（乐观更新）
  addMessage(userMessage);
  
  // 3. 发送到后端
  await sendStreamMessage(content);
  
  // 4. 后端保存到数据库
  // db.add(Message(...))
  
  // 5. 流式返回 AI 回复
  // 6. 更新 Zustand Store
  updateMessage(aiMessageId, { content: chunk });
  
  // 7. 完成后更新 React Query 缓存
  queryClient.setQueryData(['chat', 'messages', sessionId], (old) => [...old, newMessage]);
}
```

## 三、三者关系图

```
┌─────────────────────────────────────────────────────────┐
│                    用户界面 (UI)                         │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│              Zustand Store (客户端状态)                  │
│  • currentSessionId                                     │
│  • messages (⚠️ 包含所有会话的消息)                     │
│  • isLoading, error                                     │
│  • 持久化到 localStorage                                 │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│          React Query Cache (服务端状态缓存)               │
│  • ['sessions']: Session[]                               │
│  • ['chat', 'messages', sessionId]: Message[]          │
│  • ['user', 'preferences']: UserPreferences             │
│  • 自动缓存、失效、同步                                  │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│              API 服务层 (HTTP 请求)                      │
│  • sessionApi.getSessions()                             │
│  • chatApi.getHistory(sessionId)                         │
│  • chatApi.send(request)                                 │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│           后端 API (FastAPI)                             │
│  • GET /v1/sessions                                      │
│  • GET /v1/sessions/{session_id}                         │
│  • POST /v1/chat/completions                             │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│           数据库 (PostgreSQL)                            │
│  • sessions 表                                           │
│  • messages 表                                           │
│  • 唯一真实数据源                                         │
└─────────────────────────────────────────────────────────┘
```

## 四、职责划分

### 4.1 数据库
**职责**：
- ✅ 持久化存储所有数据
- ✅ 保证数据一致性（ACID）
- ✅ 跨设备、跨会话的数据共享
- ✅ 数据查询和事务管理

**不负责**：
- ❌ UI 状态管理
- ❌ 客户端缓存
- ❌ 乐观更新

### 4.2 React Query
**职责**：
- ✅ 缓存服务端数据
- ✅ 管理数据获取和同步
- ✅ 处理加载状态、错误状态
- ✅ 自动重试、失效策略
- ✅ 乐观更新支持

**不负责**：
- ❌ 持久化存储（除非配置）
- ❌ UI 状态管理（如模态框开关）
- ❌ 客户端计算状态

### 4.3 Zustand
**职责**：
- ✅ 管理客户端 UI 状态
- ✅ 跨组件共享状态
- ✅ 可以持久化到 localStorage
- ✅ 快速访问（无需网络请求）

**不负责**：
- ❌ 服务端数据缓存（应该用 React Query）
- ❌ 数据同步和失效（应该用 React Query）
- ❌ 网络请求（应该用 React Query）

## 五、当前实现的问题

### 5.1 职责混乱

**问题 1：Zustand 存储了服务端状态**
```typescript
// ❌ 错误：messages 是服务端状态，应该用 React Query
messages: Message[]  // 包含所有会话的消息
```

**应该**：
```typescript
// ✅ 正确：只存储客户端状态
currentSessionId: string | null
// messages 应该从 React Query 获取
```

**问题 2：数据重复存储**
- React Query 缓存：`['chat', 'messages', sessionId]`
- Zustand Store：`messages`（包含所有会话的消息）
- 两者存储相同的数据，但格式不同，容易不一致

**问题 3：数据同步问题**
- 发送消息时，同时更新 Zustand 和 React Query
- 切换会话时，从 React Query 加载，但合并到 Zustand
- 容易导致数据不一致

## 六、正确的架构设计

### 6.1 理想的数据流

```
┌─────────────────────────────────────────────────────────┐
│                   数据库 (PostgreSQL)                   │
│              唯一真实数据源 (Source of Truth)            │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│              React Query (服务端状态)                    │
│  • 缓存从数据库获取的数据                                 │
│  • 管理数据同步和失效                                     │
│  • 自动处理加载和错误状态                                 │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│              Zustand (客户端状态)                        │
│  • currentSessionId                                     │
│  • UI 状态（模态框、侧边栏等）                           │
│  • 用户偏好（如果不需要实时同步）                         │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│                    React 组件                            │
│  • 从 React Query 读取服务端数据                         │
│  • 从 Zustand 读取客户端状态                             │
│  • 通过 React Query Mutations 更新服务端数据             │
└─────────────────────────────────────────────────────────┘
```

### 6.2 正确的使用方式

**服务端数据（会话、消息）**：
```typescript
// ✅ 使用 React Query
const { data: sessions } = useQuery({
  queryKey: ['sessions'],
  queryFn: () => sessionApi.getSessions(),
});

const { data: messages } = useQuery({
  queryKey: ['chat', 'messages', sessionId],
  queryFn: () => chatApi.getHistory(sessionId),
});

// 更新数据
const sendMutation = useMutation({
  mutationFn: (request) => chatApi.send(request),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['chat', 'messages', sessionId] });
  },
});
```

**客户端状态（UI 状态）**：
```typescript
// ✅ 使用 Zustand
const { currentSessionId, setCurrentSessionId } = useChatStore();

// UI 状态
const [isModalOpen, setIsModalOpen] = useState(false);
```

## 七、总结

### 7.1 三者关系

1. **数据库**：唯一真实数据源，持久化存储
2. **React Query**：服务端状态缓存层，管理数据同步
3. **Zustand**：客户端状态管理，管理 UI 状态

### 7.2 数据流向

- **读取**：数据库 → React Query → 组件
- **写入**：组件 → React Query → API → 数据库
- **客户端状态**：组件 ↔ Zustand

### 7.3 当前问题

- ❌ Zustand 存储了服务端状态（messages）
- ❌ 数据重复存储（React Query + Zustand）
- ❌ 数据同步混乱（两者不一致）

### 7.4 改进建议

- ✅ 移除 Zustand 的 `messages` 存储
- ✅ 只保留 `currentSessionId` 在 Zustand
- ✅ 所有服务端数据都通过 React Query 管理
- ✅ Zustand 只管理客户端 UI 状态

