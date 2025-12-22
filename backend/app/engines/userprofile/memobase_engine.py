"""
Memobase用户画像引擎实现

通过memobase SDK连接Memobase后端服务，实现用户画像管理
"""

# 标准库
import time
import uuid
from typing import Any, Dict, List, Optional

# 第三方库
from memobase import MemoBaseClient, ChatBlob

# 本地库
from app.engines.userprofile.base import UserProfileEngineBase
from app.utils.logger import logger


def user_id_to_uuid(user_id: str) -> str:
    """将任意用户ID转换为UUID v5格式
    
    Memobase API要求user_id必须是UUID格式。
    使用UUID v5确保同一user_id总是生成相同的UUID。
    
    Args:
        user_id: 原始用户ID
    
    Returns:
        UUID v5格式的字符串
    """
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, user_id))


class MemobaseUserProfileEngine(UserProfileEngineBase):
    """Memobase用户画像引擎实现
    
    使用memobase SDK连接Memobase后端服务，提供：
    - 用户画像获取
    - 用户画像更新
    - 自动特征提取
    
    Attributes:
        project_url: Memobase项目URL
        api_key: Memobase API Key
        client: MemoBaseClient实例
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化Memobase引擎
        
        Args:
            config: 引擎配置，包含：
                - project_url: 项目URL
                - api_key: API Key
        """
        super().__init__(engine_name="memobase", config=config)
        
        self.project_url = config.get("project_url", "http://localhost:8019")
        self.api_key = config.get("api_key", "secret")
        self.client: Optional[MemoBaseClient] = None
    
    async def initialize(self) -> bool:
        """初始化Memobase客户端
        
        Returns:
            bool: 初始化是否成功
        """
        if self._initialized:
            return True
        
        try:
            start_time = time.time()
            
            # 创建Memobase客户端（同步客户端）
            self.client = MemoBaseClient(
                project_url=self.project_url,
                api_key=self.api_key
            )
            
            # Memobase没有显式健康检查，尝试列出用户
            try:
                self.client.list_users()
                self._initialized = True
                
                processing_time = time.time() - start_time
                self.update_metrics(success=True, processing_time=processing_time)
                
                logger.info(
                    f"Memobase userprofile engine initialized successfully",
                    extra={
                        "project_url": self.project_url,
                        "processing_time": processing_time
                    }
                )
                return True
            except Exception as e:
                logger.error(f"Memobase list_users failed during initialization: {e}")
                return False
            
        except Exception as e:
            logger.error(
                f"Failed to initialize Memobase engine: {e}",
                exc_info=True,
                extra={"project_url": self.project_url}
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
            # 尝试列出用户作为健康检查
            self.client.list_users()
            logger.debug("Memobase health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Memobase health check error: {e}", exc_info=True)
            return False
    
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
            Dict: 用户画像数据
        """
        # 确保引擎已初始化
        await self.initialize()
        
        # 转换用户ID为UUID格式
        uuid_user_id = user_id_to_uuid(user_id)
        
        start_time = time.time()
        
        try:
            # 获取用户
            user = self.client.get_user(uuid_user_id, no_get=False)  # type: ignore[union-attr]
            
            # 获取画像
            profile_text = user.profile(
                max_token_size=max_token_size,
                prefer_topics=["basic_info", "interest", "work"]
            )
            
            # 更新指标
            processing_time = time.time() - start_time
            self.update_metrics(success=True, processing_time=processing_time)
            
            logger.info(
                f"User profile retrieved",
                extra={
                    "user_id": user_id,
                    "token_size": len(str(profile_text).split()),
                    "processing_time": processing_time
                }
            )
            
            return {
                "user_id": user_id,
                "profile_text": str(profile_text) if profile_text else "",
                "token_size": len(str(profile_text).split()) if profile_text else 0
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.update_metrics(success=False, processing_time=processing_time)
            
            # 判断是否是用户不存在错误
            error_msg = str(e)
            if "422" in error_msg or "404" in error_msg or "Unprocessable Entity" in error_msg:
                logger.debug(
                    f"User {user_id} (UUID: {uuid_user_id}) not found (normal for new users)",
                    extra={"user_id": user_id}
                )
            else:
                logger.warning(
                    f"Error getting user profile: {e}",
                    extra={"user_id": user_id}
                )
            
            # 返回空画像
            return {
                "user_id": user_id,
                "profile_text": "",
                "token_size": 0
            }
    
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
        """
        # 确保引擎已初始化
        await self.initialize()
        
        # 转换用户ID为UUID格式
        uuid_user_id = user_id_to_uuid(user_id)
        
        start_time = time.time()
        
        try:
            # 尝试获取用户，如果不存在则创建
            user = None
            try:
                user = self.client.get_user(uuid_user_id, no_get=False)  # type: ignore[union-attr]
            except Exception as get_error:
                error_msg = str(get_error)
                if "422" in error_msg or "404" in error_msg or "Unprocessable Entity" in error_msg:
                    logger.info(f"Creating new user: {user_id} (UUID: {uuid_user_id})")
                    try:
                        self.client.add_user(id=uuid_user_id, data={})  # type: ignore[union-attr]
                        user = self.client.get_user(uuid_user_id, no_get=True)  # type: ignore[union-attr]
                    except Exception:
                        user = self.client.get_user(uuid_user_id, no_get=True)  # type: ignore[union-attr]
                else:
                    user = self.client.get_user(uuid_user_id, no_get=True)  # type: ignore[union-attr]
            
            if user:
                # 插入会话数据
                blob = ChatBlob(messages=messages)
                user.insert(blob)
                user.flush()
                
                # 更新指标
                processing_time = time.time() - start_time
                self.update_metrics(success=True, processing_time=processing_time)
                
                logger.info(
                    f"User profile updated",
                    extra={
                        "user_id": user_id,
                        "message_count": len(messages),
                        "processing_time": processing_time
                    }
                )
                return True
            else:
                logger.warning(f"Failed to get/create user: {user_id}")
                return False
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.update_metrics(success=False, processing_time=processing_time)
            
            logger.warning(
                f"Error updating user profile: {e}",
                extra={"user_id": user_id}
            )
            return False
    
    async def shutdown(self) -> None:
        """关闭引擎"""
        if self.client:
            self.client = None
        
        await super().shutdown()

