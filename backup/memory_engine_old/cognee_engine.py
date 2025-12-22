"""
Cognee 记忆引擎实现

使用 Cognee Python SDK 通过 HTTP API 存储和检索记忆
"""

# 标准库
import asyncio
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

# 第三方库
try:
    from cognee_sdk import CogneeClient, SearchType
    from cognee_sdk.exceptions import (
        AuthenticationError,
        CogneeAPIError,
        NotFoundError,
        ServerError,
        TimeoutError,
        ValidationError,
    )
    COGNEE_SDK_AVAILABLE = True
except ImportError:
    COGNEE_SDK_AVAILABLE = False
    CogneeClient = None  # type: ignore
    SearchType = None  # type: ignore

# 本地库
from app.utils.logger import logger
from .base import MemoryEngineBase
from .models import Memory, MemorySearchResult, MemoryType


class CogneeMemoryEngine(MemoryEngineBase):
    """Cognee 记忆引擎适配器（使用 SDK）
    
    通过 Cognee Python SDK 调用 Cognee API 服务器存储和检索记忆
    
    Attributes:
        client: Cognee SDK 客户端实例
        _initialized: 是否已初始化
        api_url: Cognee API 服务器地址
        api_token: API 认证 Token（可选）
        user_dataset_pattern: 用户数据集命名模式
        user_node_set_pattern: 用户节点集命名模式
        assistant_node_set_pattern: AI助手节点集命名模式
        default_top_k: 默认返回结果数量
        similarity_threshold: 相似度阈值
        enable_cognify: 是否启用知识图谱构建
        enable_graph_search: 是否启用图遍历搜索
    """
    
    def __init__(self, engine_name: str, config: Dict[str, Any]):
        """初始化 Cognee 引擎
        
        Args:
            engine_name: 引擎名称
            config: 配置信息（从 YAML 读取）
        """
        # 检查依赖
        if not COGNEE_SDK_AVAILABLE:
            raise ImportError(
                "Cognee SDK is not installed. "
                "Install it with: pip install cognee-sdk"
            )
        
        super().__init__(engine_name, config)
        
        # ✅ 从配置读取 API 服务器配置
        # 优先使用环境变量，如果没有则使用配置
        self.api_url = os.getenv("COGNEE_API_URL", config.get("api_url", "http://localhost:8000"))
        if not self.api_url:
            raise ValueError("Cognee api_url is required in config or COGNEE_API_URL environment variable")
        
        self.api_token = os.getenv("COGNEE_API_TOKEN", config.get("api_token", ""))
        
        # 数据集和节点集配置
        datasets_config = config.get("datasets", {})
        self.user_dataset_pattern = datasets_config.get("user_pattern", "conversation_{user_id}")
        
        node_sets_config = config.get("node_sets", {})
        self.user_node_set_pattern = node_sets_config.get("user", "user_{user_id}_conversations")
        self.assistant_node_set_pattern = node_sets_config.get("assistant", "assistant_{user_id}_conversations")
        
        # 性能配置
        performance_config = config.get("performance", {})
        self.async_enabled = performance_config.get("async_write", True)
        self.enable_cognify = performance_config.get("enable_cognify", False)
        self.enable_graph_search = performance_config.get("enable_graph_search", False)
        self.batch_size = performance_config.get("batch_size", 10)
        
        # 搜索配置
        search_config = config.get("search", {})
        self.default_top_k = search_config.get("default_top_k", 5)
        self.similarity_threshold = search_config.get("similarity_threshold", 0.7)
        self.use_graph_completion = search_config.get("use_graph_completion", False)
        self.use_combined_context = search_config.get("use_combined_context", True)
        
        # 创建客户端（延迟初始化）
        self.client: Optional[CogneeClient] = None
        self._initialized = False
        
        logger.info(
            "Cognee memory engine initialized (SDK mode)",
            extra={
                "api_url": self.api_url,
                "async_enabled": self.async_enabled,
                "enable_cognify": self.enable_cognify,
                "enable_graph_search": self.enable_graph_search
            }
        )
    
    async def initialize(self) -> bool:
        """初始化 Cognee SDK 客户端"""
        if self._initialized and self.client:
            return True
        
        try:
            # 创建客户端
            self.client = CogneeClient(
                api_url=self.api_url,
                api_token=self.api_token if self.api_token else None,
                timeout=300.0,
                max_retries=3,
                retry_delay=1.0
            )
            
            # 健康检查
            health = await self.client.health_check()
            self._initialized = True
            
            logger.info(
                "Cognee SDK client initialized successfully",
                extra={
                    "api_url": self.api_url,
                    "health_status": health.status if hasattr(health, 'status') else "ok"
                }
            )
            return True
            
        except Exception as e:
            logger.error(f"Cognee SDK initialization failed: {e}", exc_info=True)
            if self.client:
                await self.client.close()
                self.client = None
            raise
    
    async def add_memory(self, memory: Memory) -> str:
        """添加记忆
        
        注意：异步写入由 MemoryManager 的队列机制处理，
        这里直接写入 Cognee（Worker 会调用此方法）
        """
        return await self._add_to_cognee(memory)
    
    async def _add_to_cognee(self, memory: Memory) -> str:
        """实际写入 Cognee（Worker 中调用）"""
        await self.initialize()
        
        if not self.client:
            raise RuntimeError("Cognee client not initialized")
        
        # ✅ 从配置读取数据集和节点集命名模式
        dataset_name = self.user_dataset_pattern.format(user_id=memory.user_id)
        
        if memory.memory_type == MemoryType.USER:
            node_set_pattern = self.user_node_set_pattern
        else:
            node_set_pattern = self.assistant_node_set_pattern
        
        node_set = [node_set_pattern.format(user_id=memory.user_id)]
        
        try:
            # 通过 SDK 添加到 Cognee
            result = await self.client.add(
                data=memory.content,
                dataset_name=dataset_name,
                node_set=node_set
            )
            
            # 注意：SDK 的 add 方法不直接支持 metadata 参数
            # metadata（memory_id, session_id 等）需要通过其他方式存储
            # 方案1：使用 update 方法（需要先 add 再 update，性能较差）
            # 方案2：将 metadata 编码到 content 中（不推荐，影响搜索质量）
            # 方案3：在 Cognee API 服务器端扩展支持 metadata（推荐）
            # 当前实现：暂时不存储 metadata，使用 data_id 作为 memory_id
            
            # 可选：认知化处理（异步，不阻塞）
            if self.enable_cognify:
                asyncio.create_task(self._cognify_async(dataset_name))
            
            data_id = result.data_id if result.data_id else memory.id
            logger.debug(f"Memory added to Cognee: {data_id}")
            return str(data_id) if data_id else memory.id
            
        except ValidationError as e:
            logger.error(f"Validation error adding memory: {e.message}", exc_info=False)
            raise
        except ServerError as e:
            logger.error(f"Server error adding memory: {e.message}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to add memory to Cognee: {e}", exc_info=True)
            raise
    
    async def _cognify_async(self, dataset_name: str):
        """异步认知化处理（不阻塞主流程）"""
        if not self.client:
            return
        
        try:
            result = await self.client.cognify(
                datasets=[dataset_name],
                run_in_background=True
            )
            logger.debug(f"Cognify started for dataset: {dataset_name}")
        except Exception as e:
            logger.warning(f"Cognify failed for {dataset_name}: {e}", exc_info=False)
    
    async def search_memories(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[MemorySearchResult]:
        """搜索记忆"""
        await self.initialize()
        
        if not self.client:
            raise RuntimeError("Cognee client not initialized")
        
        # ✅ 从配置读取参数
        dataset_name = self.user_dataset_pattern.format(user_id=user_id)
        top_k = limit if limit else self.default_top_k
        threshold = similarity_threshold if similarity_threshold else self.similarity_threshold
        
        # 根据配置选择搜索类型
        if self.enable_graph_search and self.use_graph_completion:
            search_type = SearchType.GRAPH_COMPLETION
        else:
            search_type = SearchType.CHUNKS  # 只使用向量搜索
        
        try:
            # 通过 SDK 执行搜索
            results = await self.client.search(
                query=query,
                search_type=search_type,
                datasets=[dataset_name],
                top_k=top_k,
                only_context=False,
                use_combined_context=self.use_combined_context
            )
            
            # 转换为标准格式
            search_results = []
            
            # SDK 返回的结果可能是列表或 CombinedSearchResult
            if isinstance(results, list):
                for result in results:
                    # 处理 SearchResult 对象
                    similarity = 1.0
                    if hasattr(result, 'score') and result.score is not None:
                        similarity = float(result.score)
                    elif hasattr(result, 'similarity') and result.similarity is not None:
                        similarity = float(result.similarity)
                    
                    # 过滤相似度低于阈值的
                    if similarity < threshold:
                        continue
                    
                    # 提取内容
                    content = ""
                    if hasattr(result, 'text') and result.text:
                        content = result.text
                    elif hasattr(result, 'content') and result.content:
                        content = result.content
                    elif isinstance(result, str):
                        content = result
                    else:
                        # 尝试从元数据中获取
                        metadata = getattr(result, 'metadata', {})
                        if isinstance(metadata, dict):
                            content = metadata.get('content', str(result))
                        else:
                            content = str(result)
                    
                    # 提取元数据
                    metadata = {}
                    if hasattr(result, 'metadata') and result.metadata:
                        metadata = result.metadata if isinstance(result.metadata, dict) else {}
                    
                    # 构建 Memory 对象
                    memory = Memory(
                        id=metadata.get('memory_id', str(uuid.uuid4())),
                        user_id=user_id,
                        session_id=metadata.get('session_id', session_id or ""),
                        memory_type=MemoryType(metadata.get('memory_type', 'user')),
                        content=content,
                        embedding=None,  # 不返回 embedding
                        importance=metadata.get('importance', 0.5),
                        metadata={k: v for k, v in metadata.items() 
                                 if k not in ['memory_id', 'session_id', 'memory_type', 'importance', 'created_at', 'expires_at']},
                        created_at=datetime.fromisoformat(metadata['created_at']) 
                            if metadata.get('created_at') else datetime.utcnow(),
                        expires_at=datetime.fromisoformat(metadata['expires_at']) 
                            if metadata.get('expires_at') else None
                    )
                    
                    search_results.append(
                        MemorySearchResult(
                            memory=memory,
                            similarity=similarity,
                            distance=1.0 - similarity if similarity < 1.0 else None
                        )
                    )
            elif hasattr(results, 'result'):
                # CombinedSearchResult 类型
                # 这种情况下，我们使用 result 字段作为内容
                content = results.result if hasattr(results, 'result') else str(results)
                metadata = results.metadata if hasattr(results, 'metadata') else {}
                
                memory = Memory(
                    id=metadata.get('memory_id', str(uuid.uuid4())),
                    user_id=user_id,
                    session_id=metadata.get('session_id', session_id or ""),
                    memory_type=MemoryType(metadata.get('memory_type', 'user')),
                    content=content,
                    embedding=None,
                    importance=metadata.get('importance', 0.5),
                    metadata={k: v for k, v in metadata.items() 
                             if k not in ['memory_id', 'session_id', 'memory_type', 'importance', 'created_at', 'expires_at']},
                    created_at=datetime.fromisoformat(metadata['created_at']) 
                        if metadata.get('created_at') else datetime.utcnow(),
                    expires_at=datetime.fromisoformat(metadata['expires_at']) 
                        if metadata.get('expires_at') else None
                )
                
                search_results.append(
                    MemorySearchResult(
                        memory=memory,
                        similarity=1.0,  # CombinedSearchResult 通常不提供相似度
                        distance=None
                    )
                )
            
            # 按相似度排序
            search_results.sort(key=lambda x: x.similarity, reverse=True)
            
            logger.debug(
                f"Search completed: {len(search_results)} results",
                extra={"query": query[:50], "user_id": user_id, "top_k": top_k}
            )
            
            return search_results[:top_k]
            
        except NotFoundError:
            logger.debug(f"No results found for query: {query[:50]}")
            return []
        except ValidationError as e:
            logger.error(f"Validation error in search: {e.message}", exc_info=False)
            return []
        except ServerError as e:
            logger.error(f"Server error in search: {e.message}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Cognee search failed: {e}", exc_info=True)
            return []
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """删除记忆"""
        await self.initialize()
        
        if not self.client:
            raise RuntimeError("Cognee client not initialized")
        
        try:
            dataset_name = self.user_dataset_pattern.format(user_id=user_id)
            
            # 需要先获取数据集 ID
            datasets = await self.client.list_datasets()
            dataset = None
            for ds in datasets:
                if ds.name == dataset_name:
                    dataset = ds
                    break
            
            if not dataset:
                logger.warning(f"Dataset not found: {dataset_name}")
                return False
            
            # 通过 SDK 删除
            try:
                memory_uuid = UUID(memory_id)
            except ValueError:
                logger.warning(f"Invalid memory_id format: {memory_id}")
                return False
            
            await self.client.delete(
                data_id=memory_uuid,
                dataset_id=dataset.id,
                mode="soft"
            )
            
            logger.debug(f"Memory deleted from Cognee: {memory_id}")
            return True
            
        except NotFoundError:
            logger.warning(f"Memory not found: {memory_id}")
            return False
        except ValidationError as e:
            logger.error(f"Validation error deleting memory: {e.message}", exc_info=False)
            return False
        except ServerError as e:
            logger.error(f"Server error deleting memory: {e.message}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}", exc_info=True)
            return False
    
    async def delete_session_memories(
        self,
        user_id: str,
        session_id: str
    ) -> int:
        """删除会话的所有记忆"""
        await self.initialize()
        
        if not self.client:
            raise RuntimeError("Cognee client not initialized")
        
        try:
            dataset_name = self.user_dataset_pattern.format(user_id=user_id)
            
            # 获取数据集 ID
            datasets = await self.client.list_datasets()
            dataset = None
            for ds in datasets:
                if ds.name == dataset_name:
                    dataset = ds
                    break
            
            if not dataset:
                logger.warning(f"Dataset not found: {dataset_name}")
                return 0
            
            # 获取数据集中的所有数据项
            data_items = await self.client.get_dataset_data(dataset.id)
            
            # 过滤出该会话的记忆
            # 注意：SDK 的 get_dataset_data 可能不包含 metadata
            # 这里简化处理，实际可能需要通过搜索来找到相关记忆
            memory_ids = []
            for item in data_items:
                # 如果 data_items 包含 metadata，可以过滤
                # 否则需要搜索来找到相关记忆
                # 这里先简化，返回 0（需要根据实际 API 调整）
                pass
            
            # 如果无法通过 data_items 获取 metadata，使用搜索
            # 注意：空查询可能不支持，使用通用查询词
            # 或者直接获取所有数据项（如果 API 支持）
            try:
                # 尝试获取所有数据项
                data_items = await self.client.get_dataset_data(dataset.id)
                # 如果 data_items 包含 metadata，可以过滤
                # 否则需要其他方式（如通过搜索）
                memory_ids = []
                # 简化处理：暂时返回 0（需要根据实际 API 调整）
                logger.warning(
                    "delete_session_memories: metadata filtering not fully supported yet",
                    extra={"user_id": user_id, "session_id": session_id}
                )
                return 0
            except Exception:
                # 如果 get_dataset_data 失败，尝试搜索
                results = await self.client.search(
                    query="*",  # 使用通配符或通用查询
                    search_type=SearchType.CHUNKS,
                    datasets=[dataset_name],
                    top_k=1000
                )
            
            # 过滤出该会话的记忆
            memory_ids = []
            if isinstance(results, list):
                for result in results:
                    metadata = getattr(result, 'metadata', {})
                    if isinstance(metadata, dict) and metadata.get('session_id') == session_id:
                        memory_id = metadata.get('memory_id')
                        if memory_id:
                            try:
                                memory_ids.append(UUID(memory_id))
                            except ValueError:
                                pass
            
            # 批量删除
            deleted_count = 0
            for memory_id in memory_ids:
                try:
                    await self.client.delete(
                        data_id=memory_id,
                        dataset_id=dataset.id,
                        mode="soft"
                    )
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete memory {memory_id}: {e}", exc_info=False)
            
            logger.info(
                f"Deleted {deleted_count} memories for session {session_id}",
                extra={"user_id": user_id, "session_id": session_id, "count": deleted_count}
            )
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete session memories: {e}", exc_info=True)
            return 0
    
    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """获取记忆统计信息"""
        await self.initialize()
        
        if not self.client:
            raise RuntimeError("Cognee client not initialized")
        
        try:
            dataset_name = self.user_dataset_pattern.format(user_id=user_id)
            
            # 获取数据集
            datasets = await self.client.list_datasets()
            dataset = None
            for ds in datasets:
                if ds.name == dataset_name:
                    dataset = ds
                    break
            
            if not dataset:
                return {
                    "user_memories": 0,
                    "assistant_memories": 0,
                    "total_memories": 0
                }
            
            # 获取数据集中的所有数据项
            data_items = await self.client.get_dataset_data(dataset.id)
            
            # 统计（简化处理，假设无法从 data_items 获取 memory_type）
            # 实际可能需要通过搜索来统计
            total_memories = len(data_items)
            
            stats = {
                "user_memories": total_memories,  # 简化处理
                "assistant_memories": 0,  # 简化处理
                "total_memories": total_memories
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}", exc_info=True)
            return {
                "user_memories": 0,
                "assistant_memories": 0,
                "total_memories": 0
            }
    
    async def batch_add_memories(self, memories: List[Memory]) -> List[str]:
        """批量添加记忆
        
        Args:
            memories: 记忆对象列表
            
        Returns:
            List[str]: 成功写入的记忆ID列表
        """
        if not memories:
            return []
        
        await self.initialize()
        
        if not self.client:
            raise RuntimeError("Cognee client not initialized")
        
        try:
            success_ids = []
            
            # 使用 SDK 的 add_batch 方法（如果支持）
            # 或者逐个添加
            for memory in memories:
                try:
                    memory_id = await self._add_to_cognee(memory)
                    success_ids.append(memory_id)
                except Exception as e:
                    logger.error(f"Failed to add memory {memory.id} in batch: {e}", exc_info=True)
                    # 继续处理其他记忆
            
            logger.info(
                f"Batch added {len(success_ids)}/{len(memories)} memories to Cognee",
                extra={"total": len(memories), "success": len(success_ids)}
            )
            
            return success_ids
            
        except Exception as e:
            logger.error(f"Failed to batch add memories: {e}", exc_info=True)
            return []
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self.initialize()
            
            if not self.client:
                return False
            
            # 健康检查
            health = await self.client.health_check()
            return health.status == "ok" if hasattr(health, 'status') else True
            
        except Exception as e:
            logger.error(f"Cognee health check failed: {e}", exc_info=True)
            return False
    
    async def close(self):
        """清理资源"""
        if self.client:
            try:
                await self.client.close()
            except Exception as e:
                logger.warning(f"Error closing Cognee client: {e}", exc_info=False)
            finally:
                self.client = None
                self._initialized = False
