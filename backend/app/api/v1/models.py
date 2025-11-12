"""
Models API

提供模型列表和详情查询（OpenAI兼容）
"""

# 标准库
from typing import Any, Dict, List, Optional

# 第三方库
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

# 本地库
from app.api.deps import get_current_active_user
from app.engines.ai import AIEngineFactory, AIEngineRegistry
from app.models.user import User
from app.utils.config_loader import get_config_loader
from app.utils.logger import logger

router = APIRouter(tags=["models"])


# ===== 响应模型 =====

class ModelInfo(BaseModel):
    """模型信息"""
    id: str = Field(..., description="模型ID")
    object: str = Field(default="model", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    owned_by: str = Field(..., description="拥有者")
    provider: str = Field(..., description="提供商")
    capabilities: Dict[str, bool] = Field(default_factory=dict, description="能力")


class ModelDetail(ModelInfo):
    """模型详情"""
    pricing: Optional[Dict[str, Any]] = Field(None, description="定价信息")


class ModelsListResponse(BaseModel):
    """模型列表响应"""
    object: str = Field(default="list", description="对象类型")
    data: List[ModelInfo] = Field(..., description="模型列表")


# ===== API路由 =====

@router.get("", response_model=ModelsListResponse)
async def list_models(
    user: User = Depends(get_current_active_user)
) -> ModelsListResponse:
    """列出所有可用模型
    
    返回所有已注册的AI引擎及其支持的模型列表
    
    Args:
        user: 当前用户
        
    Returns:
        ModelsListResponse: 模型列表
    """
    try:
        # 清除配置缓存，确保获取最新配置
        config_loader = get_config_loader()
        config_loader.clear_cache()
        
        # 获取所有已注册的引擎
        engines = AIEngineRegistry.list_engines()
        
        models: List[ModelInfo] = []
        
        # 为每个引擎生成模型信息
        for engine_name in engines:
            try:
                # 创建引擎实例以获取模型信息
                engine = AIEngineFactory.create_engine(engine_name)
                
                # 获取引擎支持的模型列表
                if hasattr(engine, 'list_models'):
                    engine_models = engine.list_models()
                else:
                    # 默认模型（从引擎配置获取）
                    engine_models = [engine.model] if engine.model else []
                
                # 为每个模型创建ModelInfo
                for model_id in engine_models:
                    models.append(ModelInfo(
                        id=model_id,
                        object="model",
                        created=1677610602,  # 固定时间戳
                        owned_by=engine_name,
                        provider=engine_name,
                        capabilities={
                            "function_calling": hasattr(engine, 'chat_with_tools'),
                            "streaming": hasattr(engine, 'chat_stream')
                        }
                    ))
                    
            except Exception as e:
                logger.warning(
                    f"Failed to get models for engine {engine_name}: {e}",
                    exc_info=True
                )
                continue
        
        logger.info(
            "Listed models",
            extra={"user_id": str(user.id), "models_count": len(models)}
        )
        
        return ModelsListResponse(
            object="list",
            data=models
        )
        
    except Exception as e:
        logger.error(f"Failed to list models: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list models"
        )


@router.get("/{model_id}", response_model=ModelDetail)
async def get_model(
    model_id: str,
    user: User = Depends(get_current_active_user)
) -> ModelDetail:
    """获取单个模型详情
    
    Args:
        model_id: 模型ID
        user: 当前用户
        
    Returns:
        ModelDetail: 模型详情
        
    Raises:
        HTTPException: 如果模型不存在
    """
    try:
        # 查找模型对应的引擎
        engines = AIEngineRegistry.list_engines()
        model_info: Optional[ModelDetail] = None
        
        for engine_name in engines:
            try:
                engine = AIEngineFactory.create_engine(engine_name)
                
                # 检查模型是否属于此引擎
                if hasattr(engine, 'list_models'):
                    engine_models = engine.list_models()
                else:
                    engine_models = [engine.model] if engine.model else []
                
                if model_id in engine_models:
                    # 获取定价信息（如果有）
                    pricing = None
                    if hasattr(engine, 'get_pricing'):
                        pricing = engine.get_pricing(model_id)
                    
                    model_info = ModelDetail(
                        id=model_id,
                        object="model",
                        created=1677610602,
                        owned_by=engine_name,
                        provider=engine_name,
                        capabilities={
                            "function_calling": hasattr(engine, 'chat_with_tools'),
                            "streaming": hasattr(engine, 'chat_stream')
                        },
                        pricing=pricing
                    )
                    break
                    
            except Exception as e:
                logger.warning(
                    f"Failed to check model in engine {engine_name}: {e}",
                    exc_info=True
                )
                continue
        
        if not model_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{model_id}' not found"
            )
        
        logger.info(
            "Retrieved model detail",
            extra={"user_id": str(user.id), "model_id": model_id}
        )
        
        return model_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get model"
        )

