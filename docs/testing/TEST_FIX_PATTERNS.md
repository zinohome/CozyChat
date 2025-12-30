# 测试修复模式指南

## 修复日期
2025-12-22

## 已修复的测试文件

### 1. test_sessions.py ✅
- ✅ `test_create_session_success`
- ✅ `test_list_sessions_success`
- ✅ `test_list_sessions_with_pagination`
- ✅ `test_get_session_detail_success`
- ✅ `test_update_session_success`
- ✅ `test_delete_session_success`

### 2. test_users.py ✅
- ✅ `test_get_current_user_success`
- ✅ `test_update_current_user_success`
- ✅ `test_get_user_stats`
- ✅ `test_get_user_profile`
- ✅ `test_update_current_user_error`
- ✅ `test_register_user_success`
- ✅ `test_login_user_success`

### 3. test_personalities.py ✅ (部分)
- ✅ `test_list_personalities_success`

### 4. test_auth.py ✅
- ✅ `test_refresh_token_success`

### 5. test_chat.py ✅
- ✅ `test_create_chat_completion_stream`

## 修复模式

### 模式1：API测试 - 需要认证和数据库会话

**适用场景**：所有需要认证的API端点测试

**修复步骤**：

```python
@pytest.mark.asyncio
async def test_api_endpoint(self, client, auth_token, sync_db_session, db_session):
    """测试：API端点"""
    from app.api.deps import get_current_active_user_async, get_db
    from app.utils.security import decode_token
    from app.models.user import User as UserModel
    
    # 1. 从token中获取user_id
    token_payload = decode_token(auth_token)
    user_id = token_payload.get("sub")
    
    # 2. 从数据库获取用户
    user = sync_db_session.query(UserModel).filter(UserModel.id == user_id).first()
    assert user is not None, "User should exist in database"
    
    # 3. 覆盖认证依赖
    async def get_user():
        return user
    
    app.dependency_overrides[get_current_active_user_async] = get_user
    
    # 4. 覆盖数据库会话依赖（如果需要）
    app.dependency_overrides[get_db] = lambda: db_session
    
    # 5. Mock其他依赖（如果需要）
    from unittest.mock import MagicMock
    mock_registry = MagicMock()
    app.dependency_overrides[get_personality_registry] = lambda: mock_registry
    
    try:
        # 6. 执行测试
        response = client.get(
            "/v1/endpoint",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # 7. 断言
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json() if response.status_code != 200 else ''}"
        data = response.json()
        assert isinstance(data, dict)
    finally:
        # 8. 清理依赖覆盖
        app.dependency_overrides.clear()
```

### 模式2：API测试 - 使用同步认证依赖

**适用场景**：使用`get_current_active_user`（同步版本）的API端点

**修复步骤**：

```python
from app.api.deps import get_current_active_user  # 注意：同步版本

# 覆盖依赖（同步函数）
def get_user():
    return user

app.dependency_overrides[get_current_active_user] = get_user
```

### 模式3：API测试 - 使用同步数据库会话

**适用场景**：使用`get_sync_session`的API端点

**修复步骤**：

```python
from app.api.deps import get_sync_session

# 覆盖依赖（生成器函数）
def get_sync_db():
    yield sync_db_session

app.dependency_overrides[get_sync_session] = get_sync_db
```

### 模式4：流式响应测试

**适用场景**：测试流式API响应

**修复步骤**：

```python
from fastapi.responses import StreamingResponse

# Mock编排器
mock_orchestrator = AsyncMock()
async def mock_stream_generator():
    """模拟流式响应生成器"""
    yield b'data: {"id":"chatcmpl-123","choices":[{"delta":{"content":"Hello"}}]}\n\n'
    yield b'data: [DONE]\n\n'

# process_request返回StreamingResponse
mock_stream_response = StreamingResponse(
    mock_stream_generator(),
    media_type="text/event-stream"
)
mock_orchestrator.process_request = AsyncMock(return_value=mock_stream_response)
```

## 常见依赖映射

| API端点类型 | 认证依赖 | 数据库会话依赖 | 其他依赖 |
|------------|---------|---------------|---------|
| 异步端点 | `get_current_active_user_async` | `get_db` (AsyncSession) | 根据端点 |
| 同步端点 | `get_current_active_user` | `get_sync_session` (Session) | 根据端点 |
| 会话API | `get_current_active_user_async` | `get_db` 或 `get_sync_session` | `get_personality_registry` |
| 用户API | `get_current_active_user_async` | `get_db` | 无 |
| 人格API | `get_current_active_user` | 无 | `get_personality_registry` |
| 聊天API | `get_current_active_user_async` | `get_db` | `get_chat_orchestrator` |

## 待修复的测试文件

### API测试文件

1. **test_personalities.py** (部分)
   - `test_get_personality_success`
   - `test_list_personalities_unauthorized`
   - 其他测试方法

2. **test_models.py**
   - 需要查看具体测试内容

3. **test_audio.py**
   - 需要查看具体测试内容

4. **test_chat_integration.py**
   - 需要查看具体测试内容

5. **test_websocket.py**
   - 需要查看具体测试内容

### 非API测试文件

需要根据实际失败情况修复

## 修复检查清单

修复每个测试时，确保：

- [ ] 导入必要的依赖（`app.main.app`, `app.api.deps.*`）
- [ ] 从token中正确获取user_id
- [ ] 从数据库正确查询用户
- [ ] 覆盖所有必需的依赖
- [ ] Mock所有外部依赖
- [ ] 使用try/finally确保清理
- [ ] 断言包含错误信息（便于调试）
- [ ] 清理测试数据（如果创建了）

## 常见错误和解决方案

### 错误1：401 Unauthorized

**原因**：认证依赖未正确覆盖

**解决方案**：
```python
# 确保覆盖了正确的认证依赖
app.dependency_overrides[get_current_active_user_async] = get_user
# 或
app.dependency_overrides[get_current_active_user] = get_user
```

### 错误2：404 Not Found

**原因**：端点不存在或路由未注册

**解决方案**：
- 检查端点路径是否正确
- 检查路由是否在`app/main.py`中注册

### 错误3：500 Internal Server Error

**原因**：数据库会话或依赖未正确覆盖

**解决方案**：
```python
# 确保覆盖了数据库会话依赖
app.dependency_overrides[get_db] = lambda: db_session
# 或
app.dependency_overrides[get_sync_session] = get_sync_db
```

### 错误4：AssertionError

**原因**：断言条件不满足

**解决方案**：
- 检查API实际返回的状态码和内容
- 调整断言以适应实际API行为
- 添加更详细的错误信息

## 相关文档

- [TEST_FIX_SUMMARY_FINAL.md](./TEST_FIX_SUMMARY_FINAL.md) - 修复总结
- [TEST_FIX_PROGRESS_UPDATE.md](./TEST_FIX_PROGRESS_UPDATE.md) - 修复进度

