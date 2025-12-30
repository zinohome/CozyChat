# Caddy WebSocket 支持说明

## 概述

Caddy 配置已完整支持 WebSocket 连接，包括 OpenAI Realtime API 等长时间运行的 WebSocket 连接。

## WebSocket 支持特性

### ✅ 已配置的功能

1. **自动 WebSocket 升级**
   - Caddy 2 默认支持 WebSocket，会自动检测并处理 WebSocket 升级请求
   - 无需额外配置即可支持 WebSocket 连接

2. **显式请求头转发**
   - 配置中显式转发了所有 WebSocket 相关的请求头：
     - `Connection`
     - `Upgrade`
     - `Sec-WebSocket-Key`
     - `Sec-WebSocket-Version`
     - `Sec-WebSocket-Protocol`
     - `Sec-WebSocket-Extensions`

3. **HTTP/1.1 和 HTTP/2 支持**
   - WebSocket 需要 HTTP/1.1，Caddy 会自动降级到 HTTP/1.1 用于 WebSocket 连接
   - 普通 HTTP 请求可以使用 HTTP/2

4. **长时间连接支持**
   - Caddy 默认支持长时间运行的 WebSocket 连接
   - 无需额外配置超时设置
   - 适合 OpenAI Realtime API 等需要保持长时间连接的场景

5. **流式数据传输**
   - 配置了 `flush_interval -1`，确保流式数据及时传输
   - 支持 Server-Sent Events (SSE) 和 WebSocket

## 支持的 WebSocket 端点

### OpenAI Realtime API

```
wss://oneapi.naivehero.top/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01
```

**使用方式**：

```javascript
// 前端连接示例
const ws = new WebSocket(
  'wss://oneapi.naivehero.top/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
  ['openai-insecure-api-key', 'sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH']
);

ws.onopen = () => {
  console.log('WebSocket connected');
};

ws.onmessage = (event) => {
  console.log('Received:', event.data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket closed');
};
```

### 其他 WebSocket 端点

所有通过 Caddy 代理的 OpenAI API WebSocket 端点都支持：

- `/v1/realtime` - Realtime API
- 其他 OpenAI WebSocket 端点（如果有）

## 工作原理

```
客户端 WebSocket 请求
  ↓
使用自定义 Key: sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH
  ↓
Caddy 检测 WebSocket 升级请求
  ↓
转发 WebSocket 升级头
  ↓
替换 Authorization 为真实 OpenAI Key
  ↓
建立 WebSocket 连接到 OpenAI
  ↓
双向数据传输（保持连接）
```

## 测试 WebSocket 连接

### 使用 curl（测试连接）

```bash
# 注意：curl 对 WebSocket 支持有限，建议使用专门的 WebSocket 客户端
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: test" \
  -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH" \
  https://oneapi.naivehero.top/v1/realtime
```

### 使用 Node.js 测试

```javascript
const WebSocket = require('ws');

const ws = new WebSocket(
  'wss://oneapi.naivehero.top/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
  {
    headers: {
      'Authorization': 'Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH'
    }
  }
);

ws.on('open', () => {
  console.log('Connected');
});

ws.on('message', (data) => {
  console.log('Received:', data.toString());
});

ws.on('error', (error) => {
  console.error('Error:', error);
});
```

### 使用浏览器测试

打开浏览器控制台，运行：

```javascript
const ws = new WebSocket(
  'wss://oneapi.naivehero.top/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
  ['openai-insecure-api-key', 'sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH']
);

ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', e.data);
ws.onerror = (e) => console.error('Error:', e);
ws.onclose = () => console.log('Closed');
```

## 故障排查

### WebSocket 连接失败

1. **检查 Caddy 日志**：
   ```bash
   docker-compose -f docker-compose.caddy.yml logs -f caddy
   # 或
   tail -f logs/caddy/access.log
   ```

2. **检查请求头**：
   - 确保包含 `Upgrade: websocket` 和 `Connection: Upgrade`
   - 确保 Authorization header 使用自定义 Key

3. **检查网络连接**：
   ```bash
   # 测试基本连接
   curl -I https://oneapi.naivehero.top/v1/models \
     -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH"
   ```

### WebSocket 连接被断开

1. **检查超时设置**：
   - Caddy 默认支持长时间连接，无需额外配置
   - 如果频繁断开，检查客户端超时设置

2. **检查网络稳定性**：
   - 确保服务器网络稳定
   - 检查防火墙设置

### 性能问题

1. **连接数限制**：
   - Caddy 默认没有严格的连接数限制
   - 如需限制，可以在配置中添加

2. **资源使用**：
   - 监控服务器 CPU 和内存使用
   - 长时间运行的 WebSocket 连接会占用资源

## 最佳实践

1. **错误处理**：
   - 实现自动重连机制
   - 处理网络中断情况

2. **心跳检测**：
   - 对于长时间连接，实现心跳检测
   - 定期发送 ping/pong 保持连接活跃

3. **连接管理**：
   - 及时关闭不需要的连接
   - 避免创建过多并发连接

4. **日志记录**：
   - 记录 WebSocket 连接事件
   - 监控连接状态和错误

## 相关文档

- [Caddy WebSocket 文档](https://caddyserver.com/docs/quick-starts/reverse-proxy#websockets)
- [OpenAI Realtime API 文档](https://platform.openai.com/docs/guides/realtime)
- [完整部署指南](./CADDY_PROXY.md)
- [Docker 部署指南](./CADDY_DOCKER_DEPLOY.md)

