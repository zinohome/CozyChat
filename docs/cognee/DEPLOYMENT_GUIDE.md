# Agent 部署指南

## 一、环境准备

### 1.1 安装依赖

```bash
# 安装 Cognee
pip install cognee

# 安装其他依赖
pip install fastapi uvicorn sqlalchemy
```

### 1.2 环境变量配置

创建 `.env` 文件：

```env
# LLM 配置（必需）
LLM_API_KEY=your_openai_api_key
LLM_PROVIDER=openai
LLM_MODEL=gpt-4

# 数据库配置
# 向量数据库（默认使用 LanceDB）
VECTOR_DB_PROVIDER=lancedb

# 图数据库（默认使用 Kuzu）
GRAPH_DATABASE_PROVIDER=kuzu

# 关系数据库（SQLite 默认，生产环境建议 PostgreSQL）
DATABASE_URL=sqlite:///./cognee.db

# 用户认证（可选）
DEFAULT_USER_EMAIL=admin@example.com
DEFAULT_USER_PASSWORD=admin123
```

---

## 二、数据集初始化脚本

创建 `initialize_datasets.py`：

```python
"""
初始化专业记忆数据集
"""
import asyncio
import cognee
from cognee.modules.users.methods import get_default_user
from cognee.modules.users.permissions.methods import give_permission_on_dataset


async def initialize_professional_datasets():
    """初始化专业记忆数据集"""
    await cognee.setup()
    
    # 获取默认用户（管理员）
    admin_user = await get_default_user()
    
    # 专业数据集列表
    professional_datasets = [
        {
            "name": "medical_knowledge",
            "description": "医学专业知识库",
            "node_sets": ["medical_concepts", "medical_procedures", "medical_conditions"]
        },
        {
            "name": "psychology_knowledge",
            "description": "心理学专业知识库",
            "node_sets": ["psychology_theories", "psychology_methods", "psychology_assessments"]
        }
    ]
    
    for dataset_info in professional_datasets:
        dataset_name = dataset_info["name"]
        
        # 创建数据集（通过添加空数据）
        try:
            await cognee.add(
                data=[],
                dataset_name=dataset_name
            )
            print(f"✅ 数据集 '{dataset_name}' 已创建")
        except Exception as e:
            print(f"⚠️  数据集 '{dataset_name}' 可能已存在: {e}")
        
        # 授予管理员写权限
        try:
            await give_permission_on_dataset(
                principal=admin_user,
                dataset_name=dataset_name,
                permission="write"
            )
            print(f"✅ 已授予管理员对 '{dataset_name}' 的写权限")
        except Exception as e:
            print(f"⚠️  权限设置时出错: {e}")
    
    print("\n🎉 专业记忆数据集初始化完成！")


if __name__ == "__main__":
    asyncio.run(initialize_professional_datasets())
```

---

## 三、数据导入脚本

创建 `import_professional_documents.py`：

```python
"""
导入专业文档到知识库
"""
import asyncio
import cognee
from pathlib import Path


async def import_medical_documents():
    """导入医学文档"""
    medical_docs_dir = Path("./data/medical")
    
    if not medical_docs_dir.exists():
        print(f"⚠️  目录不存在: {medical_docs_dir}")
        return
    
    # 获取所有文档文件
    doc_files = list(medical_docs_dir.glob("*.pdf")) + \
                list(medical_docs_dir.glob("*.txt")) + \
                list(medical_docs_dir.glob("*.md"))
    
    print(f"📚 找到 {len(doc_files)} 个医学文档")
    
    for doc_file in doc_files:
        try:
            await cognee.add(
                data=str(doc_file),
                dataset_name="medical_knowledge",
                node_set=["medical_concepts", "medical_procedures"]
            )
            print(f"✅ 已导入: {doc_file.name}")
        except Exception as e:
            print(f"❌ 导入失败 {doc_file.name}: {e}")
    
    # 认知化处理
    print("\n🔄 开始认知化处理...")
    await cognee.cognify(dataset_name="medical_knowledge")
    print("✅ 医学知识库处理完成")


async def import_psychology_documents():
    """导入心理学文档"""
    psychology_docs_dir = Path("./data/psychology")
    
    if not psychology_docs_dir.exists():
        print(f"⚠️  目录不存在: {psychology_docs_dir}")
        return
    
    doc_files = list(psychology_docs_dir.glob("*.pdf")) + \
                list(psychology_docs_dir.glob("*.txt")) + \
                list(psychology_docs_dir.glob("*.md"))
    
    print(f"📚 找到 {len(doc_files)} 个心理学文档")
    
    for doc_file in doc_files:
        try:
            await cognee.add(
                data=str(doc_file),
                dataset_name="psychology_knowledge",
                node_set=["psychology_theories", "psychology_methods"]
            )
            print(f"✅ 已导入: {doc_file.name}")
        except Exception as e:
            print(f"❌ 导入失败 {doc_file.name}: {e}")
    
    # 认知化处理
    print("\n🔄 开始认知化处理...")
    await cognee.cognify(dataset_name="psychology_knowledge")
    print("✅ 心理学知识库处理完成")


async def main():
    await cognee.setup()
    
    print("=" * 50)
    print("开始导入专业文档")
    print("=" * 50)
    
    await import_medical_documents()
    print("\n" + "=" * 50)
    await import_psychology_documents()
    
    print("\n" + "=" * 50)
    print("🎉 所有文档导入完成！")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 四、API 服务

创建 `api_server.py`：

```python
"""
FastAPI 服务，提供 Agent API
"""
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import cognee
from cognee.modules.users.models import User
from cognee.modules.users.methods import get_authenticated_user
from agent_implementation_example import MultiUserAgent

app = FastAPI(title="Multi-User Agent API")

# 全局 Agent 实例
agent = None


@app.on_event("startup")
async def startup():
    """启动时初始化 Agent"""
    global agent
    agent = MultiUserAgent()
    await agent.initialize()
    print("✅ Agent 已初始化")


# 请求模型
class ChatRequest(BaseModel):
    message: str
    user_id: str


class AddKnowledgeRequest(BaseModel):
    content: str
    domain: str  # "medical" 或 "psychology"
    node_sets: Optional[List[str]] = None


class SearchRequest(BaseModel):
    query: str
    domains: Optional[List[str]] = None
    top_k: int = 5


# API 端点
@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    user: User = Depends(get_authenticated_user)
):
    """处理用户对话"""
    try:
        response = await agent.chat(
            user_id=request.user_id,
            message=request.message,
            user=user
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/users/register")
async def register_user(
    user_id: str,
    email: str,
    password: str
):
    """注册新用户"""
    try:
        user = await agent.register_user(
            user_id=user_id,
            email=email,
            password=password
        )
        return {"user_id": str(user.id), "email": user.email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/knowledge/add")
async def add_knowledge(
    request: AddKnowledgeRequest,
    user: User = Depends(get_authenticated_user)
):
    """添加专业知识（需要管理员权限）"""
    try:
        await agent.add_professional_knowledge(
            data=request.content,
            domain=request.domain,
            node_sets=request.node_sets
        )
        return {"status": "success", "message": f"已添加 {request.domain} 知识"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/knowledge/search")
async def search_knowledge(request: SearchRequest):
    """搜索专业知识"""
    try:
        results = await agent.search_professional_knowledge(
            query=request.query,
            domains=request.domains,
            top_k=request.top_k
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    """健康检查"""
    return {"status": "healthy", "agent_initialized": agent is not None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 五、部署步骤

### 5.1 本地开发环境

```bash
# 1. 克隆项目
git clone <your-repo>
cd usecognee

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key

# 5. 初始化数据集
python initialize_datasets.py

# 6. 导入专业文档（可选）
python import_professional_documents.py

# 7. 启动 API 服务
python api_server.py
```

### 5.2 生产环境部署

#### 使用 Docker

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "api_server.py"]
```

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  agent-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LLM_API_KEY=${LLM_API_KEY}
      - DATABASE_URL=postgresql://user:password@db:5432/cognee
      - VECTOR_DB_PROVIDER=lancedb
      - GRAPH_DATABASE_PROVIDER=kuzu
    volumes:
      - ./data:/app/data
      - ./storage:/app/storage
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=cognee
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 六、测试

创建 `test_agent.py`：

```python
"""
测试 Agent 功能
"""
import asyncio
from agent_implementation_example import MultiUserAgent


async def test_agent():
    """测试 Agent 基本功能"""
    
    agent = MultiUserAgent()
    await agent.initialize()
    
    # 测试1: 注册用户
    print("测试1: 注册用户")
    user1 = await agent.register_user(
        user_id="test_user_001",
        email="test1@example.com",
        password="test123"
    )
    print(f"✅ 用户注册成功: {user1.email}")
    
    # 测试2: 添加专业知识
    print("\n测试2: 添加专业知识")
    await agent.add_professional_knowledge(
        data="高血压是常见的心血管疾病，需要长期管理。",
        domain="medical"
    )
    print("✅ 专业知识添加成功")
    
    # 测试3: 搜索专业知识
    print("\n测试3: 搜索专业知识")
    results = await agent.search_professional_knowledge(
        query="高血压",
        domains=["medical"],
        top_k=3
    )
    print(f"✅ 搜索结果: {len(results)} 条")
    
    # 测试4: 用户对话
    print("\n测试4: 用户对话")
    response = await agent.chat(
        user_id="test_user_001",
        message="什么是高血压？",
        user=user1
    )
    print(f"✅ Agent 响应: {response[:100]}...")
    
    # 测试5: 搜索用户会话记忆
    print("\n测试5: 搜索用户会话记忆")
    conv_results = await agent.search_user_conversation(
        user_id="test_user_001",
        query="高血压",
        user=user1,
        top_k=2
    )
    print(f"✅ 会话记忆搜索结果: {len(conv_results)} 条")
    
    print("\n🎉 所有测试通过！")


if __name__ == "__main__":
    asyncio.run(test_agent())
```

---

## 七、监控和维护

### 7.1 数据集状态检查

```python
async def check_datasets_status():
    """检查数据集状态"""
    from cognee.modules.data.methods import get_all_datasets
    
    datasets = await get_all_datasets()
    
    for dataset in datasets:
        print(f"数据集: {dataset.name}")
        print(f"  - ID: {dataset.id}")
        print(f"  - 创建时间: {dataset.created_at}")
        print(f"  - 文档数量: {dataset.document_count}")
        print()
```

### 7.2 用户数据集清理

```python
async def cleanup_inactive_users(days_inactive: int = 90):
    """清理不活跃用户的会话数据集"""
    # 实现逻辑：查找超过 N 天未活动的用户，清理其会话数据集
    pass
```

---

## 八、性能优化建议

1. **数据集分片**：当用户数量很大时，考虑按用户ID范围分片
2. **缓存策略**：对专业记忆的搜索结果进行缓存
3. **异步处理**：使用后台任务处理大量文档导入
4. **索引优化**：定期优化向量数据库和图数据库索引

---

## 九、安全注意事项

1. **API 密钥管理**：使用环境变量或密钥管理服务
2. **用户认证**：实现 JWT 或 OAuth2 认证
3. **权限验证**：每次操作前验证用户权限
4. **数据加密**：敏感数据加密存储
5. **访问日志**：记录所有数据访问操作

---

## 十、故障排查

### 常见问题

1. **数据集创建失败**
   - 检查数据库连接
   - 验证用户权限

2. **搜索无结果**
   - 确认数据已认知化（cognify）
   - 检查数据集名称是否正确

3. **权限错误**
   - 验证用户是否有访问权限
   - 检查权限配置

---

## 总结

通过以上步骤，您可以成功部署一个支持多用户会话记忆和专业记忆共享的 Agent 系统。

