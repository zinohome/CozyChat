"""
记忆写入Worker

后台Worker，循环从Redis队列读取任务并批量写入Qdrant。
"""

# 标准库
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict, List

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from .queue import MemoryQueue
from .jobs import MemoryWriteJob, MemoryWriteJobStatus
from .models import Memory, MemoryType
from .qdrant_engine import QdrantMemoryEngine
from .deduplicator import MemoryDeduplicator


class MemoryWorker:
    """记忆写入Worker
    
    从队列批量读取记忆写入任务，并异步写入到Qdrant。
    支持批量写入、错误重试和去重。
    """
    
    MAX_RETRY_COUNT = 3
    RETRY_DELAY = 5  # 秒
    
    def __init__(
        self,
        queue: MemoryQueue,
        engine: QdrantMemoryEngine,
        batch_size: Optional[int] = None,
        poll_interval: float = 1.0
    ):
        """初始化Worker
        
        Args:
            queue: 记忆写入队列
            engine: Qdrant引擎
            batch_size: 批次大小（可选，默认从配置读取）
            poll_interval: 轮询间隔（秒）
        """
        self.queue = queue
        self.engine = engine
        self.batch_size = batch_size or settings.memory_batch_size
        self.poll_interval = poll_interval
        self.running = False
        self.task: Optional[asyncio.Task] = None
        
        # 去重器
        self.deduplicator = MemoryDeduplicator(engine=engine)
        self.dedup_enabled = settings.memory_dedup_enabled
        self.dedup_mode = settings.memory_dedup_mode
        
        # 统计信息
        self.stats = {
            "total_processed": 0,
            "total_success": 0,
            "total_failed": 0,
            "last_batch_time": None
        }
        
        logger.info(
            "Memory worker initialized",
            extra={
                "batch_size": self.batch_size,
                "poll_interval": poll_interval,
                "dedup_enabled": self.dedup_enabled,
                "dedup_mode": self.dedup_mode
            }
        )
    
    async def start(self) -> None:
        """启动Worker"""
        if self.running:
            logger.warning("Memory worker is already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._run())
        logger.info("Memory worker started")
    
    async def stop(self, wait_for_completion: bool = True) -> None:
        """停止Worker
        
        Args:
            wait_for_completion: 是否等待当前批次完成
        """
        if not self.running:
            return
        
        self.running = False
        
        if self.task and not self.task.done():
            if wait_for_completion:
                # 等待当前任务完成
                await asyncio.wait_for(self.task, timeout=60.0)
            else:
                # 立即取消
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
        
        logger.info(
            "Memory worker stopped",
            extra={"stats": self.stats}
        )
    
    async def _run(self) -> None:
        """主循环"""
        logger.info("Memory worker main loop started")
        
        while self.running:
            try:
                # 批量读取任务
                jobs = await self.queue.pop_batch(self.batch_size)
                
                if jobs:
                    await self._process_batch(jobs)
                else:
                    # 队列为空，等待一段时间
                    await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in worker main loop: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval)
        
        logger.info("Memory worker main loop stopped")
    
    async def _process_batch(self, jobs: List[MemoryWriteJob]) -> None:
        """处理一批任务
        
        Args:
            jobs: 任务列表
        """
        start_time = datetime.utcnow()
        
        logger.info(
            f"Processing memory batch",
            extra={"batch_size": len(jobs)}
        )
        
        try:
            # 转换为Memory对象
            memories = []
            job_map = {}  # memory_id -> job
            
            for job in jobs:
                memory = self._job_to_memory(job)
                memories.append(memory)
                job_map[memory.id] = job
            
            # 批量写入
            success_ids = await self._batch_write_memories(memories)
            
            # 更新统计
            self.stats["total_processed"] += len(jobs)
            self.stats["total_success"] += len(success_ids)
            self.stats["total_failed"] += (len(jobs) - len(success_ids))
            self.stats["last_batch_time"] = start_time
            
            # 处理失败的任务
            failed_jobs = [job for job in jobs if job.memory_id not in success_ids]
            for job in failed_jobs:
                await self._handle_failed_job(job, "Write failed")
            
            # 异步去重（如果启用）
            if self.dedup_enabled and self.dedup_mode == "async":
                asyncio.create_task(self._async_deduplicate())
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"Memory batch processed",
                extra={
                    "batch_size": len(jobs),
                    "success_count": len(success_ids),
                    "failed_count": len(failed_jobs),
                    "duration_seconds": duration
                }
            )
        except Exception as e:
            logger.error(f"Failed to process batch: {e}", exc_info=True)
            # 所有任务都失败，推入重试队列
            for job in jobs:
                await self._handle_failed_job(job, str(e))
    
    def _job_to_memory(self, job: MemoryWriteJob) -> Memory:
        """将Job转换为Memory对象
        
        Args:
            job: 写入任务
            
        Returns:
            Memory: 记忆对象
        """
        memory_type = MemoryType.USER if job.role == "user" else MemoryType.ASSISTANT
        
        return Memory(
            id=job.memory_id,
            user_id=job.user_id,
            session_id=job.session_id,
            memory_type=memory_type,
            content=job.content,
            importance=job.importance,
            metadata=job.metadata,
            created_at=job.created_at
        )
    
    async def _batch_write_memories(self, memories: List[Memory]) -> List[str]:
        """批量写入记忆
        
        Args:
            memories: 记忆列表
            
        Returns:
            List[str]: 成功写入的记忆ID列表
        """
        if not memories:
            return []
        
        try:
            # 使用批量写入接口
            success_ids = await self.engine.batch_add_memories(memories)
            
            logger.debug(
                f"Batch write completed",
                extra={
                    "total_memories": len(memories),
                    "success_count": len(success_ids)
                }
            )
            
            return success_ids
            
        except Exception as e:
            logger.error(f"Batch write failed, falling back to individual writes: {e}", exc_info=True)
            
            # 降级：逐个写入
            success_ids = []
            for memory in memories:
                try:
                    memory_id = await self.engine.add_memory(memory)
                    success_ids.append(memory_id)
                except Exception as e2:
                    logger.error(f"Failed to write memory {memory.id}: {e2}")
            
            return success_ids
    
    async def _handle_failed_job(self, job: MemoryWriteJob, error_msg: str) -> None:
        """处理失败的任务
        
        Args:
            job: 失败的任务
            error_msg: 错误信息
        """
        # 检查重试次数
        retry_count = job.metadata.get("retry_count", 0)
        
        if retry_count < self.MAX_RETRY_COUNT:
            # 重试
            job.metadata["retry_count"] = retry_count + 1
            job.status = MemoryWriteJobStatus.PENDING
            await self.queue.push_to_retry(job)
            
            logger.debug(
                f"Job pushed to retry queue",
                extra={
                    "job_id": job.job_id,
                    "retry_count": retry_count + 1,
                    "error": error_msg
                }
            )
        else:
            # 超过重试次数，推入死信队列
            job.status = MemoryWriteJobStatus.FAILED
            await self.queue.push_to_dlq(job, error_msg)
            
            logger.error(
                f"Job failed after {self.MAX_RETRY_COUNT} retries",
                extra={
                    "job_id": job.job_id,
                    "error": error_msg
                }
            )
    
    async def _async_deduplicate(self) -> None:
        """异步去重任务
        
        根据配置的阈值触发去重。
        """
        try:
            # 检查是否需要去重
            should_deduplicate = False
            reason = ""
            
            # 1. 检查内容计数阈值
            # TODO: 实现内容相似度聚类统计
            # 简化实现：定期触发
            content_threshold = settings.memory_dedup_content_threshold
            
            # 2. 检查存储利用率阈值（简化实现：检查队列长度）
            queue_length = await self.queue.get_length()
            if queue_length > content_threshold * 10:
                should_deduplicate = True
                reason = f"Queue length ({queue_length}) exceeds threshold"
            
            # 3. 定期触发（基于时间间隔）
            # 简化实现：每处理N个批次后触发一次
            if self.stats["total_processed"] % (self.batch_size * 10) == 0:
                should_deduplicate = True
                reason = "Periodic deduplication trigger"
            
            if should_deduplicate:
                logger.info(
                    f"Triggering async deduplication: {reason}",
                    extra={"queue_length": queue_length}
                )
                
                # 执行批量去重
                # TODO: 根据实际需求选择去重范围（用户/会话/类型）
                # 这里简化为跨用户去重（在实际应用中应该按用户分别去重）
                stats = await self.deduplicator.batch_deduplicate(
                    user_id="*",  # 特殊标记，表示所有用户（需要在deduplicator中处理）
                    session_id=None,
                    memory_type=None
                )
                
                logger.info(
                    f"Async deduplication completed",
                    extra={"dedup_stats": stats}
                )
            
        except Exception as e:
            logger.error(f"Async deduplication failed: {e}", exc_info=True)
    
    def get_stats(self) -> Dict:
        """获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            **self.stats,
            "running": self.running,
            "queue_length": asyncio.create_task(self.queue.get_length())
        }

