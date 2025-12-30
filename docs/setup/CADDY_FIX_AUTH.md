# Caddy Authorization Header 修复指南

## 问题症状

请求被转发到 OpenAI，但返回 401 "Invalid authorization header"。

## 原因分析

`{$OPENAI_API_KEY}` 环境变量可能：
1. 未设置
2. Caddy 无法读取
3. 值为空

## 解决方案

### 方法1：检查环境变量（推荐）

```bash
# 检查环境变量是否设置
echo $OPENAI_API_KEY

# 如果为空，设置环境变量
export OPENAI_API_KEY="sk-your-real-openai-key"

# 如果使用 systemd，需要在服务文件中设置
sudo systemctl edit caddy
# 添加：
# [Service]
# Environment="OPENAI_API_KEY=sk-your-real-openai-key"

# 重启 Caddy
sudo systemctl restart caddy
```

### 方法2：验证环境变量是否被 Caddy 读取

```bash
# 检查 Caddy 进程的环境变量
sudo cat /proc/$(pgrep caddy)/environ | tr '\0' '\n' | grep OPENAI

# 或使用 systemd
sudo systemctl show caddy --property=Environment
```

### 方法3：临时测试（硬编码真实 Key）

如果环境变量有问题，可以临时硬编码测试（**仅用于测试，不要提交到 Git**）：

```caddyfile
header_up Authorization "Bearer sk-your-real-openai-key-here"
```

## 验证步骤

### 1. 检查环境变量

```bash
# 在运行 Caddy 的用户/服务环境中检查
sudo -u caddy env | grep OPENAI_API_KEY
```

### 2. 测试 Key 替换

```bash
# 使用自定义 Key 测试
curl -v https://oneapi.naivehero.top/v1/models \
  -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH" 2>&1 | grep -i "authorization\|401\|200"
```

### 3. 查看 Caddy 日志

```bash
# 查看详细日志，检查是否有环境变量相关的错误
sudo journalctl -u caddy -n 100 | grep -i "openai\|authorization\|env"
```

## 常见问题

### Q: 环境变量设置了但 Caddy 还是读不到？

**A:** 可能的原因：
1. Caddy 服务启动时环境变量未设置
2. 需要使用 systemd 环境文件
3. 需要重启 Caddy 服务

**解决**：
```bash
# 创建 systemd 环境文件
sudo mkdir -p /etc/systemd/system/caddy.service.d
sudo tee /etc/systemd/system/caddy.service.d/environment.conf <<EOF
[Service]
Environment="OPENAI_API_KEY=sk-your-real-openai-key"
EOF

# 重新加载并重启
sudo systemctl daemon-reload
sudo systemctl restart caddy
```

### Q: 如何确认 Key 是否被正确替换？

**A:** 可以通过以下方式验证：
1. 使用错误的真实 Key，如果返回 401，说明替换成功
2. 查看 Caddy 的调试日志（如果启用）
3. 测试不同的自定义 Key，只有正确的自定义 Key 才能通过

## 调试技巧

### 启用详细日志

在 Caddyfile 中：
```caddyfile
log {
    output file /var/log/caddy/access.log
    format json
    level DEBUG
}
```

### 测试环境变量替换

创建一个测试端点：
```caddyfile
handle /test-env {
    respond "OPENAI_API_KEY: {$OPENAI_API_KEY}" 200
}
```

然后访问：`https://oneapi.naivehero.top/test-env`

**注意**：测试后记得删除这个端点，避免泄露 Key。

