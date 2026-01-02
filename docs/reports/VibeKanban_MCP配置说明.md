# VibeKanban MCP配置说明

**参考文档**: [VibeKanban MCP Server Configuration](https://www.vibekanban.com/docs/integrations/mcp-server-configuration)

---

## 🔍 问题分析

根据官方文档和实际测试，发现以下问题：

1. **端口动态分配**: VibeKanban服务器默认绑定到随机可用端口
2. **MCP工具无法发现端口**: MCP工具尝试连接的端口（43820, 43714等）与服务器实际端口（44524）不匹配

---

## ✅ 解决方案

### 1. 设置固定端口

根据文档，可以通过环境变量 `PORT` 来指定VibeKanban服务器使用固定端口。

**已更新配置** (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "vibe_kanban": {
      "command": "npx",
      "args": [
        "-y",
        "vibe-kanban@latest",
        "--mcp"
      ],
      "env": {
        "PORT": "44524",
        "VK_API_PORT": "44524",
        "VIBE_KANBAN_PORT": "44524",
        "VK_API_URL": "http://127.0.0.1:44524"
      }
    }
  }
}
```

### 2. 确保VibeKanban服务器使用固定端口

如果VibeKanban服务器是手动启动的，需要设置环境变量：

```bash
PORT=44524 npx vibe-kanban
```

或者如果通过systemd或其他方式启动，需要在启动脚本中设置环境变量。

---

## 🔄 下一步操作

### 1. 重启Cursor（必须）

**重要**: MCP配置更改后需要重启Cursor才能生效。

1. 完全关闭Cursor
2. 重新启动Cursor
3. MCP工具会使用新的环境变量配置

### 2. 验证连接

重启后，尝试调用MCP工具：
```python
mcp_vibe_kanban_list_projects()
```

### 3. 如果仍然失败

如果重启后仍然失败，可能需要：

1. **检查VibeKanban服务器端口**
   - 确保VibeKanban服务器使用固定端口44524启动
   - 检查服务器启动日志，确认端口

2. **检查MCP工具日志**
   - 查看Cursor的MCP工具日志
   - 确认环境变量是否被正确读取

3. **尝试其他端口配置方式**
   - 某些版本可能需要不同的环境变量名
   - 可以尝试: `API_PORT`, `SERVER_PORT` 等

---

## 📋 配置说明

### 环境变量说明

- `PORT`: VibeKanban服务器监听端口（主要配置）
- `VK_API_PORT`: VibeKanban API端口（备用）
- `VIBE_KANBAN_PORT`: VibeKanban端口（备用）
- `VK_API_URL`: 完整的API URL（备用）

### 为什么需要多个环境变量？

不同版本的MCP工具可能使用不同的环境变量名，设置多个可以确保兼容性。

---

## 🔗 相关资源

- **官方文档**: https://www.vibekanban.com/docs/integrations/mcp-server-configuration
- **Vibe Kanban MCP Server**: https://www.vibekanban.com/docs/integrations/vibe-kanban-mcp-server
- **配置文件位置**: `~/.cursor/mcp.json`
- **CozyChat项目ID**: `95d04669-8987-46d7-9487-2ba503b1b221`

---

## ⚠️ 注意事项

1. **端口冲突**: 确保端口44524没有被其他服务占用
2. **防火墙**: 确保本地防火墙允许端口44524的通信
3. **重启要求**: 配置更改后必须重启Cursor才能生效

---

**最后更新**: 2026-01-02  
**状态**: ✅ 配置已更新，待重启验证
