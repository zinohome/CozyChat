"""
安全工具

提供密码哈希、JWT生成和验证等功能
"""

# 标准库
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

# 第三方库
from jose import JWTError, jwt
from passlib.context import CryptContext

# 本地库
from app.config.config import settings
from app.utils.logger import logger

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30天
REFRESH_TOKEN_EXPIRE_DAYS = 90  # 90天


def hash_password(password: str) -> str:
    """哈希密码
    
    Args:
        password: 明文密码
        
    Returns:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        bool: 密码是否正确
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌
    
    Args:
        data: 要编码的数据（通常包含user_id、username、role等）
        expires_delta: 过期时间差（可选）
        
    Returns:
        str: JWT令牌
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """创建刷新令牌
    
    Args:
        data: 要编码的数据
        
    Returns:
        str: 刷新令牌
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """验证JWT令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        Optional[Dict[str, Any]]: 解码后的数据，如果验证失败返回None
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解码JWT令牌（不验证签名和过期时间，仅用于调试）
    
    Args:
        token: JWT令牌
        
    Returns:
        Optional[Dict[str, Any]]: 解码后的数据
    """
    try:
        # 注意：这里不验证签名和过期时间，仅用于调试
        payload = jwt.decode(
            token,
            key="",  # 空密钥，因为不验证签名
            options={"verify_signature": False, "verify_exp": False}
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        return None

