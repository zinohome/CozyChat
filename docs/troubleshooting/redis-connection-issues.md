# Redis连接问题故障排查

## 问题描述

当出现以下错误时，说明Redis连接存在问题：

```
WARNING [app/engines/memory/queue.py:236] Memory queue disabled due to Redis connection error: 
Error while reading from 192.168.66.10:6379 : (54, 'Connection reset by peer'). 
Memory async write will be disabled. Please check Redis configuration.
```

## 错误原因分析

### 1. "Connection reset by peer" 错误

这个错误通常表示：
- **Redis服务器主动关闭了连接**：可能是超时、配置限制或服务器重启
- **网络问题**：网络不稳定、防火墙拦截、连接被中间设备重置
- **Redis配置问题**：`timeout`、`tcp-keepalive` 等配置不当
- **连接池问题**：连接池配置不当，连接长时间空闲被服务器关闭

### 2. 常见原因

| 原因 | 说明 | 解决方案 |
|------|------|----------|
| Redis服务器超时设置 | `timeout` 配置过短，空闲连接被关闭 | 增加 `timeout` 或设置为 0（禁用） |
| 网络不稳定 | 网络抖动、防火墙重置连接 | 检查网络稳定性，配置防火墙规则 |
| Redis服务器重启 | Redis服务重启导致连接断开 | 检查Redis服务状态，配置自动重连 |
| 连接池配置不当 | 连接池没有健康检查机制 | 使用新版本配置（已修复） |
| 认证失败 | 密码错误或认证配置问题 | 检查 `REDIS_PASSWORD` 配置 |

## 解决方案

### 方案1：检查Redis服务器配置（推荐）

#### 1.1 检查Redis服务状态

```bash
# 检查Redis是否运行
redis-cli -h 192.168.66.10 -p 6379 ping

# 如果配置了密码
redis-cli -h 192.168.66.10 -p 6379 -a your_password ping
```

#### 1.2 检查Redis配置

编辑Redis配置文件（通常在 `/etc/redis/redis.conf` 或 `/usr/local/etc/redis.conf`）：

```conf
# 增加超时时间（秒），0表示禁用超时
timeout 300

# 启用TCP keepalive（推荐）
tcp-keepalive 60

# 最大客户端连接数
maxclients 10000

# 如果使用密码，确保配置正确
requirepass your_password
```

#### 1.3 重启Redis服务

```bash
# 使用systemd
sudo systemctl restart redis

# 或使用service
sudo service redis restart
```

### 方案2：更新应用配置

#### 2.1 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# Redis连接URL
REDIS_URL=redis://192.168.66.10:6379/0

# Redis密码（如果配置了）
REDIS_PASSWORD=your_password

# 连接池配置
REDIS_MAX_CONNECTIONS=50

# 连接超时配置（秒）
REDIS_SOCKET_CONNECT_TIMEOUT=5.0
REDIS_SOCKET_TIMEOUT=5.0
REDIS_RETRY_ON_TIMEOUT=true
REDIS_HEALTH_CHECK_INTERVAL=30
```

#### 2.2 配置说明

- **REDIS_SOCKET_CONNECT_TIMEOUT**: 连接建立超时时间（默认5秒）
- **REDIS_SOCKET_TIMEOUT**: Socket操作超时时间（默认5秒）
- **REDIS_RETRY_ON_TIMEOUT**: 超时时是否自动重试（默认true）
- **REDIS_HEALTH_CHECK_INTERVAL**: 连接健康检查间隔（默认30秒）

### 方案3：网络问题排查

#### 3.1 检查网络连通性

```bash
# 测试TCP连接
telnet 192.168.66.10 6379

# 或使用nc
nc -zv 192.168.66.10 6379
```

#### 3.2 检查防火墙规则

```bash
# 检查防火墙状态
sudo ufw status
# 或
sudo iptables -L

# 允许Redis端口（如果需要）
sudo ufw allow 6379/tcp
```

#### 3.3 检查网络延迟

```bash
# 测试网络延迟
ping 192.168.66.10

# 测试Redis响应时间
redis-cli -h 192.168.66.10 -p 6379 --latency
```

### 方案4：使用本地Redis（开发环境）

如果Redis服务器不稳定，开发环境可以使用本地Redis：

```bash
# 安装Redis（macOS）
brew install redis

# 启动Redis
brew services start redis

# 或手动启动
redis-server
```

然后更新 `.env`：

```bash
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
```

## 代码修复说明

### 已实现的改进

1. **连接超时配置**：添加了 `socket_connect_timeout` 和 `socket_timeout` 配置
2. **自动重试机制**：配置了 `retry_on_timeout` 和 `retry_on_error`
3. **健康检查**：添加了 `health_check_interval` 定期检查连接
4. **自动重连**：实现了 `_check_and_reconnect()` 方法，连接失败时自动重连
5. **连接恢复**：连接恢复后自动重新启用队列功能

### 代码变更

- `backend/app/config/config.py`: 添加了Redis超时和重试配置项
- `backend/app/engines/memory/queue.py`: 
  - 添加了连接超时和重试参数
  - 实现了 `_check_and_reconnect()` 方法
  - 在所有操作前自动检查连接并重连

## 验证修复

### 1. 检查日志

修复后，如果连接恢复，应该看到：

```
INFO [app/engines/memory/queue.py] Memory queue connection restored
```

### 2. 测试连接

```python
# 在Python中测试
import redis.asyncio as aioredis

async def test_redis():
    client = aioredis.from_url(
        "redis://192.168.66.10:6379/0",
        socket_connect_timeout=5.0,
        socket_timeout=5.0,
        retry_on_timeout=True,
        health_check_interval=30
    )
    result = await client.ping()
    print(f"Redis连接成功: {result}")
    await client.close()

# 运行测试
import asyncio
asyncio.run(test_redis())
```

### 3. 监控队列状态

检查内存队列是否正常工作：

```bash
# 查看应用日志
tail -f logs/app.log | grep -i "memory queue"

# 应该看到：
# - "Memory queue initialized"
# - "Memory queue connection restored" (如果之前有错误)
```

## 预防措施

### 1. Redis服务器配置建议

```conf
# Redis配置文件最佳实践
timeout 300                    # 5分钟超时（或0禁用）
tcp-keepalive 60              # 60秒keepalive
maxclients 10000              # 足够的客户端连接数
tcp-backlog 511               # TCP backlog队列
```

### 2. 监控和告警

建议配置监控：
- Redis服务状态监控
- 连接数监控
- 内存使用监控
- 网络延迟监控

### 3. 高可用方案

生产环境建议使用：
- **Redis Sentinel**：主从复制 + 自动故障转移
- **Redis Cluster**：分布式集群方案
- **连接池**：使用连接池管理连接

## 相关文档

- [Redis官方文档](https://redis.io/docs/)
- [Redis配置参考](https://redis.io/docs/management/config/)
- [CozyChat配置指南](../setup/CONFIG.md)

## 常见问题

### Q1: 为什么连接会被重置？

A: 通常是因为Redis服务器的 `timeout` 配置过短，或者网络不稳定。建议增加 `timeout` 值或设置为 0（禁用超时）。

### Q2: 修复后仍然出现错误？

A: 请检查：
1. Redis服务是否正常运行
2. 网络是否稳定
3. 防火墙是否允许连接
4. Redis密码是否正确

### Q3: 如何禁用异步写入功能？

A: 如果Redis不可用，可以设置环境变量：

```bash
MEMORY_ASYNC_WRITE=false
```

这样记忆会同步写入，但可能影响性能。

### Q4: 生产环境如何配置？

A: 生产环境建议：
1. 使用Redis Sentinel或Cluster
2. 配置监控和告警
3. 使用连接池
4. 设置合理的超时和重试参数

## 联系支持

如果问题仍未解决，请提供以下信息：
1. Redis版本和配置
2. 网络环境（本地/Docker/云服务器）
3. 完整的错误日志
4. Redis服务器日志

