"""
记忆写入队列

使用Redis实现异步记忆写入队列。
"""

# 标准库
import json
from typing import List, Optional
import redis.asyncio as aioredis
import redis.exceptions

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from .jobs import MemoryWriteJob


class MemoryQueue:
    """记忆写入队列
    
    使用Redis List实现FIFO队列，支持批量读写操作。
    """
    
    QUEUE_KEY = "memory:write_queue"
    RETRY_QUEUE_KEY = "memory:retry_queue"
    DLQ_KEY = "memory:dlq"  # Dead Letter Queue
    
    redis_client: Optional[aioredis.Redis]  # 类型注解：可能为None（连接失败时）
    _enabled: bool  # 队列是否启用
    _connection_error_logged: bool  # 是否已记录连接错误（避免重复报错）
    _redis_url: str  # Redis连接URL（用于重连）
    
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        """初始化队列
        
        Args:
            redis_client: Redis客户端（可选，默认使用全局配置）
        """
        self._enabled = True
        self._connection_error_logged = False
        self._redis_url = ""
        
        if redis_client is None:
            # 如果没有提供redis_client，创建一个新的
            redis_url = settings.redis_url
            
            # 处理Redis密码认证
            # 如果redis_url中不包含密码，但单独设置了redis_password，需要组装URL
            if settings.redis_password and "@" not in redis_url:
                # 提取协议、主机、端口、数据库
                # redis://host:port/db -> redis://:password@host:port/db
                if redis_url.startswith("redis://"):
                    rest = redis_url[8:]  # 去掉 "redis://"
                    redis_url = f"redis://:{settings.redis_password}@{rest}"
                elif redis_url.startswith("rediss://"):
                    rest = redis_url[9:]  # 去掉 "rediss://"
                    redis_url = f"rediss://:{settings.redis_password}@{rest}"
            
            self._redis_url = redis_url
            
            self.redis_client = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.redis_max_connections,
                socket_connect_timeout=settings.redis_socket_connect_timeout,
                socket_timeout=settings.redis_socket_timeout,
                retry_on_timeout=settings.redis_retry_on_timeout,
                health_check_interval=settings.redis_health_check_interval,
                # 启用连接池健康检查
                retry_on_error=[redis.exceptions.ConnectionError, redis.exceptions.TimeoutError],
            )
        else:
            self.redis_client = redis_client
        
        logger.info(
            "Memory queue initialized",
            extra={"queue_key": self.QUEUE_KEY}
        )
    
    async def _check_and_reconnect(self) -> bool:
        """检查连接并尝试重连
        
        Returns:
            bool: 连接是否可用
        """
        if self.redis_client is None:
            return False
        
        try:
            # 使用PING命令检查连接
            await self.redis_client.ping()
            # 如果之前有连接错误，现在连接成功，重置标志
            if self._connection_error_logged:
                self._connection_error_logged = False
                self._enabled = True
                logger.info("Memory queue connection restored")
            return True
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
            # 连接失败，尝试重连
            if self._redis_url:
                try:
                    # 关闭旧连接
                    if self.redis_client:
                        await self.redis_client.close()
                    
                    # 创建新连接
                    self.redis_client = aioredis.from_url(
                        self._redis_url,
                        encoding="utf-8",
                        decode_responses=True,
                        max_connections=settings.redis_max_connections,
                        socket_connect_timeout=settings.redis_socket_connect_timeout,
                        socket_timeout=settings.redis_socket_timeout,
                        retry_on_timeout=settings.redis_retry_on_timeout,
                        health_check_interval=settings.redis_health_check_interval,
                        retry_on_error=[redis.exceptions.ConnectionError, redis.exceptions.TimeoutError],
                    )
                    
                    # 测试新连接
                    await self.redis_client.ping()
                    self._connection_error_logged = False
                    self._enabled = True
                    logger.info("Memory queue reconnected successfully")
                    return True
                except Exception as reconnect_error:
                    if not self._connection_error_logged:
                        logger.warning(
                            f"Memory queue reconnection failed: {reconnect_error}. "
                            "Memory async write will be disabled.",
                            exc_info=False
                        )
                        self._connection_error_logged = True
                        self._enabled = False
                    return False
            else:
                if not self._connection_error_logged:
                    logger.warning(
                        f"Memory queue connection check failed: {e}. "
                        "Memory async write will be disabled.",
                        exc_info=False
                    )
                    self._connection_error_logged = True
                    self._enabled = False
                return False
        except Exception as e:
            logger.error(f"Unexpected error during connection check: {e}", exc_info=True)
            return False
    
    async def push(self, job: MemoryWriteJob) -> int:
        """将任务推入队列
        
        Args:
            job: 写入任务
            
        Returns:
            int: 队列当前长度
        """
        # 如果队列已禁用（Redis连接失败），直接返回0
        if not self._enabled or self.redis_client is None:
            return 0
        
        try:
            job_json = job.model_dump_json()
            queue_length = await self.redis_client.rpush(self.QUEUE_KEY, job_json)
            
            logger.debug(
                f"Pushed memory job to queue",
                extra={
                    "job_id": job.job_id,
                    "memory_id": job.memory_id,
                    "queue_length": queue_length
                }
            )
            
            return queue_length
        except (redis.exceptions.AuthenticationError, redis.exceptions.ConnectionError) as e:
            # Redis连接/认证错误：禁用队列功能
            if not self._connection_error_logged:
                logger.warning(
                    f"Memory queue disabled due to Redis connection error: {e}. "
                    "Memory async write will be disabled.",
                    exc_info=False
                )
                self._connection_error_logged = True
                self._enabled = False
            return 0
        except Exception as e:
            logger.error(f"Failed to push job to queue: {e}", exc_info=True)
            raise
    
    async def push_batch(self, jobs: List[MemoryWriteJob]) -> int:
        """批量推入任务
        
        Args:
            jobs: 任务列表
            
        Returns:
            int: 队列当前长度
        """
        if not jobs:
            return 0
        
        # 如果队列已禁用，尝试重连
        if not self._enabled or self.redis_client is None:
            await self._check_and_reconnect()
            if not self._enabled or self.redis_client is None:
                return 0
        
        try:
            job_jsons = [job.model_dump_json() for job in jobs]
            queue_length = await self.redis_client.rpush(self.QUEUE_KEY, *job_jsons)
            
            logger.debug(
                f"Pushed {len(jobs)} memory jobs to queue",
                extra={"queue_length": queue_length}
            )
            
            return queue_length
        except (redis.exceptions.AuthenticationError, redis.exceptions.ConnectionError) as e:
            # Redis连接/认证错误：禁用队列功能
            if not self._connection_error_logged:
                logger.warning(
                    f"Memory queue disabled due to Redis connection error: {e}. "
                    "Memory async write will be disabled.",
                    exc_info=False
                )
                self._connection_error_logged = True
                self._enabled = False
            return 0
        except Exception as e:
            logger.error(f"Failed to push batch to queue: {e}", exc_info=True)
            raise
    
    async def pop(self, timeout: float = 1.0) -> Optional[MemoryWriteJob]:
        """从队列弹出一个任务（阻塞）
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            Optional[MemoryWriteJob]: 任务对象，队列为空时返回None
        """
        # 检查连接
        if not self._enabled or self.redis_client is None:
            await self._check_and_reconnect()
            if not self._enabled or self.redis_client is None:
                return None
        
        try:
            # BLPOP: 阻塞式左侧弹出
            result = await self.redis_client.blpop(self.QUEUE_KEY, timeout=timeout)
            
            if result:
                # result 是 (key, value) 元组
                _, job_json = result
                job = MemoryWriteJob.model_validate_json(job_json)
                
                logger.debug(
                    f"Popped memory job from queue",
                    extra={
                        "job_id": job.job_id,
                        "memory_id": job.memory_id
                    }
                )
                
                return job
            
            return None
        except Exception as e:
            logger.error(f"Failed to pop job from queue: {e}", exc_info=True)
            return None
    
    async def pop_batch(self, batch_size: int = 10) -> List[MemoryWriteJob]:
        """批量从队列弹出任务（非阻塞）
        
        Args:
            batch_size: 批次大小
            
        Returns:
            List[MemoryWriteJob]: 任务列表
        """
        jobs = []
        
        # 如果队列已禁用，尝试重连
        if not self._enabled or self.redis_client is None:
            await self._check_and_reconnect()
            if not self._enabled or self.redis_client is None:
                return jobs
        
        try:
            # 使用pipeline提升性能
            pipe = self.redis_client.pipeline()
            
            for _ in range(batch_size):
                pipe.lpop(self.QUEUE_KEY)
            
            results = await pipe.execute()
            
            for job_json in results:
                if job_json:
                    try:
                        job = MemoryWriteJob.model_validate_json(job_json)
                        jobs.append(job)
                    except Exception as e:
                        logger.warning(f"Failed to parse job from queue: {e}")
                        continue
            
            if jobs:
                logger.debug(
                    f"Popped {len(jobs)} memory jobs from queue",
                    extra={"batch_size": batch_size, "actual_count": len(jobs)}
                )
            
            return jobs
        except (redis.exceptions.AuthenticationError, redis.exceptions.ConnectionError) as e:
            # Redis连接/认证错误：禁用队列功能，避免持续报错
            if not self._connection_error_logged:
                logger.warning(
                    f"Memory queue disabled due to Redis connection error: {e}. "
                    "Memory async write will be disabled. Please check Redis configuration.",
                    exc_info=False
                )
                self._connection_error_logged = True
                self._enabled = False
            return jobs
        except Exception as e:
            # 其他错误：记录但不禁用队列（可能是临时错误）
            if not self._connection_error_logged:
                logger.error(f"Failed to pop batch from queue: {e}", exc_info=True)
            return jobs
    
    async def get_length(self) -> int:
        """获取队列长度
        
        Returns:
            int: 队列当前长度
        """
        if not self._enabled or self.redis_client is None:
            return 0
        
        try:
            length = await self.redis_client.llen(self.QUEUE_KEY)
            return length
        except (redis.exceptions.AuthenticationError, redis.exceptions.ConnectionError) as e:
            if not self._connection_error_logged:
                logger.warning(
                    f"Memory queue disabled due to Redis connection error: {e}",
                    exc_info=False
                )
                self._connection_error_logged = True
                self._enabled = False
            return 0
        except Exception as e:
            logger.error(f"Failed to get queue length: {e}", exc_info=True)
            return 0
    
    async def push_to_retry(self, job: MemoryWriteJob) -> int:
        """将任务推入重试队列
        
        Args:
            job: 写入任务
            
        Returns:
            int: 重试队列当前长度
        """
        if not self._enabled or self.redis_client is None:
            return 0
        
        try:
            job_json = job.model_dump_json()
            queue_length = await self.redis_client.rpush(self.RETRY_QUEUE_KEY, job_json)
            
            logger.debug(
                f"Pushed job to retry queue",
                extra={"job_id": job.job_id, "queue_length": queue_length}
            )
            
            return queue_length
        except (redis.exceptions.AuthenticationError, redis.exceptions.ConnectionError) as e:
            if not self._connection_error_logged:
                logger.warning(
                    f"Memory queue disabled due to Redis connection error: {e}",
                    exc_info=False
                )
                self._connection_error_logged = True
                self._enabled = False
            return 0
        except Exception as e:
            logger.error(f"Failed to push job to retry queue: {e}", exc_info=True)
            raise
    
    async def push_to_dlq(self, job: MemoryWriteJob, error_msg: str) -> int:
        """将任务推入死信队列
        
        Args:
            job: 写入任务
            error_msg: 错误信息
            
        Returns:
            int: 死信队列当前长度
        """
        if not self._enabled or self.redis_client is None:
            return 0
        
        try:
            job_dict = job.model_dump()
            job_dict["error"] = error_msg
            job_json = json.dumps(job_dict)
            
            queue_length = await self.redis_client.rpush(self.DLQ_KEY, job_json)
            
            logger.warning(
                f"Pushed job to dead letter queue",
                extra={
                    "job_id": job.job_id,
                    "error": error_msg,
                    "queue_length": queue_length
                }
            )
            
            return queue_length
        except (redis.exceptions.AuthenticationError, redis.exceptions.ConnectionError) as e:
            if not self._connection_error_logged:
                logger.warning(
                    f"Memory queue disabled due to Redis connection error: {e}",
                    exc_info=False
                )
                self._connection_error_logged = True
                self._enabled = False
            return 0
        except Exception as e:
            logger.error(f"Failed to push job to DLQ: {e}", exc_info=True)
            raise
    
    async def clear(self) -> None:
        """清空队列"""
        if not self._enabled or self.redis_client is None:
            return
        
        try:
            await self.redis_client.delete(self.QUEUE_KEY)
            logger.info("Memory queue cleared")
        except (redis.exceptions.AuthenticationError, redis.exceptions.ConnectionError) as e:
            if not self._connection_error_logged:
                logger.warning(
                    f"Memory queue disabled due to Redis connection error: {e}",
                    exc_info=False
                )
                self._connection_error_logged = True
                self._enabled = False
        except Exception as e:
            logger.error(f"Failed to clear queue: {e}", exc_info=True)
            raise
    
    async def close(self) -> None:
        """关闭Redis连接"""
        if self.redis_client is None:
            return
        
        try:
            await self.redis_client.close()
            logger.info("Memory queue connection closed")
        except Exception as e:
            logger.error(f"Failed to close queue connection: {e}", exc_info=True)
    
    @property
    def is_enabled(self) -> bool:
        """检查队列是否启用"""
        return self._enabled and self.redis_client is not None

