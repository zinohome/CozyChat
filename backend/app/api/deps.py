"""
API依赖注入

定义FastAPI路由中使用的依赖项
"""

# 标准库
from typing import AsyncGenerator, Generator, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.context.builder import ContextBuilder
    from app.core.context.summary_generator import SummaryGenerator
    from app.core.personality import PersonalityRegistry
    from app.engines.tools.factory import ToolManagerFactory
    from app.engines.ai.engine_pool import LLMEnginePool
    from app.engines.memory.manager import MemoryManager
    from app.services.orchestration.chat_orchestrator import ChatOrchestrator
    from app.services.context.context_service import ContextService
    from qdrant_client import QdrantClient

# 第三方库
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select

# 本地库
from app.models.base import get_async_db, get_sync_db
from app.models.user import User
from app.core.user.auth import AuthService
from app.utils.logger import logger
from app.utils.security import decode_token
from app.utils.type_helpers import is_active_user

# 安全相关
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话依赖（异步）
    
    Yields:
        AsyncSession: 数据库会话
    """
    async for session in get_async_db():
        yield session


def get_sync_session() -> Generator[Session, None, None]:
    """获取同步数据库会话依赖
    
    Yields:
        Session: 数据库会话
    """
    for session in get_sync_db():
        yield session


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_sync_session)
) -> Optional[User]:
    """获取当前用户
    
    Args:
        credentials: HTTP Bearer认证凭证
        db: 数据库会话
        
    Returns:
        Optional[User]: 当前用户对象，如果未认证返回None
        
    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        auth_service = AuthService()
        token = credentials.credentials
        user = auth_service.get_current_user_from_token(db, token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user_async(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（异步版本）
    
    Args:
        credentials: HTTP Bearer认证凭证
        db: 数据库会话（异步）
        
    Returns:
        Optional[User]: 当前用户对象，如果未认证返回None
        
    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        auth_service = AuthService()
        token = credentials.credentials
        payload = auth_service.verify_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 异步查询用户
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 检查用户状态
        if not is_active_user(user):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户未激活",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_active_user_async(
    current_user: User = Depends(get_current_user_async)
) -> User:
    """获取当前激活用户（异步版本）
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        User: 当前激活的用户对象
        
    Raises:
        HTTPException: 用户未激活时抛出400错误
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    return current_user


async def get_current_user_from_token(token: str) -> User:
    """从JWT token获取当前用户（用于WebSocket等场景）
    
    Args:
        token: JWT token字符串
    
    Returns:
        User: 用户对象
    
    Raises:
        HTTPException: 如果token无效或用户不存在
    """
    try:
        # 解码token
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # 从数据库获取用户
        db = next(get_sync_session())
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user from token: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前激活用户
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        User: 当前激活的用户对象
        
    Raises:
        HTTPException: 用户未激活时抛出400错误
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    return current_user


def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """要求管理员角色
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        User: 管理员用户对象
        
    Raises:
        HTTPException: 如果不是管理员则抛出403错误
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def get_current_user_async(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（异步版本）
    
    Args:
        credentials: HTTP Bearer认证凭证
        db: 数据库会话（异步）
        
    Returns:
        Optional[User]: 当前用户对象，如果未认证返回None
        
    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        from sqlalchemy import select
        auth_service = AuthService()
        token = credentials.credentials
        payload = auth_service.verify_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 异步查询用户
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 检查用户状态
        if not is_active_user(user):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户未激活",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_active_user_async(
    current_user: User = Depends(get_current_user_async)
) -> User:
    """获取当前激活用户（异步版本）
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        User: 当前激活的用户对象
        
    Raises:
        HTTPException: 用户未激活时抛出400错误
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    return current_user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_sync_session)
) -> Optional[User]:
    """获取当前用户（可选，不抛出异常）
    
    用于限流等场景，如果未认证则返回None
    
    Args:
        credentials: HTTP Bearer认证凭证
        db: 数据库会话
        
    Returns:
        Optional[User]: 当前用户对象，如果未认证返回None
    """
    if not credentials:
        return None
    
    try:
        auth_service = AuthService()
        token = credentials.credentials
        user = auth_service.get_current_user_from_token(db, token)
        return user
    except Exception:
        # 认证失败时返回None，不抛出异常
        return None


# ===== 全局组件依赖注入（Phase 2: Lifecycle Optimization） =====

def get_personality_registry() -> "PersonalityRegistry":
    """获取人格注册表依赖
    
    Returns:
        PersonalityRegistry: 人格注册表实例
    """
    from app.core.personality import get_personality_registry
    return get_personality_registry()


def get_tool_manager_factory() -> "ToolManagerFactory":
    """获取工具管理器工厂依赖
    
    Returns:
        ToolManagerFactory: 工具管理器工厂实例
    """
    from app.engines.tools.factory import get_tool_manager_factory
    return get_tool_manager_factory()


def get_llm_engine_pool() -> "LLMEnginePool":
    """获取LLM引擎池依赖
    
    Returns:
        LLMEnginePool: LLM引擎池实例
    """
    from app.engines.ai.engine_pool import get_llm_engine_pool
    return get_llm_engine_pool()


def get_qdrant_client() -> "QdrantClient":
    """获取Qdrant客户端依赖
    
    Returns:
        QdrantClient: Qdrant客户端实例
    """
    from app.engines.memory.qdrant_client_manager import get_qdrant_client
    return get_qdrant_client()


# ===== Memory Manager依赖 =====

def get_memory_manager() -> "MemoryManager":
    """获取MemoryManager依赖
    
    Returns:
        MemoryManager: MemoryManager单例实例
    """
    from app.engines.memory import get_memory_manager
    return get_memory_manager()


# ===== 智能上下文相关依赖 =====

async def get_context_builder(
    db: AsyncSession = Depends(get_db),
    memory_manager = Depends(get_memory_manager)
) -> "ContextBuilder":
    """获取上下文构建器
    
    Args:
        db: 异步数据库会话
        memory_manager: 记忆管理器
    
    Returns:
        ContextBuilder: 上下文构建器实例
    """
    from app.core.context.builder import ContextBuilder
    from app.engines.ai.engine_pool import get_llm_engine_pool
    
    engine_pool = get_llm_engine_pool()
    
    return ContextBuilder(
        memory_manager=memory_manager,
        engine_pool=engine_pool,
        db=db
    )


async def get_context_service(
    db: AsyncSession = Depends(get_db),
    memory_manager: "MemoryManager" = Depends(get_memory_manager),
) -> "ContextService":
    """获取上下文服务依赖
    
    Args:
        db: 异步数据库会话
        memory_manager: 记忆管理器
    
    Returns:
        ContextService: 上下文服务实例
    """
    from app.services.context.context_service import ContextService
    return ContextService(db=db, memory_manager=memory_manager)


async def get_chat_orchestrator(
    personality_registry: "PersonalityRegistry" = Depends(get_personality_registry),
    tool_factory: "ToolManagerFactory" = Depends(get_tool_manager_factory),
    engine_pool: "LLMEnginePool" = Depends(get_llm_engine_pool),
    context_builder: "ContextBuilder" = Depends(get_context_builder),
    memory_manager: "MemoryManager" = Depends(get_memory_manager),
    context_service: Optional["ContextService"] = Depends(get_context_service),
) -> "ChatOrchestrator":
    """获取聊天编排器依赖
    
    Args:
        personality_registry: 人格注册表
        tool_factory: 工具管理器工厂
        engine_pool: LLM引擎池
        context_builder: 上下文构建器（旧版，用于兼容）
        memory_manager: 记忆管理器
        context_service: 上下文服务（新版，优先使用）
        
    Returns:
        ChatOrchestrator: 聊天编排器实例
    """
    from app.services.orchestration.chat_orchestrator import ChatOrchestrator
    return ChatOrchestrator(
        personality_registry=personality_registry,
        tool_factory=tool_factory,
        engine_pool=engine_pool,
        context_builder=context_builder,
        memory_manager=memory_manager,
        context_service=context_service,
    )


async def get_summary_generator(
    sync_db: Session = Depends(get_sync_session)
) -> "SummaryGenerator":
    """获取摘要生成器
    
    Args:
        db: 异步数据库会话
    
    Returns:
        SummaryGenerator: 摘要生成器实例
    """
    from app.core.context.summary_generator import SummaryGenerator
    from app.engines.ai.engine_pool import get_llm_engine_pool
    from app.engines.memory.qdrant_engine import QdrantMemoryEngine
    from app.utils.logger import logger
    
    engine_pool = get_llm_engine_pool()
    
    try:
        memory_engine = QdrantMemoryEngine()
    except Exception as e:
        logger.warning(f"Failed to initialize memory engine: {e}")
        memory_engine = None
    
    return SummaryGenerator(
        engine_pool=engine_pool,
        db=sync_db,
        memory_engine=memory_engine
    )
