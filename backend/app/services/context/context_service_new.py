"""
新的上下文服务（集成三大引擎）

使用Knowledge、UserProfile、ChatMemory三大引擎构建智能上下文
"""

# 标准库
import asyncio
from typing import Any, Dict, List, Optional

# 本地库
from app.config.config import settings
from app.engines.knowledge.factory import KnowledgeEngineFactory
from app.engines.userprofile.factory import UserProfileEngineFactory
from app.engines.chatmemory.factory import ChatMemoryEngineFactory
from app.services.context.intent_analyzer import IntentAnalyzer
from app.utils.cache_new.multi_level_cache import MultiLevelCache
from app.utils.logger import logger


class ContextServiceNew:
    """新的上下文服务
    
    集成三大人格化引擎：
    - Knowledge Engine: 知识图谱检索
    - UserProfile Engine: 用户画像获取
    - ChatMemory Engine: 会话记忆搜索
    """
    
    _instance = None
    
    def __init__(self):
        """初始化ContextService"""
        # 创建三大引擎
        self.knowledge_engine = KnowledgeEngineFactory.create_engine(
            provider=settings.knowledge_engine_provider,
            config={
                "api_url": settings.cognee_api_url,
                "api_token": settings.cognee_api_token
            }
        )
        
        self.userprofile_engine = UserProfileEngineFactory.create_engine(
            provider=settings.userprofile_engine_provider,
            config={
                "project_url": settings.memobase_project_url,
                "api_key": settings.memobase_api_key
            }
        )
        
        self.chatmemory_engine = ChatMemoryEngineFactory.create_engine(
            provider=settings.chatmemory_engine_provider,
            config={
                "api_url": settings.mem0_api_url,
                "api_key": settings.mem0_api_key
            }
        )
        
        # 创建缓存和意图分析器
        self.cache = MultiLevelCache()
        self.intent_analyzer = IntentAnalyzer()
        
        # 初始化标志
        self._initialized = False
        
        logger.info("ContextServiceNew created with three engines")
    
    @classmethod
    def get_instance(cls) -> "ContextServiceNew":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def initialize(self) -> bool:
        """初始化所有引擎
        
        Returns:
            bool: 初始化是否成功
        """
        if self._initialized:
            return True
        
        try:
            # 并行初始化三大引擎
            results = await asyncio.gather(
                self.knowledge_engine.initialize(),
                self.userprofile_engine.initialize(),
                self.chatmemory_engine.initialize(),
                return_exceptions=True
            )
            
            # 检查初始化结果
            success_count = sum(1 for r in results if r is True)
            logger.info(
                f"Engine initialization: {success_count}/3 succeeded",
                extra={
                    "knowledge": results[0],
                    "userprofile": results[1],
                    "chatmemory": results[2]
                }
            )
            
            # 至少一个引擎初始化成功即可
            self._initialized = success_count > 0
            return self._initialized
            
        except Exception as e:
            logger.error(f"Failed to initialize engines: {e}", exc_info=True)
            return False
    
    async def build_personalized_context(
        self,
        user_id: str,
        session_id: str,
        query: str,
        dataset_names: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """构建个性化上下文
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            query: 查询文本
            dataset_names: 知识库数据集名称列表
            **kwargs: 其他参数
        
        Returns:
            Dict: 个性化上下文数据
        """
        # 确保引擎已初始化
        await self.initialize()
        
        start_time = asyncio.get_event_loop().time()
        
        # 1. 分析意图
        intent = self.intent_analyzer.analyze_intent(query)
        engine_config = self.intent_analyzer.get_engine_config(intent)
        
        logger.info(
            f"Building context with intent: {intent.value}",
            extra={
                "user_id": user_id,
                "session_id": session_id,
                "query": query[:50]
            }
        )
        
        # 2. 并行调用启用的引擎
        tasks = []
        task_names = []
        
        # Knowledge Engine
        if engine_config["knowledge"]["enabled"]:
            if dataset_names:
                tasks.append(
                    self._safe_call(
                        self.knowledge_engine.search_knowledge(
                            query=query,
                            dataset_names=dataset_names,
                            top_k=engine_config["knowledge"].get("top_k", 3)
                        ),
                        timeout=0.5
                    )
                )
                task_names.append("knowledge")
        
        # UserProfile Engine
        if engine_config["userprofile"]["enabled"]:
            tasks.append(
                self._safe_call(
                    self.userprofile_engine.get_profile(
                        user_id=user_id,
                        max_token_size=engine_config["userprofile"].get("max_tokens", 300)
                    ),
                    timeout=0.3
                )
            )
            task_names.append("userprofile")
        
        # ChatMemory Engine
        if engine_config["chatmemory"]["enabled"]:
            tasks.append(
                self._safe_call(
                    self.chatmemory_engine.search_memories(
                        query=query,
                        user_id=user_id,
                        session_id=session_id,
                        top_k=engine_config["chatmemory"].get("top_k", 5)
                    ),
                    timeout=0.4
                )
            )
            task_names.append("chatmemory")
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 3. 处理结果
        context = {
            "intent": intent.value,
            "knowledge": [],
            "profile": {"user_id": user_id, "profile_text": "", "token_size": 0},
            "memories": []
        }
        
        for i, (task_name, result) in enumerate(zip(task_names, results)):
            if isinstance(result, Exception):
                logger.warning(f"{task_name} failed: {result}")
                continue
            
            if task_name == "knowledge":
                context["knowledge"] = result or []
            elif task_name == "userprofile":
                context["profile"] = result or context["profile"]
            elif task_name == "chatmemory":
                context["memories"] = result or []
        
        # 记录性能
        processing_time = asyncio.get_event_loop().time() - start_time
        logger.info(
            f"Context built successfully",
            extra={
                "intent": intent.value,
                "knowledge_count": len(context["knowledge"]),
                "has_profile": bool(context["profile"]["profile_text"]),
                "memory_count": len(context["memories"]),
                "processing_time": f"{processing_time:.3f}s"
            }
        )
        
        return context
    
    async def update_user_data(
        self,
        user_id: str,
        session_id: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, bool]:
        """更新用户数据
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            messages: 消息列表
            **kwargs: 其他参数
        
        Returns:
            Dict: 更新结果
        """
        # 确保引擎已初始化
        await self.initialize()
        
        # 并行更新UserProfile和ChatMemory
        tasks = [
            self._safe_call(
                self.userprofile_engine.update_profile(user_id, messages),
                timeout=1.0
            ),
            self._safe_call(
                self.chatmemory_engine.add_memory(user_id, session_id, messages),
                timeout=1.0
            )
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "userprofile_updated": results[0] is True,
            "chatmemory_updated": not isinstance(results[1], Exception)
        }
    
    async def _safe_call(self, coro, timeout: float):
        """安全调用协程（带超时和异常处理）
        
        Args:
            coro: 协程对象
            timeout: 超时时间（秒）
        
        Returns:
            协程结果或None
        """
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Operation timeout after {timeout}s")
            return None
        except Exception as e:
            logger.error(f"Operation failed: {e}", exc_info=True)
            return None
    
    async def build_context(
        self,
        user_id: str,
        session_id: str,
        current_message: str,
        personality_config: Any,
        **kwargs
    ) -> Any:
        """构建上下文（兼容旧接口）
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            current_message: 当前消息
            personality_config: 人格配置
            **kwargs: 其他参数
        
        Returns:
            ContextBundle: 上下文包（简化版）
        """
        # 获取数据集名称
        dataset_names = kwargs.get("dataset_names", ["default"])
        
        # 调用新的build_personalized_context
        context = await self.build_personalized_context(
            user_id=user_id,
            session_id=session_id,
            query=current_message,
            dataset_names=dataset_names
        )
        
        # 转换为兼容的ContextBundle格式
        from app.schemas.context import ContextBundle
        
        return ContextBundle(
            recent_messages=[],  # 由调用方处理
            history_summaries=[],  # 暂不支持
            memories=context.get("memories", []),
            user_profile=context.get("profile", {}),
            token_usage={"total": 0},  # 后续计算
            metadata={
                "intent": context.get("intent"),
                "knowledge": context.get("knowledge", [])
            }
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            Dict: 健康状态
        """
        # 并行检查三大引擎
        tasks = [
            self.knowledge_engine.health_check(),
            self.userprofile_engine.health_check(),
            self.chatmemory_engine.health_check()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "knowledge": results[0] if not isinstance(results[0], Exception) else False,
            "userprofile": results[1] if not isinstance(results[1], Exception) else False,
            "chatmemory": results[2] if not isinstance(results[2], Exception) else False,
            "overall": any(r is True for r in results)
        }

