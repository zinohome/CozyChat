# ChatUI 实施指南

> **文档位置**: `docs/14-ChatUI实施指南.md`  
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

# 安装 ChatUI 及相关依赖
npm install @chatui/core @chatui/react
npm install antd @ant-design/icons
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

---

## 2. 项目初始化

### 2.1 应用入口

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
  id?: string;
  timestamp?: number;
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

  // 流式聊天（SSE）
  async streamChat(request: ChatRequest): Promise<EventSource> {
    const token = localStorage.getItem('access_token');
    const url = new URL('/v1/chat/completions/stream', window.location.origin);
    
    url.searchParams.set('session_id', request.session_id || '');
    url.searchParams.set('personality_id', request.personality_id || 'default');
    url.searchParams.set('stream', 'true');

    // 注意：EventSource 不支持自定义 Header，需要通过 URL 参数传递 token
    // 或者使用 POST 请求 + SSE
    url.searchParams.set('token', token || '');

    return new EventSource(url.toString());
  },
};
```

### 3.3 使用 ChatUI 核心组件

```typescript
// src/components/chat/ChatContainer.tsx
import { useState, useEffect, useRef } from 'react';
import { Chat, Message, Input } from '@chatui/core';
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
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const { isStreaming, streamingContent, startStream, stopStream } = useSSE();
  const chatRef = useRef<any>(null);

  // 发送消息
  const handleSend = async (type: string, val: string) => {
    if (type === 'text' && val.trim()) {
      // 添加用户消息
      const userMessage: Message = {
        type: 'text',
        content: { text: val },
        user: { id: 'user' },
        createdAt: Date.now(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // 开始流式响应
      try {
        const eventSource = await chatApi.streamChat({
          messages: [
            ...messages.map((m) => ({
              role: m.user?.id === 'user' ? 'user' : 'assistant',
              content: m.content?.text || '',
            })),
            { role: 'user', content: val },
          ],
          session_id: sessionId,
          personality_id: personalityId,
          stream: true,
          use_memory: true,
        });

        // 处理 SSE 流
        let assistantContent = '';
        const assistantMessage: Message = {
          type: 'text',
          content: { text: '' },
          user: { id: 'assistant' },
          createdAt: Date.now(),
        };
        setMessages((prev) => [...prev, assistantMessage]);

        eventSource.onmessage = (event) => {
          if (event.data === '[DONE]') {
            eventSource.close();
            return;
          }

          try {
            const data = JSON.parse(event.data);
            const content = data.choices?.[0]?.delta?.content || '';
            assistantContent += content;

            // 更新消息
            setMessages((prev) => {
              const updated = [...prev];
              const lastMessage = updated[updated.length - 1];
              if (lastMessage.user?.id === 'assistant') {
                lastMessage.content = { text: assistantContent };
              }
              return updated;
            });
          } catch (error) {
            console.error('Failed to parse SSE data:', error);
          }
        };

        eventSource.onerror = (error) => {
          console.error('SSE error:', error);
          eventSource.close();
        };
      } catch (error) {
        console.error('Failed to send message:', error);
      }
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-auto">
        <Chat
          ref={chatRef}
          messages={messages}
          onSend={handleSend}
          placeholder="输入您的问题..."
          toolbar={[
            { type: 'voice', icon: 'mic' },
            { type: 'image', icon: 'image' },
            { type: 'file', icon: 'file' },
          ]}
        />
      </div>
    </div>
  );
};
```

---

## 4. 与后端 API 集成

### 4.1 后端 SSE 端点实现

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
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Layout } from 'antd';
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

---

## 6. Drawer 实现

### 6.1 使用 Ant Design Drawer

ChatUI 本身不提供 Drawer 组件，但可以使用 Ant Design 的 `Drawer` 组件来实现侧边弹出功能。

```typescript
// src/components/user/HealthRecordDrawer.tsx
import { Drawer, Tabs } from 'antd';
import { UserOutlined } from '@ant-design/icons';

export const HealthRecordDrawer: React.FC<{
  visible: boolean;
  onClose: () => void;
}> = ({ visible, onClose }) => {
  return (
    <Drawer
      title={
        <Space>
          <UserOutlined />
          健康档案
        </Space>
      }
      placement="right"
      width={600}
      open={visible}
      onClose={onClose}
    >
      <Tabs items={tabItems} />
    </Drawer>
  );
};
```

详细实现方案请参考：`docs/15-ChatUI-Drawer实现方案.md`

---

## 7. 常见问题

### 7.1 SSE 连接问题

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

### 7.2 样式冲突

**问题**: ChatUI 与 Ant Design 样式冲突

**解决方案**:
1. 使用 CSS Modules 隔离样式
2. 使用 TailwindCSS 的 `@layer` 功能
3. 调整样式优先级
4. 禁用 Tailwind preflight

```javascript
// tailwind.config.js
module.exports = {
  corePlugins: {
    preflight: false, // 禁用 Tailwind 的默认样式
  },
};
```

### 7.3 Drawer 实现

**问题**: ChatUI 不提供 Drawer 组件

**解决方案**:
使用 Ant Design 的 `Drawer` 组件，详细实现请参考：`docs/15-ChatUI-Drawer实现方案.md`

---

## 8. 下一步

### 8.1 实施步骤

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

### 8.2 参考资源

- [ChatUI 官方文档](https://chatui.io)
- [ChatUI GitHub](https://github.com/alibaba/ChatUI)
- [Ant Design 官方文档](https://ant.design)
- [TanStack Query 文档](https://tanstack.com/query)
- [Zustand 文档](https://zustand-demo.pmnd.rs)

---

**文档版本**: v1.0  
**最后更新**: 2025-11-07  
**维护者**: CozyChat Team

