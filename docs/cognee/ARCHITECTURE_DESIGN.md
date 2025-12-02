# Agent 架构设计方案

## 需求概述

构建一个多用户 Agent 系统，具备：
1. **会话记忆**：每个用户独有的对话历史记忆
2. **专业记忆**：从专业文档提取的知识，多个用户共享
3. **记忆隔离**：区分不同用户的会话记忆，同时共享专业记忆

---

## 架构设计

### 一、整体架构层次

```
┌─────────────────────────────────────────────────────────┐
│                    Agent 应用层                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 会话管理器   │  │ 记忆路由器   │  │ 响应生成器   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  Cognee 知识层                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 数据集管理   │  │ 节点集管理   │  │ 本体管理     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                   存储层                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 关系数据库   │  │ 向量数据库   │  │ 图数据库     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 二、Cognee 数据集设计

### 2.1 数据集结构

使用 **数据集（Dataset）** 作为数据隔离的基本单位：

#### 专业记忆数据集（共享）
```
数据集名称：professional_knowledge
- 医学知识：medical_knowledge
- 心理学知识：psychology_knowledge
- 其他专业领域：{domain}_knowledge

特点：
- 多个用户共享访问（read 权限）
- 只读或管理员可写
- 通过权限系统控制访问
```

#### 会话记忆数据集（用户独有）
```
数据集命名规则：conversation_{user_id}
- conversation_user_001
- conversation_user_002
- conversation_user_003

特点：
- 每个用户拥有独立的会话数据集
- 用户对自己的数据集拥有完整权限（read/write/delete）
- 完全隔离，其他用户无法访问
```

### 2.2 数据集创建策略

```python
# 专业记忆数据集（全局共享）
professional_datasets = {
    "medical_knowledge": {
        "description": "医学专业知识库",
        "permissions": {
            "default_role": "read",  # 所有用户默认可读
            "admin_role": "write"    # 管理员可写
        }
    },
    "psychology_knowledge": {
        "description": "心理学专业知识库",
        "permissions": {
            "default_role": "read",
            "admin_role": "write"
        }
    }
}

# 会话记忆数据集（按用户创建）
async def create_user_conversation_dataset(user_id: str):
    dataset_name = f"conversation_{user_id}"
    # 创建数据集，用户拥有完整权限
    await cognee.add(
        data=[],
        dataset_name=dataset_name,
        user=user
    )
    # 授予用户完整权限
    await give_user_full_permissions(user, dataset_name)
```

---

## 三、节点集（NodeSet）设计

### 3.1 节点集分类

使用 **节点集（NodeSet）** 在知识图谱中组织和标记数据：

#### 专业记忆节点集
```python
professional_node_sets = [
    "medical_concepts",      # 医学概念
    "medical_procedures",    # 医疗程序
    "medical_conditions",   # 疾病症状
    "psychology_theories",   # 心理学理论
    "psychology_methods",   # 心理治疗方法
    "psychology_assessments" # 心理评估
]
```

#### 会话记忆节点集
```python
# 每个用户的会话节点集
conversation_node_sets = [
    f"user_{user_id}_conversations",  # 对话历史
    f"user_{user_id}_preferences",    # 用户偏好
    f"user_{user_id}_context",         # 上下文信息
    f"user_{user_id}_insights"         # 用户洞察
]
```

### 3.2 节点集使用策略

```python
# 添加专业文档时使用专业节点集
await cognee.add(
    data=medical_document,
    dataset_name="medical_knowledge",
    node_set=["medical_concepts", "medical_procedures"]
)

# 添加会话内容时使用用户专属节点集
await cognee.add(
    data=conversation_text,
    dataset_name=f"conversation_{user_id}",
    node_set=[f"user_{user_id}_conversations"]
)
```

---

## 四、本体（Ontology）设计

### 4.1 本体用途

使用 **本体（Ontology）** 连接外部知识结构，增强专业记忆：

#### 医学本体
```python
medical_ontologies = [
    "SNOMED_CT",      # 医学术语本体
    "ICD-10",         # 疾病分类本体
    "UMLS"            # 统一医学语言系统
]
```

#### 心理学本体
```python
psychology_ontologies = [
    "DSM-5",          # 精神疾病诊断与统计手册
    "ICD-11_mental",  # 心理健康分类
    "PSYCHONET"       # 心理学知识网络
]
```

### 4.2 本体集成策略

```python
# 在 cognify 阶段连接本体
await cognee.cognify(
    dataset_name="medical_knowledge",
    ontology_config={
        "enabled": True,
        "ontologies": ["SNOMED_CT", "ICD-10"],
        "matching_strategy": "semantic_similarity"
    }
)
```

---

## 五、完整工作流程

### 5.1 初始化阶段

```python
# 1. 创建专业记忆数据集
async def initialize_professional_memory():
    # 医学知识
    await cognee.add(
        data=medical_documents,
        dataset_name="medical_knowledge",
        node_set=["medical_concepts", "medical_procedures"]
    )
    
    # 心理学知识
    await cognee.add(
        data=psychology_documents,
        dataset_name="psychology_knowledge",
        node_set=["psychology_theories", "psychology_methods"]
    )
    
    # 认知化处理
    await cognee.cognify(
        dataset_name="medical_knowledge",
        ontology_config={"ontologies": ["SNOMED_CT"]}
    )
    await cognee.cognify(
        dataset_name="psychology_knowledge",
        ontology_config={"ontologies": ["DSM-5"]}
    )

# 2. 为用户创建会话数据集
async def initialize_user_memory(user_id: str, user: User):
    dataset_name = f"conversation_{user_id}"
    await cognee.add(
        data=[],
        dataset_name=dataset_name,
        user=user
    )
    # 授予用户完整权限
    await give_user_full_permissions(user, dataset_name)
```

### 5.2 对话处理流程

```python
async def process_conversation(user_id: str, message: str, user: User):
    # 1. 保存用户对话到会话记忆
    conversation_dataset = f"conversation_{user_id}"
    await cognee.add(
        data=message,
        dataset_name=conversation_dataset,
        user=user,
        node_set=[f"user_{user_id}_conversations"]
    )
    
    # 2. 认知化会话内容（提取用户偏好、上下文等）
    await cognee.cognify(
        dataset_name=conversation_dataset,
        user=user
    )
    
    # 3. 混合搜索：结合专业记忆和会话记忆
    # 搜索专业记忆
    professional_results = await cognee.search(
        query_text=message,
        datasets=["medical_knowledge", "psychology_knowledge"],
        top_k=5
    )
    
    # 搜索用户会话记忆
    conversation_results = await cognee.search(
        query_text=message,
        datasets=[conversation_dataset],
        user=user,
        top_k=3
    )
    
    # 4. 生成响应（结合专业知识和用户上下文）
    response = await generate_response(
        query=message,
        professional_context=professional_results,
        conversation_context=conversation_results,
        user_id=user_id
    )
    
    # 5. 保存响应到会话记忆
    await cognee.add(
        data=response,
        dataset_name=conversation_dataset,
        user=user,
        node_set=[f"user_{user_id}_conversations"]
    )
    
    return response
```

### 5.3 搜索策略

```python
async def hybrid_search(user_id: str, query: str, user: User):
    """
    混合搜索：同时搜索专业记忆和会话记忆
    """
    conversation_dataset = f"conversation_{user_id}"
    
    # 策略1：分别搜索，然后合并
    professional_context = await cognee.search(
        query_text=query,
        datasets=["medical_knowledge", "psychology_knowledge"],
        query_type=SearchType.GRAPH_COMPLETION,
        top_k=5
    )
    
    user_context = await cognee.search(
        query_text=query,
        datasets=[conversation_dataset],
        user=user,
        query_type=SearchType.GRAPH_COMPLETION,
        top_k=3
    )
    
    # 策略2：使用节点集过滤
    results = await cognee.search(
        query_text=query,
        datasets=["medical_knowledge", "psychology_knowledge", conversation_dataset],
        node_name=[
            "medical_concepts",
            "psychology_theories",
            f"user_{user_id}_conversations"
        ],
        use_combined_context=True,
        top_k=10
    )
    
    return results
```

---

## 六、权限管理

### 6.1 权限结构

```python
# 专业记忆权限
professional_permissions = {
    "medical_knowledge": {
        "default_user": "read",      # 所有用户可读
        "admin": "write",            # 管理员可写
        "medical_expert": "write"    # 医学专家可写
    },
    "psychology_knowledge": {
        "default_user": "read",
        "admin": "write",
        "psychology_expert": "write"
    }
}

# 会话记忆权限
conversation_permissions = {
    f"conversation_{user_id}": {
        user_id: ["read", "write", "delete"],  # 用户拥有完整权限
        "system": ["read"]                      # 系统可读（用于分析）
    }
}
```

### 6.2 权限实现

```python
async def setup_permissions():
    # 为所有用户授予专业记忆的读取权限
    for dataset_name in ["medical_knowledge", "psychology_knowledge"]:
        await give_permission_to_role(
            role="default_user",
            dataset_name=dataset_name,
            permission="read"
        )
    
    # 为每个用户创建专属会话数据集并授予权限
    for user in all_users:
        dataset_name = f"conversation_{user.id}"
        await give_permission_to_user(
            user=user,
            dataset_name=dataset_name,
            permissions=["read", "write", "delete"]
        )
```

---

## 七、数据模型设计

### 7.1 专业记忆数据模型

```python
class ProfessionalMemory:
    dataset_name: str          # "medical_knowledge"
    node_sets: List[str]       # ["medical_concepts", "medical_procedures"]
    ontologies: List[str]      # ["SNOMED_CT", "ICD-10"]
    access_level: str          # "shared_read"
    last_updated: datetime
```

### 7.2 会话记忆数据模型

```python
class ConversationMemory:
    user_id: str
    dataset_name: str          # f"conversation_{user_id}"
    node_sets: List[str]       # [f"user_{user_id}_conversations"]
    access_level: str          # "user_private"
    created_at: datetime
    last_interaction: datetime
```

---

## 八、实现示例代码

### 8.1 Agent 类设计

```python
class MultiUserAgent:
    def __init__(self):
        self.professional_datasets = [
            "medical_knowledge",
            "psychology_knowledge"
        ]
    
    async def initialize(self):
        """初始化专业记忆"""
        await initialize_professional_memory()
    
    async def register_user(self, user_id: str, user: User):
        """注册新用户，创建会话数据集"""
        await initialize_user_memory(user_id, user)
    
    async def chat(self, user_id: str, message: str, user: User):
        """处理用户对话"""
        return await process_conversation(user_id, message, user)
    
    async def search_knowledge(self, query: str, user_id: str = None):
        """搜索知识库"""
        datasets = self.professional_datasets.copy()
        if user_id:
            datasets.append(f"conversation_{user_id}")
        
        return await cognee.search(
            query_text=query,
            datasets=datasets,
            use_combined_context=True
        )
```

---

## 九、优势与特点

### 9.1 数据隔离
- ✅ 每个用户的会话记忆完全隔离
- ✅ 通过数据集和权限系统实现安全隔离
- ✅ 用户无法访问其他用户的会话数据

### 9.2 知识共享
- ✅ 专业记忆在所有用户间共享
- ✅ 通过权限控制访问级别
- ✅ 支持多领域专业知识（医学、心理学等）

### 9.3 灵活扩展
- ✅ 易于添加新的专业领域
- ✅ 支持动态创建用户会话数据集
- ✅ 节点集和本体可灵活配置

### 9.4 性能优化
- ✅ 数据集级别的隔离减少搜索范围
- ✅ 节点集过滤提高搜索精度
- ✅ 混合搜索策略平衡准确性和效率

---

## 十、注意事项

1. **数据集命名规范**：使用统一的命名规则，便于管理和查找
2. **权限管理**：确保专业记忆的写权限严格控制
3. **数据同步**：专业记忆更新时，需要考虑缓存和同步机制
4. **性能考虑**：大量用户时，考虑数据集的分片策略
5. **备份策略**：会话记忆需要定期备份，专业记忆需要版本控制

---

## 十一、总结

这个架构设计充分利用了 Cognee 的核心特性：

- **数据集（Dataset）**：实现用户隔离和知识共享
- **节点集（NodeSet）**：组织和标记不同类型的记忆
- **本体（Ontology）**：连接外部专业知识结构
- **权限系统**：控制访问级别

通过这种设计，可以实现：
1. ✅ 每个用户独立的会话记忆
2. ✅ 多个用户共享的专业记忆
3. ✅ 清晰的记忆类型区分
4. ✅ 灵活的扩展和维护

