# 数据库索引优化迁移说明

**迁移ID**: `f99ada8c6f7e`  
**迁移名称**: add_performance_optimization_indexes  
**创建时间**: 2025-11-20

## 📋 概述

本次迁移添加了13个性能优化索引，覆盖Users、Sessions和Messages三个核心表，旨在提升常见查询的性能。

## 🎯 优化目标

### 1. 查询性能提升
- **目标**: 将常见查询响应时间从 >200ms 降低到 <50ms
- **方法**: 添加复合索引和部分索引

### 2. 减少索引存储开销
- **方法**: 使用部分索引（Partial Indexes）只索引常用数据
- **收益**: 减少20-30%的索引存储空间

### 3. 优化N+1查询
- **方法**: 添加针对性的复合索引
- **收益**: 避免多次单独查询，提升批量查询性能

## 📊 新增索引详情

### User表索引（5个）

| 索引名 | 列 | 类型 | 用途 |
|--------|-----|------|------|
| `idx_users_status_role` | (status, role) | 复合索引 | 查询特定状态和角色的用户 |
| `idx_users_email_verified_status` | (email_verified, status) | 复合索引 | 查询已验证的活跃用户 |
| `idx_users_username_active` | (username) WHERE status='active' | 部分索引 | 活跃用户用户名查询 |
| `idx_users_email_active` | (email) WHERE status='active' | 部分索引 | 活跃用户邮箱查询 |
| `idx_users_last_login_at` | (last_login_at) | 单列索引 | 查询最近登录用户 |

**优化场景**:
```python
# 场景1：查询所有活跃的管理员
users = session.query(User).filter(
    User.status == 'active',
    User.role == 'admin'
).all()

# 场景2：查询已验证的活跃用户
users = session.query(User).filter(
    User.email_verified == True,
    User.status == 'active'
).all()

# 场景3：按最近登录排序
users = session.query(User).order_by(
    User.last_login_at.desc()
).limit(10).all()
```

### Session表索引（3个）

| 索引名 | 列 | 类型 | 用途 |
|--------|-----|------|------|
| `idx_sessions_personality_user` | (personality_id, user_id) | 复合索引 | 按人格查询特定用户的会话 |
| `idx_sessions_personality_active` | (personality_id) WHERE deleted_at IS NULL | 部分索引 | 活跃会话的人格查询 |
| `idx_sessions_user_personality_lastmsg` | (user_id, personality_id, last_message_at) WHERE deleted_at IS NULL | 复合索引 | 多维度会话查询和排序 |

**优化场景**:
```python
# 场景1：查询用户在特定人格下的所有会话
sessions = session.query(Session).filter(
    Session.user_id == user_id,
    Session.personality_id == 'health_assistant',
    Session.deleted_at == None
).order_by(Session.last_message_at.desc()).all()

# 场景2：统计各人格的活跃会话数
personality_stats = session.query(
    Session.personality_id,
    func.count(Session.id)
).filter(
    Session.deleted_at == None
).group_by(Session.personality_id).all()
```

### Message表索引（5个）

| 索引名 | 列 | 类型 | 用途 |
|--------|-----|------|------|
| `idx_messages_role_session` | (role, session_id) | 复合索引 | 按角色筛选会话消息 |
| `idx_messages_session_role_created` | (session_id, role, created_at) | 复合索引 | 多维度消息查询和排序 |
| `idx_messages_session_assistant` | (session_id) WHERE role='assistant' | 部分索引 | AI回复消息查询 |
| `idx_messages_session_user` | (session_id) WHERE role='user' | 部分索引 | 用户输入消息查询 |
| `idx_messages_user_role_created` | (user_id, role, created_at) | 复合索引 | 按用户和角色查询消息 |

**优化场景**:
```python
# 场景1：只查询会话中的AI回复
assistant_messages = session.query(Message).filter(
    Message.session_id == session_id,
    Message.role == 'assistant'
).order_by(Message.created_at.asc()).all()

# 场景2：统计用户的总消息数（按角色分类）
user_message_count = session.query(func.count(Message.id)).filter(
    Message.user_id == user_id,
    Message.role == 'user'
).scalar()

# 场景3：查询用户最近的AI对话
recent_conversations = session.query(Message).filter(
    Message.user_id == user_id,
    Message.role.in_(['user', 'assistant'])
).order_by(Message.created_at.desc()).limit(50).all()
```

## 🚀 性能预期

### 查询性能提升

| 查询类型 | 优化前 | 优化后 | 提升 |
|---------|--------|--------|------|
| 用户列表（按状态+角色） | ~180ms | ~25ms | **86%** |
| 会话列表（按用户+人格） | ~220ms | ~40ms | **82%** |
| 消息列表（按会话+角色） | ~150ms | ~20ms | **87%** |
| 统计查询（count） | ~300ms | ~50ms | **83%** |

### 存储开销

| 项目 | 估算值 |
|-----|--------|
| 新增索引总大小 | ~50-100MB（取决于数据量） |
| 部分索引节省空间 | ~20-30MB |
| 净增加 | ~30-70MB |

## ⚠️ 注意事项

### 1. 迁移时间
- **小数据库（<10万条记录）**: ~5-10秒
- **中数据库（10-100万条记录）**: ~30-60秒
- **大数据库（>100万条记录）**: 1-5分钟

### 2. 锁定影响
- PostgreSQL会对表加短暂的锁
- 建议在**低峰期**执行迁移
- 如有必要，可使用 `CONCURRENTLY` 选项（需手动调整）

### 3. 回滚支持
- 完全支持回滚：`alembic downgrade -1`
- 回滚会删除所有新增的索引
- 回滚时间与迁移时间相当

## 📝 使用方法

### 执行迁移
```bash
cd backend
alembic upgrade head
```

### 验证索引创建
```sql
-- 查看Users表的所有索引
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'users';

-- 查看Sessions表的所有索引
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'sessions';

-- 查看Messages表的所有索引
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'messages';
```

### 回滚迁移
```bash
cd backend
alembic downgrade -1
```

## 🔍 性能测试

迁移后建议执行以下测试：

```bash
# 1. 运行单元测试
pytest tests/test_api/test_sessions.py -v
pytest tests/test_api/test_messages.py -v
pytest tests/test_api/test_users.py -v

# 2. 运行性能测试
pytest tests/performance/ -v

# 3. 检查慢查询日志
# 查看 PostgreSQL 日志，确认查询时间<50ms
```

## 📈 监控指标

迁移后需要监控：

1. **查询性能**
   - 平均查询时间
   - P95/P99查询时间
   - 慢查询数量

2. **数据库资源**
   - 索引缓存命中率
   - 磁盘I/O
   - 表扫描vs索引扫描比例

3. **应用性能**
   - API响应时间
   - 数据库连接池使用率
   - 错误率

## 🎓 学习资源

- [PostgreSQL索引最佳实践](https://www.postgresql.org/docs/current/indexes.html)
- [部分索引详解](https://www.postgresql.org/docs/current/indexes-partial.html)
- [复合索引设计原则](https://www.postgresql.org/docs/current/indexes-multicolumn.html)

## 📞 联系方式

如遇问题，请参考：
- 项目文档：`docs/05-数据库设计.md`
- 性能优化计划：`docs/优化实施计划.md`

