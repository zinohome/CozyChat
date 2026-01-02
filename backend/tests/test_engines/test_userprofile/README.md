# UserProfile引擎单元测试

## 测试概述

本目录包含UserProfile引擎的完整单元测试，测试覆盖率达到≥85%。

## 测试文件结构

```
test_userprofile/
├── __init__.py
├── test_memobase_engine.py  # MemobaseUserProfileEngine核心测试
├── test_factory.py            # UserProfileEngineFactory测试
├── test_models.py             # UserProfile和ProfileUpdateRequest模型测试
└── README.md                  # 本文件
```

## 测试覆盖范围

### 1. MemobaseUserProfileEngine (`test_memobase_engine.py`)

#### 初始化测试
- ✅ 引擎初始化成功
- ✅ 引擎已初始化，直接返回True
- ✅ 引擎初始化失败
- ✅ 使用默认配置初始化引擎

#### 健康检查测试
- ✅ 健康检查成功
- ✅ 健康检查失败（客户端未初始化）
- ✅ 健康检查异常

#### 获取用户画像测试 (`get_profile`)
- ✅ 成功获取用户画像
- ✅ 无效的UUID格式（抛出ValueError）
- ✅ 用户不存在，自动创建用户成功
- ✅ 用户不存在，自动创建用户失败
- ✅ 用户不存在（404错误），自动创建
- ✅ 用户不存在（422错误），自动创建
- ✅ 获取用户画像时发生其他错误
- ✅ 空画像文本（None）
- ✅ 空字符串画像文本
- ✅ 自定义max_token_size
- ✅ 自动初始化引擎

#### 更新用户画像测试 (`update_profile`)
- ✅ 成功更新用户画像
- ✅ 无效的UUID格式（抛出ValueError）
- ✅ 用户不存在，创建用户后更新画像成功
- ✅ 用户不存在，创建失败，使用no_get=True继续
- ✅ 用户不存在（422错误），创建用户
- ✅ 用户不存在（404错误），创建用户
- ✅ 获取用户时发生其他错误，使用no_get=True继续
- ✅ 无法获取或创建用户（user为None）
- ✅ 插入数据时发生错误
- ✅ 自动初始化引擎

#### 关闭引擎测试
- ✅ 关闭引擎
- ✅ 关闭引擎（客户端未初始化）

#### UUID转换函数测试（已废弃）
- ✅ user_id_to_uuid函数（有效输入）
- ✅ user_id_to_uuid函数（确定性）
- ✅ user_id_to_uuid函数（不同输入产生不同输出）
- ✅ 废弃警告验证

#### 继承关系测试
- ✅ MemobaseUserProfileEngine继承自UserProfileEngineBase
- ✅ 引擎名称验证

#### 指标更新测试
- ✅ 成功操作时更新指标
- ✅ 失败操作时更新指标

### 2. UserProfileEngineFactory (`test_factory.py`)

- ✅ 创建Memobase引擎
- ✅ 创建Memobase引擎（大小写不敏感）
- ✅ 创建未知引擎提供商（抛出异常）
- ✅ 创建引擎（空提供商）
- ✅ 创建引擎（空配置）
- ✅ 创建引擎（自定义配置）

### 3. 模型测试 (`test_models.py`)

#### UserProfile模型
- ✅ 创建UserProfile实例
- ✅ 创建UserProfile实例（包含profile_data）
- ✅ UserProfile转换为字典
- ✅ UserProfile转换为字典（包含profile_data）
- ✅ UserProfile（空profile_data）

#### ProfileUpdateRequest模型
- ✅ 创建ProfileUpdateRequest实例
- ✅ ProfileUpdateRequest转换为字典
- ✅ ProfileUpdateRequest（空消息列表）

## 测试场景重点

### UUID验证
- ✅ 测试无效UUID格式时抛出ValueError
- ✅ 测试有效UUID v4格式正常处理
- ✅ 测试UUID转换逻辑（已废弃函数）

### 用户不存在场景
- ✅ 测试404错误时自动创建用户
- ✅ 测试422错误时自动创建用户
- ✅ 测试"not found"错误时自动创建用户
- ✅ 测试自动创建用户成功场景
- ✅ 测试自动创建用户失败场景（返回空画像）

### 错误处理
- ✅ 测试各种异常情况的处理
- ✅ 测试降级策略（no_get=True）
- ✅ 测试空值处理
- ✅ 测试其他错误返回空画像

## 运行测试

```bash
# 运行所有UserProfile引擎测试
pytest tests/test_engines/test_userprofile/ -v

# 运行特定测试文件
pytest tests/test_engines/test_userprofile/test_memobase_engine.py -v

# 运行测试并生成覆盖率报告
pytest tests/test_engines/test_userprofile/ --cov=app.engines.userprofile --cov-report=html --cov-report=term

# 检查覆盖率是否≥85%
pytest tests/test_engines/test_userprofile/ --cov=app.engines.userprofile --cov-report=term-missing
```

## 测试统计

- **测试文件数**: 3个
- **测试用例数**: 约50+个
- **覆盖率目标**: ≥85%
- **主要测试类**: MemobaseUserProfileEngine

## 注意事项

1. **Mock依赖**: 测试使用unittest.mock模拟Memobase SDK，不需要真实的Memobase服务
2. **UUID格式**: 所有测试都使用有效的UUID v4格式
3. **已废弃函数**: `user_id_to_uuid`函数已废弃，但仍在测试中以确保向后兼容
4. **自动创建用户**: 测试覆盖了用户不存在时自动创建用户的场景

## 测试最佳实践

1. **AAA模式**: 所有测试遵循Arrange-Act-Assert模式
2. **独立测试**: 每个测试都是独立的，不依赖其他测试
3. **Mock隔离**: 使用Mock隔离外部依赖
4. **边界测试**: 测试边界条件和异常情况
5. **文档完整**: 每个测试都有清晰的docstring说明测试目的
