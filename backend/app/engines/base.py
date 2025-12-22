"""
通用引擎基类

为所有引擎类型（AI、Memory、Voice等）提供统一的基础接口和功能
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from app.utils.logger import logger


class EngineStatus(str, Enum):
    """引擎状态枚举"""
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STOPPED = "stopped"


class EngineType(str, Enum):
    """引擎类型枚举"""
    AI = "ai"
    MEMORY = "memory"  # 旧的记忆引擎（待删除）
    KNOWLEDGE = "knowledge"  # 知识引擎（Cognee）
    USERPROFILE = "userprofile"  # 用户画像引擎（Memobase）
    CHATMEMORY = "chatmemory"  # 会话记忆引擎（Mem0）
    TTS = "tts"
    STT = "stt"
    REALTIME = "realtime"
    TOOL = "tool"


class BaseEngine(ABC):
    """所有引擎的通用基类
    
    提供统一的接口和功能:
    - 健康检查
    - 指标收集
    - 错误处理
    - 生命周期管理
    
    Attributes:
        engine_name: 引擎名称
        engine_type: 引擎类型
        status: 引擎状态
        created_at: 创建时间
        last_health_check: 最后健康检查时间
        metrics: 引擎指标
    """
    
    def __init__(
        self,
        engine_name: str,
        engine_type: EngineType,
        **kwargs
    ):
        """初始化引擎
        
        Args:
            engine_name: 引擎名称
            engine_type: 引擎类型
            **kwargs: 其他参数
        """
        self.engine_name = engine_name
        self.engine_type = engine_type
        self.status = EngineStatus.INITIALIZING
        self.created_at = datetime.utcnow()
        self.last_health_check: Optional[datetime] = None
        self.metrics: Dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
        }
        
        logger.info(
            f"Initializing {engine_type.value} engine: {engine_name}",
            extra={
                "engine_name": engine_name,
                "engine_type": engine_type.value
            }
        )
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化引擎
        
        子类必须实现此方法，执行必要的初始化操作
        
        Returns:
            bool: 初始化是否成功
        
        Raises:
            NotImplementedError: 子类未实现此方法
        """
        raise NotImplementedError("Subclass must implement initialize()")
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查
        
        子类必须实现此方法，检查引擎是否正常运行
        
        Returns:
            bool: 引擎是否健康
        
        Raises:
            NotImplementedError: 子类未实现此方法
        """
        raise NotImplementedError("Subclass must implement health_check()")
    
    async def check_and_update_status(self) -> EngineStatus:
        """检查并更新引擎状态
        
        执行健康检查并更新引擎状态
        
        Returns:
            EngineStatus: 更新后的引擎状态
        """
        try:
            is_healthy = await self.health_check()
            self.last_health_check = datetime.utcnow()
            
            if is_healthy:
                self.status = EngineStatus.HEALTHY
            else:
                self.status = EngineStatus.DEGRADED
                logger.warning(
                    f"Engine {self.engine_name} health check failed",
                    extra={
                        "engine_name": self.engine_name,
                        "engine_type": self.engine_type.value
                    }
                )
        except Exception as e:
            self.status = EngineStatus.UNHEALTHY
            logger.error(
                f"Engine {self.engine_name} health check error: {e}",
                exc_info=True,
                extra={
                    "engine_name": self.engine_name,
                    "engine_type": self.engine_type.value
                }
            )
        
        return self.status
    
    def update_metrics(
        self,
        success: bool,
        processing_time: float
    ) -> None:
        """更新引擎指标
        
        Args:
            success: 请求是否成功
            processing_time: 处理时间（秒）
        """
        self.metrics["total_requests"] += 1
        
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
        
        self.metrics["total_processing_time"] += processing_time
        
        if self.metrics["total_requests"] > 0:
            self.metrics["average_processing_time"] = (
                self.metrics["total_processing_time"] / 
                self.metrics["total_requests"]
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取引擎指标
        
        Returns:
            Dict[str, Any]: 引擎指标字典
        """
        return {
            **self.metrics,
            "status": self.status.value,
            "engine_name": self.engine_name,
            "engine_type": self.engine_type.value,
            "created_at": self.created_at.isoformat(),
            "last_health_check": (
                self.last_health_check.isoformat() 
                if self.last_health_check 
                else None
            ),
            "uptime_seconds": (
                datetime.utcnow() - self.created_at
            ).total_seconds(),
        }
    
    def reset_metrics(self) -> None:
        """重置引擎指标"""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
        }
        logger.info(
            f"Metrics reset for engine: {self.engine_name}",
            extra={
                "engine_name": self.engine_name,
                "engine_type": self.engine_type.value
            }
        )
    
    async def shutdown(self) -> None:
        """关闭引擎
        
        执行清理操作并关闭引擎
        """
        self.status = EngineStatus.STOPPED
        logger.info(
            f"Shutting down engine: {self.engine_name}",
            extra={
                "engine_name": self.engine_name,
                "engine_type": self.engine_type.value,
                "final_metrics": self.get_metrics()
            }
        )
    
    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"<{self.__class__.__name__}("
            f"name={self.engine_name}, "
            f"type={self.engine_type.value}, "
            f"status={self.status.value})>"
        )

