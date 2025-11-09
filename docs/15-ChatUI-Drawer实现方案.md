# ChatUI + Ant Design Drawer 实现方案

> **文档位置**: `docs/15-ChatUI-Drawer实现方案.md`  
> **创建日期**: 2025-11-07  
> **最后更新**: 2025-11-07

## 📋 目录

1. [问题分析](#问题分析)
2. [解决方案](#解决方案)
3. [实现示例](#实现示例)
4. [移动端适配](#移动端适配)
5. [最佳实践](#最佳实践)

---

## 1. 问题分析

### 1.1 ChatUI 的限制

**ChatUI 本身不提供 Drawer 组件**，但项目需要以下 Drawer 功能：

1. **健康档案抽屉** - 从右侧弹出，显示用户健康档案
2. **偏好设置抽屉** - 从右侧弹出，显示用户偏好设置
3. **移动端会话列表抽屉** - 从左侧弹出，显示会话列表
4. **其他功能抽屉** - 用户资料、工具面板等

### 1.2 解决方案

**推荐方案：使用 Ant Design Drawer**

由于推荐方案是 **ChatUI + Ant Design**，可以使用 Ant Design 的 `Drawer` 组件来实现侧边弹出功能。

---

## 2. 解决方案

### 2.1 技术栈组合

```yaml
核心聊天:
  - @chatui/core: 聊天核心功能
  - @chatui/react: React 组件（可选）

通用组件:
  - antd: 通用组件（包括 Drawer）
  - @ant-design/icons: 图标

样式方案:
  - @chatui/core: 组件样式（聊天组件）
  - antd: 组件样式（通用组件，包括 Drawer）
  - tailwindcss: 原子化CSS（自定义样式，可选）
```

### 2.2 实现策略

1. **聊天功能** - 使用 ChatUI
   - `Chat` - 聊天容器
   - `Message` - 消息组件
   - `Input` - 输入组件

2. **Drawer 功能** - 使用 Ant Design
   - `Drawer` - 侧边抽屉
   - `Tabs` - 标签页（用于抽屉内容组织）
   - `Form` - 表单（用于设置）
   - `List` - 列表（用于数据展示）

3. **布局组件** - 使用 Ant Design
   - `Layout` - 布局容器
   - `Button` - 按钮（触发 Drawer）
   - `Space` - 间距组件

---

## 3. 实现示例

### 3.1 健康档案抽屉

```typescript
// src/components/user/HealthRecordDrawer.tsx
import { useState } from 'react';
import { Drawer, Tabs, Card, Descriptions, Image, Button, Space } from 'antd';
import { UserOutlined, FileTextOutlined, MedicineBoxOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { userApi } from '@/services/api/user';

interface HealthRecordDrawerProps {
  visible: boolean;
  onClose: () => void;
  userId: string;
}

export const HealthRecordDrawer: React.FC<HealthRecordDrawerProps> = ({
  visible,
  onClose,
  userId,
}) => {
  // 获取用户健康档案
  const { data: healthRecord, isLoading } = useQuery({
    queryKey: ['healthRecord', userId],
    queryFn: () => userApi.getHealthRecord(userId),
    enabled: visible && !!userId,
  });

  const tabItems = [
    {
      key: 'profile',
      label: (
        <Space>
          <UserOutlined />
          基本信息
        </Space>
      ),
      children: (
        <Card>
          <Descriptions column={1} bordered>
            <Descriptions.Item label="姓名">
              {healthRecord?.name || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="性别">
              {healthRecord?.gender || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="年龄">
              {healthRecord?.age || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="身高">
              {healthRecord?.height || '-'} cm
            </Descriptions.Item>
            <Descriptions.Item label="体重">
              {healthRecord?.weight || '-'} kg
            </Descriptions.Item>
          </Descriptions>
        </Card>
      ),
    },
    {
      key: 'health_check',
      label: (
        <Space>
          <FileTextOutlined />
          健康自测
        </Space>
      ),
      children: (
        <Card>
          {/* 健康自测内容 */}
          <p>健康自测记录...</p>
        </Card>
      ),
    },
    {
      key: 'medication',
      label: (
        <Space>
          <MedicineBoxOutlined />
          药物记录
        </Space>
      ),
      children: (
        <Card>
          {/* 药物记录内容 */}
          <p>药物记录...</p>
        </Card>
      ),
    },
  ];

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
      maskClosable={false}
      destroyOnClose
    >
      {isLoading ? (
        <div>加载中...</div>
      ) : (
        <Tabs items={tabItems} defaultActiveKey="profile" />
      )}
    </Drawer>
  );
};
```

### 3.2 偏好设置抽屉

```typescript
// src/components/user/PreferenceDrawer.tsx
import { useState } from 'react';
import { Drawer, Tabs, Form, Radio, Switch, Select, Button, Space, message } from 'antd';
import { SettingOutlined, ThemeOutlined, SoundOutlined } from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { userApi } from '@/services/api/user';

interface PreferenceDrawerProps {
  visible: boolean;
  onClose: () => void;
  userId: string;
}

export const PreferenceDrawer: React.FC<PreferenceDrawerProps> = ({
  visible,
  onClose,
  userId,
}) => {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // 获取用户偏好
  const { data: preferences, isLoading } = useQuery({
    queryKey: ['preferences', userId],
    queryFn: () => userApi.getPreferences(userId),
    enabled: visible && !!userId,
    onSuccess: (data) => {
      form.setFieldsValue(data);
    },
  });

  // 更新用户偏好
  const updatePreferences = useMutation({
    mutationFn: (data: any) => userApi.updatePreferences(userId, data),
    onSuccess: () => {
      message.success('偏好设置已保存');
      queryClient.invalidateQueries(['preferences', userId]);
      onClose();
    },
    onError: () => {
      message.error('保存失败，请重试');
    },
  });

  const handleSubmit = () => {
    form.validateFields().then((values) => {
      updatePreferences.mutate(values);
    });
  };

  const tabItems = [
    {
      key: 'theme',
      label: (
        <Space>
          <ThemeOutlined />
          主题设置
        </Space>
      ),
      children: (
        <Form form={form} layout="vertical">
          <Form.Item name="theme" label="主题">
            <Radio.Group>
              <Radio value="light">浅色主题</Radio>
              <Radio value="dark">深色主题</Radio>
              <Radio value="auto">跟随系统</Radio>
            </Radio.Group>
          </Form.Item>
          <Form.Item name="default_personality" label="默认人格">
            <Select placeholder="选择默认人格">
              <Select.Option value="default">默认助手</Select.Option>
              <Select.Option value="health_assistant">健康助手</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'voice',
      label: (
        <Space>
          <SoundOutlined />
          语音设置
        </Space>
      ),
      children: (
        <Form form={form} layout="vertical">
          <Form.Item name="voice_enabled" label="启用语音" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="voice_provider" label="语音提供商">
            <Select>
              <Select.Option value="openai">OpenAI</Select.Option>
              <Select.Option value="tencent">腾讯</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="voice_speed" label="语音速度">
            <Select>
              <Select.Option value="0.8">慢速</Select.Option>
              <Select.Option value="1.0">正常</Select.Option>
              <Select.Option value="1.2">快速</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      ),
    },
  ];

  return (
    <Drawer
      title={
        <Space>
          <SettingOutlined />
          偏好设置
        </Space>
      }
      placement="right"
      width={500}
      open={visible}
      onClose={onClose}
      maskClosable={false}
      destroyOnClose
      extra={
        <Space>
          <Button onClick={onClose}>取消</Button>
          <Button type="primary" onClick={handleSubmit} loading={updatePreferences.isLoading}>
            保存
          </Button>
        </Space>
      }
    >
      {isLoading ? (
        <div>加载中...</div>
      ) : (
        <Tabs items={tabItems} defaultActiveKey="theme" />
      )}
    </Drawer>
  );
};
```

### 3.3 移动端会话列表抽屉

```typescript
// src/components/chat/MobileSessionDrawer.tsx
import { Drawer, List, Button, Input, Space } from 'antd';
import { PlusOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { sessionApi } from '@/services/api/session';
import { useBreakpoint } from '@/hooks/useMediaQuery';

interface MobileSessionDrawerProps {
  visible: boolean;
  onClose: () => void;
  selectedSessionId?: string;
  onSelect: (sessionId: string) => void;
}

export const MobileSessionDrawer: React.FC<MobileSessionDrawerProps> = ({
  visible,
  onClose,
  selectedSessionId,
  onSelect,
}) => {
  const [searchText, setSearchText] = useState('');
  const queryClient = useQueryClient();
  const { isMobile } = useBreakpoint();

  // 获取会话列表
  const { data: sessions } = useQuery({
    queryKey: ['sessions'],
    queryFn: sessionApi.getSessions,
  });

  // 创建新会话
  const createSession = useMutation({
    mutationFn: sessionApi.createSession,
    onSuccess: (newSession) => {
      queryClient.invalidateQueries(['sessions']);
      onSelect(newSession.id);
      onClose();
    },
  });

  // 删除会话
  const deleteSession = useMutation({
    mutationFn: sessionApi.deleteSession,
    onSuccess: () => {
      queryClient.invalidateQueries(['sessions']);
    },
  });

  // 过滤会话
  const filteredSessions = sessions?.filter((session) =>
    session.title.toLowerCase().includes(searchText.toLowerCase())
  );

  return (
    <Drawer
      title="会话列表"
      placement="left"
      width={isMobile ? '80%' : 300}
      open={visible}
      onClose={onClose}
      maskClosable
      bodyStyle={{ padding: 0 }}
    >
      <div className="p-4 border-b">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            block
            onClick={() => createSession.mutate({ title: '新会话' })}
          >
            新建会话
          </Button>
          <Input
            placeholder="搜索会话..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
        </Space>
      </div>
      <List
        dataSource={filteredSessions}
        renderItem={(session) => (
          <List.Item
            className={selectedSessionId === session.id ? 'bg-blue-50' : ''}
            onClick={() => {
              onSelect(session.id);
              onClose();
            }}
            actions={[
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  deleteSession.mutate(session.id);
                }}
              />,
            ]}
          >
            <List.Item.Meta
              title={session.title}
              description={session.last_message || '暂无消息'}
            />
          </List.Item>
        )}
      />
    </Drawer>
  );
};
```

### 3.4 在聊天页面中集成 Drawer

```typescript
// src/pages/chat/ChatPage.tsx
import { useState } from 'react';
import { Layout, Button, Space } from 'antd';
import { UserOutlined, SettingOutlined, MenuOutlined } from '@ant-design/icons';
import { Chat } from '@chatui/core';
import { HealthRecordDrawer } from '@/components/user/HealthRecordDrawer';
import { PreferenceDrawer } from '@/components/user/PreferenceDrawer';
import { MobileSessionDrawer } from '@/components/chat/MobileSessionDrawer';
import { useBreakpoint } from '@/hooks/useMediaQuery';
import { useAuthStore } from '@/store/authStore';

const { Content, Sider } = Layout;

export const ChatPage: React.FC = () => {
  const { user } = useAuthStore();
  const { isMobile } = useBreakpoint();
  
  // Drawer 状态
  const [healthRecordVisible, setHealthRecordVisible] = useState(false);
  const [preferenceVisible, setPreferenceVisible] = useState(false);
  const [sessionDrawerVisible, setSessionDrawerVisible] = useState(false);

  return (
    <Layout className="h-screen">
      {/* 桌面端：固定侧边栏 */}
      {!isMobile && (
        <Sider width={250} className="border-r">
          <SessionList />
        </Sider>
      )}

      <Layout>
        {/* 头部工具栏 */}
        <div className="border-b p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isMobile && (
              <Button
                icon={<MenuOutlined />}
                onClick={() => setSessionDrawerVisible(true)}
              />
            )}
            <h2 className="m-0">CozyChat</h2>
          </div>
          
          <Space>
            <Button
              icon={<UserOutlined />}
              onClick={() => setHealthRecordVisible(true)}
            >
              健康档案
            </Button>
            <Button
              icon={<SettingOutlined />}
              onClick={() => setPreferenceVisible(true)}
            >
              偏好设置
            </Button>
          </Space>
        </div>

        {/* 聊天内容区域 */}
        <Content className="flex-1 overflow-hidden">
          <Chat
            messages={messages}
            onSend={handleSend}
            placeholder="输入您的问题..."
            toolbar={[
              { type: 'voice', icon: 'mic' },
              { type: 'image', icon: 'image' },
              { type: 'file', icon: 'file' },
            ]}
          />
        </Content>
      </Layout>

      {/* Drawer 组件 */}
      <HealthRecordDrawer
        visible={healthRecordVisible}
        onClose={() => setHealthRecordVisible(false)}
        userId={user?.id || ''}
      />
      
      <PreferenceDrawer
        visible={preferenceVisible}
        onClose={() => setPreferenceVisible(false)}
        userId={user?.id || ''}
      />
      
      {isMobile && (
        <MobileSessionDrawer
          visible={sessionDrawerVisible}
          onClose={() => setSessionDrawerVisible(false)}
          selectedSessionId={selectedSessionId}
          onSelect={setSelectedSessionId}
        />
      )}
    </Layout>
  );
};
```

### 3.5 在输入区域工具栏中集成 Drawer

```typescript
// src/components/chat/ChatInputArea.tsx
import { useState } from 'react';
import { Input, Button, Space } from 'antd';
import { UserOutlined, SettingOutlined, SendOutlined } from '@ant-design/icons';
import { HealthRecordDrawer } from '@/components/user/HealthRecordDrawer';
import { PreferenceDrawer } from '@/components/user/PreferenceDrawer';
import { useAuthStore } from '@/store/authStore';

interface ChatInputAreaProps {
  onSend: (message: string) => void;
  placeholder?: string;
}

export const ChatInputArea: React.FC<ChatInputAreaProps> = ({
  onSend,
  placeholder = '输入您的问题...',
}) => {
  const [inputValue, setInputValue] = useState('');
  const { user } = useAuthStore();
  
  // Drawer 状态
  const [healthRecordVisible, setHealthRecordVisible] = useState(false);
  const [preferenceVisible, setPreferenceVisible] = useState(false);

  const handleSend = () => {
    if (inputValue.trim()) {
      onSend(inputValue);
      setInputValue('');
    }
  };

  return (
    <>
      <div className="border-t p-4">
        {/* 工具栏 */}
        <div className="mb-2 flex gap-2">
          <Button
            type="text"
            icon={<UserOutlined />}
            onClick={() => setHealthRecordVisible(true)}
          >
            健康档案
          </Button>
          <Button
            type="text"
            icon={<SettingOutlined />}
            onClick={() => setPreferenceVisible(true)}
          >
            偏好设置
          </Button>
        </div>

        {/* 输入区域 */}
        <Space.Compact style={{ width: '100%' }}>
          <Input.TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={placeholder}
            autoSize={{ minRows: 1, maxRows: 4 }}
            onPressEnter={(e) => {
              if (e.shiftKey) {
                return; // Shift+Enter 换行
              }
              e.preventDefault();
              handleSend();
            }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            disabled={!inputValue.trim()}
          >
            发送
          </Button>
        </Space.Compact>
      </div>

      {/* Drawer 组件 */}
      <HealthRecordDrawer
        visible={healthRecordVisible}
        onClose={() => setHealthRecordVisible(false)}
        userId={user?.id || ''}
      />
      
      <PreferenceDrawer
        visible={preferenceVisible}
        onClose={() => setPreferenceVisible(false)}
        userId={user?.id || ''}
      />
    </>
  );
};
```

---

## 4. 移动端适配

### 4.1 响应式 Drawer

```typescript
// src/components/common/ResponsiveDrawer.tsx
import { Drawer, DrawerProps } from 'antd';
import { useBreakpoint } from '@/hooks/useMediaQuery';

interface ResponsiveDrawerProps extends DrawerProps {
  mobileWidth?: string | number;
  desktopWidth?: string | number;
}

export const ResponsiveDrawer: React.FC<ResponsiveDrawerProps> = ({
  mobileWidth = '80%',
  desktopWidth = 500,
  ...props
}) => {
  const { isMobile } = useBreakpoint();

  return (
    <Drawer
      {...props}
      width={isMobile ? mobileWidth : desktopWidth}
    />
  );
};
```

### 4.2 移动端优化

```typescript
// src/components/chat/MobileChatLayout.tsx
import { useState } from 'react';
import { Layout, Button } from 'antd';
import { MenuOutlined } from '@ant-design/icons';
import { Chat } from '@chatui/core';
import { MobileSessionDrawer } from './MobileSessionDrawer';
import { useBreakpoint } from '@/hooks/useMediaQuery';

export const MobileChatLayout: React.FC = () => {
  const { isMobile } = useBreakpoint();
  const [sessionDrawerVisible, setSessionDrawerVisible] = useState(false);

  if (!isMobile) {
    return null; // 桌面端使用其他布局
  }

  return (
    <Layout className="h-screen">
      {/* 移动端头部 */}
      <div className="border-b p-4 flex items-center">
        <Button
          icon={<MenuOutlined />}
          onClick={() => setSessionDrawerVisible(true)}
        />
        <h2 className="m-0 ml-4">CozyChat</h2>
      </div>

      {/* 聊天内容 */}
      <Content className="flex-1 overflow-hidden">
        <Chat messages={messages} onSend={handleSend} />
      </Content>

      {/* 移动端会话抽屉 */}
      <MobileSessionDrawer
        visible={sessionDrawerVisible}
        onClose={() => setSessionDrawerVisible(false)}
        selectedSessionId={selectedSessionId}
        onSelect={setSelectedSessionId}
      />
    </Layout>
  );
};
```

---

## 5. 最佳实践

### 5.1 Drawer 状态管理

```typescript
// src/store/uiStore.ts
import { create } from 'zustand';

interface UIState {
  // Drawer 状态
  healthRecordDrawerVisible: boolean;
  preferenceDrawerVisible: boolean;
  sessionDrawerVisible: boolean;
  
  // Drawer 操作
  openHealthRecordDrawer: () => void;
  closeHealthRecordDrawer: () => void;
  openPreferenceDrawer: () => void;
  closePreferenceDrawer: () => void;
  openSessionDrawer: () => void;
  closeSessionDrawer: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  healthRecordDrawerVisible: false,
  preferenceDrawerVisible: false,
  sessionDrawerVisible: false,
  
  openHealthRecordDrawer: () => set({ healthRecordDrawerVisible: true }),
  closeHealthRecordDrawer: () => set({ healthRecordDrawerVisible: false }),
  openPreferenceDrawer: () => set({ preferenceDrawerVisible: true }),
  closePreferenceDrawer: () => set({ preferenceDrawerVisible: false }),
  openSessionDrawer: () => set({ sessionDrawerVisible: true }),
  closeSessionDrawer: () => set({ sessionDrawerVisible: false }),
}));
```

### 5.2 使用 Zustand 管理 Drawer

```typescript
// src/pages/chat/ChatPage.tsx
import { useUIStore } from '@/store/uiStore';

export const ChatPage: React.FC = () => {
  const {
    healthRecordDrawerVisible,
    preferenceDrawerVisible,
    sessionDrawerVisible,
    openHealthRecordDrawer,
    closeHealthRecordDrawer,
    openPreferenceDrawer,
    closePreferenceDrawer,
    openSessionDrawer,
    closeSessionDrawer,
  } = useUIStore();

  return (
    <>
      {/* 触发按钮 */}
      <Button onClick={openHealthRecordDrawer}>健康档案</Button>
      <Button onClick={openPreferenceDrawer}>偏好设置</Button>
      
      {/* Drawer 组件 */}
      <HealthRecordDrawer
        visible={healthRecordDrawerVisible}
        onClose={closeHealthRecordDrawer}
        userId={user?.id || ''}
      />
      
      <PreferenceDrawer
        visible={preferenceDrawerVisible}
        onClose={closePreferenceDrawer}
        userId={user?.id || ''}
      />
    </>
  );
};
```

### 5.3 Drawer 内容懒加载

```typescript
// src/components/user/HealthRecordDrawer.tsx
import { Drawer, Tabs } from 'antd';
import { lazy, Suspense } from 'react';

// 懒加载抽屉内容
const HealthProfile = lazy(() => import('./HealthProfile'));
const HealthCheck = lazy(() => import('./HealthCheck'));
const Medication = lazy(() => import('./Medication'));

export const HealthRecordDrawer: React.FC<HealthRecordDrawerProps> = ({
  visible,
  onClose,
  userId,
}) => {
  const tabItems = [
    {
      key: 'profile',
      label: '基本信息',
      children: (
        <Suspense fallback={<div>加载中...</div>}>
          <HealthProfile userId={userId} />
        </Suspense>
      ),
    },
    {
      key: 'health_check',
      label: '健康自测',
      children: (
        <Suspense fallback={<div>加载中...</div>}>
          <HealthCheck userId={userId} />
        </Suspense>
      ),
    },
    {
      key: 'medication',
      label: '药物记录',
      children: (
        <Suspense fallback={<div>加载中...</div>}>
          <Medication userId={userId} />
        </Suspense>
      ),
    },
  ];

  return (
    <Drawer
      title="健康档案"
      placement="right"
      width={600}
      open={visible}
      onClose={onClose}
      destroyOnClose
    >
      <Tabs items={tabItems} />
    </Drawer>
  );
};
```

### 5.4 Drawer 动画优化

```typescript
// src/components/common/AnimatedDrawer.tsx
import { Drawer, DrawerProps } from 'antd';
import { motion, AnimatePresence } from 'framer-motion';

interface AnimatedDrawerProps extends DrawerProps {
  children: React.ReactNode;
}

export const AnimatedDrawer: React.FC<AnimatedDrawerProps> = ({
  open,
  children,
  ...props
}) => {
  return (
    <Drawer {...props} open={open}>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 100 }}
            transition={{ duration: 0.3 }}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </Drawer>
  );
};
```

---

## 6. 样式兼容性

### 6.1 避免样式冲突

```typescript
// src/styles/drawer.css
/* ChatUI 和 Ant Design Drawer 样式兼容 */

/* 确保 Drawer 内容区域样式正确 */
.ant-drawer-body {
  padding: 24px;
}

/* ChatUI 消息在 Drawer 中的样式 */
.ant-drawer-body .chatui-message {
  margin-bottom: 16px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .ant-drawer {
    width: 80% !important;
  }
}
```

### 6.2 TailwindCSS 与 Ant Design 兼容

```javascript
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  corePlugins: {
    preflight: false, // 禁用 Tailwind 的默认样式，避免与 Ant Design 冲突
  },
  theme: {
    extend: {
      // 自定义主题变量
    },
  },
};
```

---

## 7. 完整示例

### 7.1 完整的聊天页面（包含所有 Drawer）

```typescript
// src/pages/chat/ChatPage.tsx
import { useState } from 'react';
import { Layout, Button, Space } from 'antd';
import { UserOutlined, SettingOutlined, MenuOutlined } from '@ant-design/icons';
import { Chat } from '@chatui/core';
import { HealthRecordDrawer } from '@/components/user/HealthRecordDrawer';
import { PreferenceDrawer } from '@/components/user/PreferenceDrawer';
import { MobileSessionDrawer } from '@/components/chat/MobileSessionDrawer';
import { useBreakpoint } from '@/hooks/useMediaQuery';
import { useAuthStore } from '@/store/authStore';
import { useChat } from '@/hooks/useChat';

const { Content, Sider } = Layout;

export const ChatPage: React.FC = () => {
  const { user } = useAuthStore();
  const { isMobile } = useBreakpoint();
  const [selectedSessionId, setSelectedSessionId] = useState<string>('');
  
  // Drawer 状态
  const [healthRecordVisible, setHealthRecordVisible] = useState(false);
  const [preferenceVisible, setPreferenceVisible] = useState(false);
  const [sessionDrawerVisible, setSessionDrawerVisible] = useState(false);

  // 聊天功能
  const { messages, sendMessage } = useChat(selectedSessionId);

  return (
    <Layout className="h-screen">
      {/* 桌面端：固定侧边栏 */}
      {!isMobile && (
        <Sider width={250} className="border-r">
          <SessionList
            selectedSessionId={selectedSessionId}
            onSelect={setSelectedSessionId}
          />
        </Sider>
      )}

      <Layout>
        {/* 头部工具栏 */}
        <div className="border-b p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isMobile && (
              <Button
                icon={<MenuOutlined />}
                onClick={() => setSessionDrawerVisible(true)}
              />
            )}
            <h2 className="m-0">CozyChat</h2>
          </div>
          
          <Space>
            <Button
              icon={<UserOutlined />}
              onClick={() => setHealthRecordVisible(true)}
            >
              健康档案
            </Button>
            <Button
              icon={<SettingOutlined />}
              onClick={() => setPreferenceVisible(true)}
            >
              偏好设置
            </Button>
          </Space>
        </div>

        {/* 聊天内容区域 */}
        <Content className="flex-1 overflow-hidden">
          {selectedSessionId ? (
            <Chat
              messages={messages}
              onSend={sendMessage}
              placeholder="输入您的问题..."
              toolbar={[
                { type: 'voice', icon: 'mic' },
                { type: 'image', icon: 'image' },
                { type: 'file', icon: 'file' },
              ]}
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <p>请选择一个会话或创建新会话</p>
            </div>
          )}
        </Content>
      </Layout>

      {/* Drawer 组件 */}
      <HealthRecordDrawer
        visible={healthRecordVisible}
        onClose={() => setHealthRecordVisible(false)}
        userId={user?.id || ''}
      />
      
      <PreferenceDrawer
        visible={preferenceVisible}
        onClose={() => setPreferenceVisible(false)}
        userId={user?.id || ''}
      />
      
      {isMobile && (
        <MobileSessionDrawer
          visible={sessionDrawerVisible}
          onClose={() => setSessionDrawerVisible(false)}
          selectedSessionId={selectedSessionId}
          onSelect={(id) => {
            setSelectedSessionId(id);
            setSessionDrawerVisible(false);
          }}
        />
      )}
    </Layout>
  );
};
```

---

## 8. 总结

### 8.1 实现方案

**使用 Ant Design Drawer 实现侧边弹出功能**

1. **健康档案抽屉** - 使用 `Drawer` + `Tabs` 组织内容
2. **偏好设置抽屉** - 使用 `Drawer` + `Form` 实现设置
3. **移动端会话列表** - 使用 `Drawer` + `List` 展示会话
4. **其他功能抽屉** - 使用 `Drawer` 作为通用容器

### 8.2 技术栈

```yaml
核心聊天:
  - @chatui/core: 聊天核心功能

通用组件:
  - antd: 通用组件（Drawer、Tabs、Form、List等）
  - @ant-design/icons: 图标

状态管理:
  - zustand: Drawer 状态管理

样式方案:
  - @chatui/core: 聊天组件样式
  - antd: 通用组件样式（包括 Drawer）
  - tailwindcss: 自定义样式（可选）
```

### 8.3 最佳实践

1. **状态管理** - 使用 Zustand 管理 Drawer 状态
2. **懒加载** - Drawer 内容使用懒加载优化性能
3. **响应式** - 移动端和桌面端使用不同的 Drawer 宽度
4. **样式兼容** - 禁用 Tailwind preflight，避免样式冲突
5. **动画优化** - 使用 framer-motion 优化 Drawer 动画

---

**文档版本**: v1.0  
**最后更新**: 2025-11-07  
**维护者**: CozyChat Team

