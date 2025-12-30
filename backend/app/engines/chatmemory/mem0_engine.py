"""
Mem0会话记忆引擎实现

通过HTTP API连接Mem0后端服务，实现会话记忆管理
"""

# 标准库
import time
from typing import Any, Dict, List, Optional

# 第三方库
import httpx

# 本地库
from app.engines.chatmemory.base import ChatMemoryEngineBase
from app.utils.logger import logger


class Mem0ChatMemoryEngine(ChatMemoryEngineBase):
    """Mem0会话记忆引擎实现
    
    使用HTTP API连接Mem0后端服务，提供：
    - 会话记忆搜索（当前会话+跨会话）
    - 会话记忆添加
    - 多层记忆管理
    
    Attributes:
        api_url: Mem0 API服务地址
        api_key: Mem0 API Key（可选）
        client: httpx AsyncClient实例
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化Mem0引擎
        
        Args:
            config: 引擎配置，包含：
                - api_url: API服务地址
                - api_key: API Key（可选）
        """
        super().__init__(engine_name="mem0", config=config)
        
        self.api_url = config.get("api_url", "http://localhost:8888").rstrip('/')
        self.api_key = config.get("api_key")
        self.client: Optional[httpx.AsyncClient] = None
    
    async def initialize(self) -> bool:
        """初始化Mem0客户端
        
        Returns:
            bool: 初始化是否成功
        """
        if self._initialized:
            return True
        
        try:
            start_time = time.time()
            
            # 创建httpx异步客户端
            self.client = httpx.AsyncClient(
                base_url=self.api_url,
                timeout=30.0
            )
            
            # 执行健康检查
            is_healthy = await self.health_check()
            
            if is_healthy:
                self._initialized = True
                processing_time = time.time() - start_time
                self.update_metrics(success=True, processing_time=processing_time)
                
                logger.info(
                    f"Mem0 chatmemory engine initialized successfully",
                    extra={
                        "api_url": self.api_url,
                        "processing_time": processing_time
                    }
                )
            else:
                logger.error("Mem0 health check failed during initialization")
            
            return is_healthy
            
        except Exception as e:
            logger.error(
                f"Failed to initialize Mem0 engine: {e}",
                exc_info=True,
                extra={"api_url": self.api_url}
            )
            return False
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 引擎是否健康
        """
        if not self.client:
            return False
        
        try:
            # 尝试访问API根路径
            response = await self.client.get("/")
            is_healthy = response.status_code < 500
            
            if is_healthy:
                logger.debug("Mem0 health check passed")
            else:
                logger.warning(
                    f"Mem0 health check failed: status {response.status_code}",
                    extra={"status_code": response.status_code}
                )
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"Mem0 health check error: {e}", exc_info=True)
            return False
    
    async def search_memories(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        top_k: int = 5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """搜索会话记忆
        
        并发获取当前会话记忆和跨会话记忆
        
        Args:
            query: 查询文本
            user_id: 用户ID
            session_id: 会话ID
            top_k: 返回结果数量
            **kwargs: 其他参数
        
        Returns:
            List[Dict]: 记忆搜索结果列表
        """
        # 确保引擎已初始化
        await self.initialize()
        
        start_time = time.time()
        
        try:
            import asyncio
            
            # 并发获取当前会话记忆和跨会话记忆
            tasks = [
                # 跨会话记忆（只用user_id）
                self.client.post(  # type: ignore[union-attr]
                    "/api/v1/search",
                    json={
                        "query": query,
                        "user_id": user_id
                    }
                )
            ]
            
            # 如果有session_id，也获取当前会话记忆
            if session_id:
                tasks.insert(0, self.client.post(  # type: ignore[union-attr]
                    "/api/v1/search",
                    json={
                        "query": query,
                        "user_id": user_id,
                        "agent_id": session_id
                    }
                ))
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            memories = []
            
            # 处理当前会话记忆（如果有）
            if session_id and len(responses) > 1:
                current_resp = responses[0]
                if not isinstance(current_resp, Exception):
                    current_resp.raise_for_status()
                    current_data = current_resp.json()
                    memories.extend(
                        self._parse_memories(current_data, session="current", limit=top_k)
                    )
            
            # 处理跨会话记忆
            cross_resp = responses[-1]
            if not isinstance(cross_resp, Exception):
                cross_resp.raise_for_status()
                cross_data = cross_resp.json()
                memories.extend(
                    self._parse_memories(cross_data, session="cross", limit=max(top_k - len(memories), 3))
                )
            
            # 按时间排序并限制数量
            memories.sort(key=lambda x: x.get("created_at", "") or "", reverse=True)
            memories = memories[:top_k]
            
            # 更新指标
            processing_time = time.time() - start_time
            self.update_metrics(success=True, processing_time=processing_time)
            
            logger.info(
                f"Memory search completed",
                extra={
                    "query": query[:50],
                    "user_id": user_id,
                    "session_id": session_id,
                    "results_count": len(memories),
                    "processing_time": processing_time
                }
            )
            
            return memories
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.update_metrics(success=False, processing_time=processing_time)
            
            logger.error(
                f"Memory search error: {e}",
                exc_info=True,
                extra={
                    "query": query[:50],
                    "user_id": user_id,
                    "session_id": session_id
                }
            )
            
            return []
    
    def _parse_memories(
        self,
        data: Any,
        session: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """解析记忆数据
        
        Args:
            data: Mem0 API返回的原始数据
            session: 会话类型（current/cross）
            limit: 限制数量
        
        Returns:
            List[Dict]: 解析后的记忆列表
        """
        memories = []
        
        if isinstance(data, list):
            for item in data[:limit]:
                memories.append({
                    "memory": item.get("memory", item.get("content", str(item))),
                    "score": item.get("score", 1.0),
                    "created_at": item.get("created_at", item.get("timestamp")),
                    "session": session
                })
        elif isinstance(data, dict):
            if "results" in data:
                for item in data["results"][:limit]:
                    memories.append({
                        "memory": item.get("memory", item.get("content", str(item))),
                        "score": item.get("score", 1.0),
                        "created_at": item.get("created_at", item.get("timestamp")),
                        "session": session
                    })
            else:
                # 单个结果
                memories.append({
                    "memory": data.get("memory", data.get("content", str(data))),
                    "score": data.get("score", 1.0),
                    "created_at": data.get("created_at", data.get("timestamp")),
                    "session": session
                })
        
        return memories
    
    async def add_memory(
        self,
        user_id: str,
        session_id: str,
        messages: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """添加会话记忆
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            messages: 消息列表
            metadata: 元数据
            **kwargs: 其他参数
        
        Returns:
            str: 记忆ID
        """
        # 确保引擎已初始化
        await self.initialize()
        
        start_time = time.time()
        
        try:
            # 转换消息格式
            mem0_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    if "role" in msg and "content" in msg:
                        mem0_messages.append(msg)
                    elif "message" in msg:
                        mem0_messages.append({
                            "role": msg.get("role", "user"),
                            "content": msg["message"]
                        })
            
            # 构建请求
            payload = {
                "messages": mem0_messages,
                "user_id": user_id,
                "agent_id": session_id
            }
            if metadata:
                payload["metadata"] = metadata
            
            # 发送请求
            response = await self.client.post("/api/v1/memories", json=payload)  # type: ignore[union-attr]
            response.raise_for_status()
            
            result = response.json()
            
            # 更新指标
            processing_time = time.time() - start_time
            self.update_metrics(success=True, processing_time=processing_time)
            
            logger.info(
                f"Memory added successfully",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "message_count": len(messages),
                    "processing_time": processing_time
                }
            )
            
            # 返回记忆ID（如果有）
            if isinstance(result, dict):
                return str(result.get("id", "success"))
            return "success"
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.update_metrics(success=False, processing_time=processing_time)
            
            logger.error(
                f"Failed to add memory: {e}",
                exc_info=True,
                extra={"user_id": user_id, "session_id": session_id}
            )
            raise
    
    async def shutdown(self) -> None:
        """关闭引擎"""
        if self.client:
            await self.client.aclose()
            self.client = None
        
        await super().shutdown()

