"""
用户画像引擎基类

定义用户画像引擎的统一接口，用于用户长期记忆和特征管理
"""

# 标准库
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# 本地库
from app.engines.base import BaseEngine, EngineType
from app.utils.logger import logger


class UserProfileEngineBase(BaseEngine, ABC):
    """用户画像引擎基类
    
    提供用户画像的统一接口，包括：
    - 获取用户画像
    - 更新用户画像
    - 用户特征分析
    
    Attributes:
        engine_name: 引擎名称
        config: 引擎配置字典
    """
    
    def __init__(
        self,
        engine_name: str,
        config: Dict[str, Any],
        **kwargs
    ):
        """初始化用户画像引擎
        
        Args:
            engine_name: 引擎名称
            config: 引擎配置
            **kwargs: 其他参数
        """
        super().__init__(
            engine_name=engine_name,
            engine_type=EngineType.USERPROFILE,
            **kwargs
        )
        self.config = config
        self._initialized = False
        
        logger.info(
            f"Initializing userprofile engine: {engine_name}",
            extra={"engine_name": engine_name, "config": config}
        )
    
    @abstractmethod
    async def get_profile(
        self,
        user_id: str,
        max_token_size: int = 300,
        **kwargs
    ) -> Dict[str, Any]:
        """获取用户画像
        
        Args:
            user_id: 用户ID
            max_token_size: 最大token数量
            **kwargs: 其他参数
        
        Returns:
            Dict: 用户画像数据，包含：
                - user_id: 用户ID
                - profile_text: 画像文本
                - profile_data: 结构化画像数据（可选）
                - token_size: 实际token数
        
        Raises:
            NotImplementedError: 子类未实现此方法
        """
        raise NotImplementedError("Subclass must implement get_profile()")
    
    @abstractmethod
    async def update_profile(
        self,
        user_id: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> bool:
        """更新用户画像
        
        Args:
            user_id: 用户ID
            messages: 会话消息列表
            **kwargs: 其他参数
        
        Returns:
            bool: 更新是否成功
        
        Raises:
            NotImplementedError: 子类未实现此方法
        """
        raise NotImplementedError("Subclass must implement update_profile()")
    
    async def shutdown(self) -> None:
        """关闭引擎"""
        await super().shutdown()
        logger.info(f"UserProfile engine shutdown: {self.engine_name}")

