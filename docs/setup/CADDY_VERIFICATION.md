# Caddy 代理验证指南

## 快速验证

### 1. 测试基本 API 调用

```bash
# 测试模型列表 API（使用自定义 Key）
curl -v https://oneapi.naivehero.top/v1/models \
  -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH"

# 预期结果：
# - 返回 200 状态码
# - 返回 JSON 格式的模型列表
# - 包含 OpenAI 的模型信息（如 gpt-4, gpt-3.5-turbo 等）
```

### 2. 测试聊天补全 API

```bash
curl -X POST https://oneapi.naivehero.top/v1/chat/completions \
  -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello, say hi back"}
    ]
  }'

# 预期结果：
# - 返回 200 状态码
# - 返回 JSON 格式的聊天响应
# - 包含 AI 的回复内容
```

### 3. 测试错误 Key（应该返回 401）

```bash
curl -v https://oneapi.naivehero.top/v1/models \
  -H "Authorization: Bearer wrong-key"

# 预期结果：
# - 返回 401 状态码
# - 返回 "Unauthorized: Invalid API Key" 消息
```

## 详细验证步骤

### 1. 检查 Caddy 日志

```bash
# 查看实时日志
sudo journalctl -u caddy -f

# 或查看访问日志
tail -f /var/log/caddy/access.log

# 或如果使用 Docker
docker-compose -f docker-compose.caddy.yml logs -f caddy
```

**成功转发的日志特征**：
- 状态码 200
- 请求被转发到 `api.openai.com`
- 响应时间正常（通常 < 2秒）

### 2. 验证 API Key 替换

**方法1：检查请求头（需要启用详细日志）**

在 Caddyfile 中启用详细日志：
```caddyfile
log {
    output file /var/log/caddy/access.log
    format json
    level DEBUG
}
```

**方法2：通过响应验证**

如果使用自定义 Key 能成功调用 OpenAI API，说明 Key 替换成功。

### 3. 测试不同端点

```bash
# 1. 模型列表
curl https://oneapi.naivehero.top/v1/models \
  -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH"

# 2. 聊天补全
curl -X POST https://oneapi.naivehero.top/v1/chat/completions \
  -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "test"}]}'

# 3. 嵌入向量
curl -X POST https://oneapi.naivehero.top/v1/embeddings \
  -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH" \
  -H "Content-Type: application/json" \
  -d '{"model": "text-embedding-ada-002", "input": "test"}'
```

### 4. 验证 WebSocket 连接（如果使用）

```javascript
// 在浏览器控制台或 Node.js 中测试
const ws = new WebSocket(
  'wss://oneapi.naivehero.top/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
  ['openai-insecure-api-key', 'sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH']
);

ws.onopen = () => {
  console.log('✅ WebSocket 连接成功');
};

ws.onmessage = (event) => {
  console.log('✅ 收到消息:', event.data);
};

ws.onerror = (error) => {
  console.error('❌ WebSocket 错误:', error);
};
```

## 验证清单

### ✅ 基本功能验证

- [ ] 使用自定义 Key 可以成功调用 API
- [ ] 返回正确的 JSON 响应
- [ ] 响应时间正常（< 2秒）
- [ ] 使用错误 Key 返回 401

### ✅ 安全验证

- [ ] 真实 OpenAI Key 不会暴露在响应中
- [ ] 只有使用自定义 Key 的请求才能通过
- [ ] 未授权的请求被正确拒绝

### ✅ 功能验证

- [ ] 模型列表 API 正常工作
- [ ] 聊天补全 API 正常工作
- [ ] 流式响应正常工作（如果使用）
- [ ] WebSocket 连接正常（如果使用）

## 常见问题排查

### 问题1：返回 503 "no upstreams available"

**原因**：健康检查失败或上游不可用

**解决**：
- 检查健康检查配置（已禁用）
- 检查网络连接
- 检查 OpenAI API 是否可访问

### 问题2：返回 401 Unauthorized

**可能原因**：
1. 使用了错误的自定义 Key
2. 环境变量 `OPENAI_API_KEY` 未设置或错误
3. Key 替换失败

**排查**：
```bash
# 检查环境变量
echo $OPENAI_API_KEY

# 检查 Caddy 日志
sudo journalctl -u caddy -n 50
```

### 问题3：返回 502 Bad Gateway

**原因**：无法连接到 OpenAI API

**排查**：
```bash
# 测试到 OpenAI 的连接
curl -I https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_REAL_OPENAI_KEY"

# 检查 DNS 解析
nslookup api.openai.com
```

## 性能验证

### 响应时间测试

```bash
# 测试响应时间
time curl -s https://oneapi.naivehero.top/v1/models \
  -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH" > /dev/null

# 预期：响应时间 < 2秒
```

### 并发测试

```bash
# 使用 ab 或 wrk 进行并发测试
ab -n 100 -c 10 \
  -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH" \
  https://oneapi.naivehero.top/v1/models
```

## 自动化验证脚本

创建测试脚本 `test_caddy_proxy.sh`：

```bash
#!/bin/bash

CUSTOM_KEY="sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH"
BASE_URL="https://oneapi.naivehero.top"

echo "测试 Caddy 代理..."

# 测试1：模型列表
echo "1. 测试模型列表 API..."
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $CUSTOM_KEY" \
  "$BASE_URL/v1/models")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ 模型列表 API 正常"
    echo "   返回模型数量: $(echo "$BODY" | jq '.data | length')"
else
    echo "❌ 模型列表 API 失败: HTTP $HTTP_CODE"
    echo "$BODY"
fi

# 测试2：错误 Key
echo "2. 测试错误 Key 拒绝..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer wrong-key" \
  "$BASE_URL/v1/models")

if [ "$HTTP_CODE" = "401" ]; then
    echo "✅ 错误 Key 正确拒绝"
else
    echo "❌ 错误 Key 未正确拒绝: HTTP $HTTP_CODE"
fi

# 测试3：聊天补全
echo "3. 测试聊天补全 API..."
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $CUSTOM_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "say hi"}]}' \
  "$BASE_URL/v1/chat/completions")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ 聊天补全 API 正常"
    echo "   AI 回复: $(echo "$BODY" | jq -r '.choices[0].message.content')"
else
    echo "❌ 聊天补全 API 失败: HTTP $HTTP_CODE"
    echo "$BODY"
fi

echo "测试完成！"
```

使用方式：
```bash
chmod +x test_caddy_proxy.sh
./test_caddy_proxy.sh
```

## 相关文档

- [完整部署指南](./CADDY_PROXY.md)
- [Docker 部署指南](./CADDY_DOCKER_DEPLOY.md)
- [WebSocket 支持说明](./CADDY_WEBSOCKET.md)

