# VibeKanban MCP工具连接问题诊断

**诊断时间**: 2026-01-02  
**问题**: MCP工具无法连接到VibeKanban API

---

## 🔍 问题分析

### 发现的问题

1. **端口不匹配**
   - ✅ VibeKanban服务器实际运行在: `http://127.0.0.1:44524`
   - ❌ MCP工具尝试连接: `http://127.0.0.1:43820`
   - ❌ 端口43820没有服务监听

2. **服务器状态**
   - ✅ VibeKanban服务器正在运行（进程ID: 9047）
   - ✅ 端口44524可以正常访问
   - ✅ API返回正常（已获取项目列表，包括CozyChat项目）

3. **项目信息**
   - CozyChat项目ID: `95d04669-8987-46d7-9487-2ba503b1b221`
   - 项目名称: `CozyChat`

---

## 🔧 可能的原因

### 1. MCP工具端口配置问题

MCP工具可能：
- 硬编码了端口43820
- 需要环境变量配置端口
- 需要配置文件指定端口
- 应该自动发现端口但未实现

### 2. 端口动态分配

VibeKanban服务器可能：
- 每次启动时动态分配端口
- 端口信息存储在某个配置文件中
- MCP工具需要读取配置文件获取端口

### 3. MCP工具版本问题

当前使用的MCP工具版本可能：
- 存在端口配置bug
- 需要更新到最新版本
- 需要特定的配置方式

---

## 🛠️ 解决方案

### 方案1: 检查MCP工具配置（推荐）

MCP工具可能需要通过以下方式配置端口：

1. **环境变量**
   ```bash
   export VK_API_PORT=44524
   export VIBE_KANBAN_PORT=44524
   ```

2. **配置文件**
   - 检查 `~/.vibe-kanban/` 目录下的配置文件
   - 检查Cursor的MCP配置

3. **命令行参数**
   - 可能需要添加 `--port 44524` 参数

### 方案2: 使用正确的端口直接调用API

由于API在44524端口正常工作，可以：
1. 直接使用HTTP API创建任务
2. 编写脚本通过44524端口调用API

### 方案3: 重启MCP工具

可能需要：
1. 重启MCP工具进程
2. 确保MCP工具能发现正确的端口

---

## 📋 验证步骤

### 步骤1: 验证服务器可访问性

```bash
# 测试API连接
curl http://127.0.0.1:44524/api/projects

# 应该返回项目列表
```

### 步骤2: 检查MCP工具配置

```bash
# 检查环境变量
env | grep -i "vibe\|kanban\|port"

# 检查配置文件
find ~/.vibe-kanban -type f
```

### 步骤3: 测试MCP工具连接

```bash
# 尝试设置环境变量后重启MCP工具
export VK_API_PORT=44524
# 然后重启Cursor或MCP工具
```

---

## 🎯 临时解决方案

### 直接使用HTTP API

由于API在44524端口正常工作，可以编写脚本直接调用API：

```python
import requests
import json

# VibeKanban API地址
API_BASE = "http://127.0.0.1:44524/api"

# CozyChat项目ID
PROJECT_ID = "95d04669-8987-46d7-9487-2ba503b1b221"

# 创建任务
def create_task(project_id, title, description):
    response = requests.post(
        f"{API_BASE}/projects/{project_id}/tasks",
        json={
            "title": title,
            "description": description,
            "status": "todo"
        }
    )
    return response.json()

# 使用示例
task = create_task(
    PROJECT_ID,
    "T-501: Knowledge Engine单元测试",
    "创建test_engines/test_knowledge/目录，测试Cognee引擎..."
)
```

---

## 📝 下一步行动

1. **立即行动**: 尝试设置环境变量 `VK_API_PORT=44524`
2. **检查配置**: 查看MCP工具是否有配置文件可以设置端口
3. **备用方案**: 如果MCP工具无法修复，使用HTTP API直接创建任务
4. **长期方案**: 联系VibeKanban开发者或查看文档，了解正确的端口配置方式

---

## 🔗 相关资源

- VibeKanban项目ID: `95d04669-8987-46d7-9487-2ba503b1b221`
- API地址: `http://127.0.0.1:44524/api`
- 任务列表JSON: `docs/reports/vibekanban_tasks.json`

---

**状态**: 🔴 问题已识别，待解决  
**优先级**: P0 - 阻塞任务创建
