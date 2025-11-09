# Ant Design X 实施指南

> **文档位置**: `docs/12-Ant-Design-X实施指南.md`  
> **创建日期**: 2025-11-07  
> **最后更新**: 2025-11-07

## 📋 目录

1. [快速开始](#快速开始)
2. [项目初始化](#项目初始化)
3. [核心组件使用](#核心组件使用)
4. [与后端API集成](#与后端api集成)
5. [完整示例](#完整示例)
6. [常见问题](#常见问题)

---

## 1. 快速开始

### 1.1 安装依赖

```bash
# 创建前端项目（如果还没有）
cd /Users/zhangjun/CursorProjects/CozyChat
mkdir -p frontend
cd frontend

# 使用 Vite 创建 React + TypeScript 项目
npm create vite@latest . -- --template react-ts

# 安装 Ant Design X 及相关依赖
npm install @ant-design/x @ant-design/icons antd
npm install zustand @tanstack/react-query
npm install axios
npm install tailwindcss postcss autoprefixer
npm install -D @types/node

# 安装开发依赖
npm install -D eslint prettier @typescript-eslint/eslint-plugin @typescript-eslint/parser
```

### 1.2 基础配置

#### TypeScript 配置

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

#### Vite 配置

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
});
```

#### TailwindCSS 配置

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
  corePlugins: {
    preflight: false, // 禁用 Tailwind 的默认样式，避免与 Ant Design 冲突
  },
};
```

---

## 2. 项目初始化

### 2.1 项目结构

```
frontend/
├── src/
│   ├── main.tsx              # 应用入口
│   ├── App.tsx               # 根组件
│   ├── components/           # 组件
│   │   ├── chat/            # 聊天组件
│   │   │   ├── ChatContainer.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── InputArea.tsx
│   │   │   └── SessionList.tsx
│   │   ├── layout/          # 布局组件
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Layout.tsx
│   │   └── common/          # 通用组件
│   │       ├── Loading.tsx
│   │       └── ErrorBoundary.tsx
│   ├── hooks/               # 自定义 Hooks
│   │   ├── useChat.ts
│   │   ├── useSSE.ts
│   │   └── useWebSocket.ts
│   ├── services/            # API 服务
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   ├── chat.ts
│   │   │   ├── session.ts
│   │   │   └── personality.ts
│   │   └── websocket/
│   │       └── websocket.ts
│   ├── store/               # 状态管理
│   │   ├── authStore.ts
│   │   ├── chatStore.ts
│   │   └── uiStore.ts
│   ├── types/               # 类型定义
│   │   ├── api.ts
│   │   ├── chat.ts
│   │   └── user.ts
│   ├── utils/               # 工具函数
│   │   ├── format.ts
│   │   └── storage.ts
│   └── styles/              # 样式文件
│       └── globals.css
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

### 2.2 应用入口

```typescript
// src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './styles/globals.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN}>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </ConfigProvider>
  </React.StrictMode>
);
```

### 2.3 根组件

```typescript
// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { ChatPage } from '@/pages/chat/ChatPage';
import { LoginPage } from '@/pages/auth/LoginPage';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/chat" replace />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="chat/:sessionId" element={<ChatPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

---

## 3. 核心组件使用

### 3.1 API 客户端配置

```typescript
// src/services/api/client.ts
import axios from 'axios';
import { message } from 'antd';

const apiClient = axios.create({
  baseURL: '/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    } else if (error.response?.status >= 500) {
      message.error('服务器错误，请稍后重试');
    } else {
      message.error(error.response?.data?.detail || '请求失败');
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### 3.2 Chat API 服务

```typescript
// src/services/api/chat.ts
import apiClient from './client';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  personality_id?: string;
  session_id?: string;
  stream?: boolean;
  use_memory?: boolean;
}

export interface ChatResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: ChatMessage;
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export const chatApi = {
  // 非流式聊天
  async chat(request: ChatRequest): Promise<ChatResponse> {
    return apiClient.post('/chat/completions', {
      ...request,
      stream: false,
    });
  },

  // 流式聊天（返回 SSE URL）
  async streamChat(request: ChatRequest): Promise<{ url: string }> {
    const response = await apiClient.post('/chat/completions', {
      ...request,
      stream: true,
    });
    // 返回 SSE URL
    return {
      url: `/v1/chat/completions/stream?session_id=${request.session_id}`,
    };
  },
};
```

### 3.3 使用 Ant Design X 核心组件

```typescript
// src/components/chat/ChatContainer.tsx
import { useState } from 'react';
import { useXAgent, useXChat, Sender, Bubble } from '@ant-design/x';
import { chatApi } from '@/services/api/chat';
import { useSSE } from '@/hooks/useSSE';

interface ChatContainerProps {
  sessionId: string;
  personalityId?: string;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  sessionId,
  personalityId = 'default',
}) => {
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const { isStreaming, streamingContent, startStream, stopStream } = useSSE();

  // 使用 useXAgent 管理 AI 代理
  const [agent] = useXAgent({
    request: async (info, callbacks) => {
      const { messages: historyMessages, message } = info;
      const { onSuccess, onUpdate, onError } = callbacks;

      try {
        // 调用后端 API
        const response = await chatApi.streamChat({
          messages: [
            ...historyMessages.map((m) => ({
              role: m.role as 'user' | 'assistant',
              content: m.content,
            })),
            { role: 'user', content: message },
          ],
          session_id: sessionId,
          personality_id: personalityId,
          stream: true,
          use_memory: true,
        });

        // 启动 SSE 流
        await startStream(response.url, {
          onMessage: (data) => {
            const content = data.choices?.[0]?.delta?.content || '';
            onUpdate(content);
          },
          onComplete: () => {
            onSuccess(streamingContent);
          },
          onError: (error) => {
            onError(error);
          },
        });
      } catch (error) {
        onError(error as Error);
      }
    },
  });

  // 使用 useXChat 管理聊天数据流
  const { onRequest, messages: chatMessages } = useXChat({ agent });

  // 转换消息格式
  const items = chatMessages.map(({ message, id }) => ({
    key: id,
    content: message,
    role: id.startsWith('user-') ? 'user' : 'assistant',
  }));

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-auto p-4">
        <Bubble.List items={items} />
        {isStreaming && (
          <Bubble
            content={streamingContent}
            role="assistant"
            loading
          />
        )}
      </div>
      <div className="border-t p-4">
        <Sender
          onSubmit={onRequest}
          onStop={stopStream}
          loading={isStreaming}
          placeholder="输入您的问题..."
        />
      </div>
    </div>
  );
};
```

### 3.4 SSE Hook 实现

```typescript
// src/hooks/useSSE.ts
import { useState, useCallback, useRef } from 'react';

interface SSEOptions {
  onMessage?: (data: any) => void;
  onComplete?: () => void;
  onError?: (error: Error) => void;
}

export const useSSE = () => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const eventSourceRef = useRef<EventSource | null>(null);

  const startStream = useCallback(
    async (url: string, options: SSEOptions = {}) => {
      setIsStreaming(true);
      setStreamingContent('');

      try {
        const eventSource = new EventSource(url);
        eventSourceRef.current = eventSource;

        eventSource.onmessage = (event) => {
          if (event.data === '[DONE]') {
            eventSource.close();
            setIsStreaming(false);
            options.onComplete?.();
            return;
          }

          try {
            const data = JSON.parse(event.data);
            const content = data.choices?.[0]?.delta?.content || '';
            
            setStreamingContent((prev) => {
              const newContent = prev + content;
              options.onMessage?.(data);
              return newContent;
            });
          } catch (error) {
            console.error('Failed to parse SSE data:', error);
          }
        };

        eventSource.onerror = (error) => {
          console.error('SSE error:', error);
          eventSource.close();
          setIsStreaming(false);
          options.onError?.(new Error('SSE connection error'));
        };
      } catch (error) {
        setIsStreaming(false);
        options.onError?.(error as Error);
      }
    },
    []
  );

  const stopStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsStreaming(false);
      setStreamingContent('');
    }
  }, []);

  return {
    isStreaming,
    streamingContent,
    startStream,
    stopStream,
  };
};
```

---

## 4. 与后端 API 集成

### 4.1 后端 API 适配

由于 CozyChat 后端使用 FastAPI，需要确保 API 格式与 Ant Design X 兼容：

```typescript
// src/services/api/chat.ts (扩展)
export const chatApi = {
  // ... 之前的代码

  // 适配 Ant Design X 的流式响应
  async streamChatForX(request: ChatRequest): Promise<EventSource> {
    const token = localStorage.getItem('access_token');
    const url = new URL('/v1/chat/completions', window.location.origin);
    
    // 构建 SSE URL
    url.searchParams.set('session_id', request.session_id || '');
    url.searchParams.set('personality_id', request.personality_id || 'default');
    url.searchParams.set('stream', 'true');

    // 创建 EventSource
    const eventSource = new EventSource(url.toString(), {
      withCredentials: true,
    });

    // 如果需要认证，可以通过自定义 header（但 EventSource 不支持）
    // 建议使用 POST 请求 + SSE，或者通过 URL 参数传递 token

    return eventSource;
  },
};
```

### 4.2 后端 SSE 端点实现

确保后端支持 SSE 流式响应：

```python
# backend/app/api/v1/chat.py (示例)
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

@router.post("/completions/stream")
async def stream_chat_completions(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """流式聊天响应（SSE）"""
    
    async def event_generator():
        async for chunk in orchestrator.stream_chat(
            messages=request.messages,
            personality_id=request.personality_id,
            user_id=current_user.id,
            session_id=request.session_id,
        ):
            yield {
                "event": "message",
                "data": json.dumps({
                    "id": chunk.id,
                    "object": "chat.completion.chunk",
                    "choices": [{
                        "delta": {"content": chunk.content},
                        "index": 0,
                        "finish_reason": chunk.finish_reason
                    }]
                })
            }
        
        yield {
            "event": "message",
            "data": "[DONE]"
        }
    
    return EventSourceResponse(event_generator())
```

---

## 5. 完整示例

### 5.1 完整聊天页面

```typescript
// src/pages/chat/ChatPage.tsx
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Layout, Row, Col } from 'antd';
import { ChatContainer } from '@/components/chat/ChatContainer';
import { SessionList } from '@/components/chat/SessionList';
import { PersonalitySelector } from '@/components/personality/PersonalitySelector';
import { useQuery } from '@tanstack/react-query';
import { sessionApi } from '@/services/api/session';

const { Content, Sider } = Layout;

export const ChatPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const [selectedSessionId, setSelectedSessionId] = useState<string>(
    sessionId || ''
  );
  const [personalityId, setPersonalityId] = useState<string>('default');

  // 获取会话列表
  const { data: sessions } = useQuery({
    queryKey: ['sessions'],
    queryFn: sessionApi.getSessions,
  });

  // 创建新会话
  const handleCreateSession = async () => {
    const newSession = await sessionApi.createSession({
      title: '新会话',
      personality_id: personalityId,
    });
    setSelectedSessionId(newSession.id);
  };

  return (
    <Layout className="h-screen">
      <Sider width={250} className="border-r">
        <SessionList
          sessions={sessions || []}
          selectedSessionId={selectedSessionId}
          onSelect={setSelectedSessionId}
          onCreate={handleCreateSession}
        />
      </Sider>
      <Layout>
        <Content className="flex flex-col">
          <div className="border-b p-4">
            <PersonalitySelector
              value={personalityId}
              onChange={setPersonalityId}
            />
          </div>
          <div className="flex-1 overflow-hidden">
            {selectedSessionId ? (
              <ChatContainer
                sessionId={selectedSessionId}
                personalityId={personalityId}
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <p>请选择一个会话或创建新会话</p>
              </div>
            )}
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};
```

### 5.2 会话列表组件

```typescript
// src/components/chat/SessionList.tsx
import { List, Button, Card, Space } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { sessionApi } from '@/services/api/session';

interface SessionListProps {
  sessions: Array<{ id: string; title: string; last_message?: string }>;
  selectedSessionId?: string;
  onSelect: (sessionId: string) => void;
  onCreate: () => void;
}

export const SessionList: React.FC<SessionListProps> = ({
  sessions,
  selectedSessionId,
  onSelect,
  onCreate,
}) => {
  const queryClient = useQueryClient();

  const deleteSession = useMutation({
    mutationFn: sessionApi.deleteSession,
    onSuccess: () => {
      queryClient.invalidateQueries(['sessions']);
    },
  });

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b">
        <Button
          type="primary"
          icon={<PlusOutlined />}
          block
          onClick={onCreate}
        >
          新建会话
        </Button>
      </div>
      <div className="flex-1 overflow-auto">
        <List
          dataSource={sessions}
          renderItem={(session) => (
            <List.Item
              className={selectedSessionId === session.id ? 'bg-blue-50' : ''}
              onClick={() => onSelect(session.id)}
            >
              <Card
                hoverable
                className="w-full"
                title={session.title}
                extra={
                  <Button
                    type="text"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession.mutate(session.id);
                    }}
                  />
                }
              >
                <p className="text-sm text-gray-500 truncate">
                  {session.last_message || '暂无消息'}
                </p>
              </Card>
            </List.Item>
          )}
        />
      </div>
    </div>
  );
};
```

---

## 6. 常见问题

### 6.1 SSE 连接问题

**问题**: EventSource 不支持自定义 Header，无法传递 JWT Token

**解决方案**:
1. 通过 URL 参数传递 token（不推荐，安全性低）
2. 使用 POST 请求 + SSE（推荐）
3. 使用 WebSocket 替代 SSE

```typescript
// 方案2：使用 POST + SSE
const response = await fetch('/v1/chat/completions/stream', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(request),
});

const reader = response.body?.getReader();
// 处理流式数据
```

### 6.2 样式冲突

**问题**: TailwindCSS 与 Ant Design 样式冲突

**解决方案**:
```javascript
// tailwind.config.js
export default {
  corePlugins: {
    preflight: false, // 禁用 Tailwind 的默认样式
  },
};
```

### 6.3 移动端适配

**问题**: Ant Design X 在移动端显示不佳

**解决方案**:
1. 使用 Ant Design Mobile 组件
2. 自定义响应式样式
3. 使用 CSS Media Queries

```typescript
// 响应式布局示例
import { useMediaQuery } from '@/hooks/useMediaQuery';

export const ChatContainer: React.FC = () => {
  const isMobile = useMediaQuery('(max-width: 768px)');
  
  return (
    <div className={isMobile ? 'mobile-layout' : 'desktop-layout'}>
      {/* ... */}
    </div>
  );
};
```

### 6.4 性能优化

**问题**: 长消息列表导致性能问题

**解决方案**:
1. 使用虚拟列表
2. 实现消息分页
3. 使用 React.memo 优化组件

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

export const MessageList: React.FC<{ messages: Message[] }> = ({ messages }) => {
  const parentRef = useRef<HTMLDivElement>(null);
  
  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100,
    overscan: 5,
  });
  
  return (
    <div ref={parentRef} className="h-full overflow-auto">
      {/* 虚拟列表渲染 */}
    </div>
  );
};
```

---

## 7. 下一步

### 7.1 实施步骤

1. **第一阶段**（1-2周）：基础聊天功能
   - ✅ 安装依赖和配置
   - ✅ 实现 ChatContainer 组件
   - ✅ 集成后端 API
   - ✅ 实现 SSE 流式响应

2. **第二阶段**（1周）：会话管理
   - ✅ 实现 SessionList 组件
   - ✅ 实现会话创建/删除
   - ✅ 实现会话切换

3. **第三阶段**（2-3周）：语音功能
   - ⚠️ 自定义语音录制组件
   - ⚠️ 自定义语音播放组件
   - ⚠️ 自定义 RealTime 语音组件

4. **第四阶段**（1-2周）：优化扩展
   - ⚠️ 性能优化
   - ⚠️ 移动端适配
   - ⚠️ 主题切换

### 7.2 参考资源

- [Ant Design X 官方文档](https://x.ant.design)
- [Ant Design 官方文档](https://ant.design)
- [TanStack Query 文档](https://tanstack.com/query)
- [Zustand 文档](https://zustand-demo.pmnd.rs)

---

**文档版本**: v1.0  
**最后更新**: 2025-11-07  
**维护者**: CozyChat Team

