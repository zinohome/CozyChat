# VibeKanban任务导入说明

## 📋 任务列表已生成

已创建以下文件：
1. **任务列表文档**: `docs/reports/三大人格化引擎更新任务列表.md` - 详细的任务说明
2. **JSON格式任务列表**: `docs/reports/vibekanban_tasks.json` - 可用于导入VibeKanban

## 🚀 如何导入到VibeKanban

### 方法1：手动创建任务（推荐）

由于VibeKanban API暂时无法连接，建议手动创建任务：

1. **打开VibeKanban项目**
   - 项目名称：`CozyChat - 三大人格化引擎系统重构`
   - 如果没有项目，先创建项目

2. **按阶段创建任务组**
   - 阶段五：测试验证（13个任务）
   - 阶段六：清理旧代码（8个任务）
   - 阶段七：文档更新（5个任务）

3. **创建任务时参考**
   - 任务标题：使用 `T-XXX: 任务名称` 格式
   - 任务描述：从 `vibekanban_tasks.json` 复制
   - 优先级：P0/P1/P2
   - 预计时间：参考JSON中的estimated_time

### 方法2：使用脚本导入（如果API恢复）

如果VibeKanban API恢复，可以使用以下Python脚本导入：

```python
import json
import requests

# 读取任务列表
with open('docs/reports/vibekanban_tasks.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 获取项目ID（需要先调用list_projects）
project_id = "your-project-id"

# 创建任务
for task in data['tasks']:
    response = requests.post(
        f'http://127.0.0.1:43820/api/projects/{project_id}/tasks',
        json={
            'title': task['title'],
            'description': task['description'],
            'status': 'todo',
            'priority': task['priority']
        }
    )
    print(f"Created task: {task['title']}")
```

## 📊 任务统计

### 按优先级
- **P0 (必须完成)**: 18个任务，预计5-6天
- **P1 (建议完成)**: 5个任务，预计1.5天
- **P2 (可选)**: 3个任务，预计0.3天
- **总计**: 26个任务，预计6.8-7.8天

### 按阶段
- **阶段五：测试验证**: 13个任务，预计4-4.5天
- **阶段六：清理旧代码**: 8个任务，预计1.2天
- **阶段七：文档更新**: 5个任务，预计1.1天

## 🎯 建议的执行顺序

### 第一周：测试验证
1. Day 1-2: 单元测试（T-501到T-505）
2. Day 3: 继续单元测试（T-504, T-505）
3. Day 4: 集成测试（T-511到T-514）
4. Day 5: 回归和性能测试（T-531, T-532, T-521, T-522, T-523）

### 第二周：清理和文档
1. Day 1: 代码迁移（T-601到T-603）
2. Day 2: 删除废弃文件（T-611到T-614, T-621）
3. Day 3: 文档更新（T-701, T-702, T-711）
4. Day 4: 配置文档更新（T-721到T-723）
5. Day 5: 最终验证

## 📝 任务命名规范

- **格式**: `T-XXX: 任务名称`
- **编号规则**:
  - T-5XX: 阶段五（测试验证）
  - T-6XX: 阶段六（清理旧代码）
  - T-7XX: 阶段七（文档更新）

## ⚠️ 重要提醒

1. **执行顺序**: 必须先完成测试验证，然后才能清理旧代码
2. **风险控制**: 删除文件前必须所有测试通过，并创建Git备份
3. **文档同步**: 代码变更后及时更新文档

## 📞 如有问题

- 参考详细任务列表：`docs/reports/三大人格化引擎更新任务列表.md`
- 参考完成度分析：`docs/reports/三大人格化引擎更新完成度分析.md`

---

**创建日期**: 2025-01-XX  
**状态**: 待导入VibeKanban
