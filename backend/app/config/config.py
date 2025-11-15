"""
应用配置模块

使用Pydantic Settings管理环境变量配置
"""

# 标准库
import os
from pathlib import Path
from typing import List, Optional, Union

# 第三方库
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# 查找.env文件的位置
def find_env_file() -> str:
    """查找.env文件路径
    
    检查多个可能的位置：
    1. 当前目录
    2. 父目录（backend的父目录）
    3. backend目录
    """
    current_dir = Path.cwd()
    
    # 检查当前目录
    if (current_dir / ".env").exists():
        return str(current_dir / ".env")
    
    # 检查父目录
    parent_dir = current_dir.parent
    if (parent_dir / ".env").exists():
        return str(parent_dir / ".env")
    
    # 检查backend的父目录（从代码文件位置计算）
    config_file_dir = Path(__file__).parent.parent.parent.parent
    if (config_file_dir / ".env").exists():
        return str(config_file_dir / ".env")
    
    # 默认返回相对路径
    return ".env"


class Settings(BaseSettings):
    """应用配置类
    
    所有敏感信息通过环境变量加载，不提交到Git。
    
    Attributes:
        app_name: 应用名称
        app_env: 运行环境（development/staging/production）
        app_debug: 调试模式
        app_secret_key: 应用密钥
        jwt_secret_key: JWT密钥
        cors_origins: CORS允许的源
        database_url: 数据库连接URL
        redis_url: Redis连接URL
        openai_api_key: OpenAI API密钥
        openai_base_url: OpenAI API基础URL
        chroma_persist_directory: ChromaDB持久化目录
        log_level: 日志级别
        log_file: 日志文件路径
    """
    
    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""  # 明确指定环境变量前缀为空
    )
    
    # ===== 应用配置 =====
    app_name: str = "CozyChat"
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_secret_key: str = Field(..., alias="APP_SECRET_KEY")
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    
    # ===== 安全配置 =====
    allow_registration: bool = Field(
        default=True,
        alias="ALLOW_REGISTRATION",
        description="是否允许开放注册（true=允许，false=禁止）"
    )
    
    # ===== CORS配置 =====
    # 使用 List[str] 类型，通过 field_validator 处理各种输入格式
    # 注意：pydantic_settings 会自动尝试将 List 类型解析为 JSON
    # 如果环境变量是逗号分隔的字符串，需要先转换为 JSON 格式
    # 或者使用 field_validator 在解析前处理
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ],
        alias="CORS_ORIGINS"
    )
    
    # ===== 数据库配置 =====
    database_url: str = Field(..., alias="DATABASE_URL")
    postgres_user: Optional[str] = Field(default=None, alias="POSTGRES_USER")
    postgres_password: Optional[str] = Field(default=None, alias="POSTGRES_PASSWORD")
    postgres_db: Optional[str] = Field(default=None, alias="POSTGRES_DB")
    
    # 数据库连接池配置
    db_pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    db_pool_recycle: int = Field(default=3600, alias="DB_POOL_RECYCLE")
    db_echo: bool = Field(default=False, alias="DB_ECHO")
    
    # ===== Redis配置 =====
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    redis_max_connections: int = Field(default=50, alias="REDIS_MAX_CONNECTIONS")
    
    # ===== OpenAI配置 =====
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1", 
        alias="OPENAI_BASE_URL"
    )
    openai_realtime_model: str = Field(
        default="gpt-4o-realtime-preview-2025-06-03",
        alias="OPENAI_REALTIME_MODEL",
        description="OpenAI Realtime API 使用的模型名称"
    )
    
    # ===== Ollama配置 =====
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL"
    )
    
    # ===== 向量数据库配置 =====
    chroma_persist_directory: str = Field(
        default="./data/chroma",
        alias="CHROMA_PERSIST_DIRECTORY"
    )
    qdrant_url: Optional[str] = Field(default=None, alias="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(default=None, alias="QDRANT_API_KEY")
    
    # ===== 腾讯云配置 =====
    tencent_secret_id: Optional[str] = Field(default=None, alias="TENCENT_SECRET_ID")
    tencent_secret_key: Optional[str] = Field(default=None, alias="TENCENT_SECRET_KEY")
    tencent_app_id: Optional[str] = Field(default=None, alias="TENCENT_APP_ID")
    
    # ===== 天气API配置 =====
    openweather_api_key: Optional[str] = Field(default=None, alias="OPENWEATHER_API_KEY")
    
    # ===== 日志配置 =====
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", alias="LOG_FILE")
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """解析CORS origins，支持逗号分隔的字符串
        
        Pydantic 2.x 使用 field_validator 替代 validator
        
        支持多种格式：
        - 逗号分隔的字符串: "http://localhost:5173,http://localhost:3000"
        - JSON数组字符串: '["http://localhost:5173","http://localhost:3000"]'
        - 空字符串或None: 使用默认值
        - 已经是列表: 直接返回
        """
        # 如果已经是列表，直接返回
        if isinstance(v, list):
            return [str(origin).strip() for origin in v if origin]
        
        # 如果是None或空字符串，返回默认值（包含常见本地地址）
        if v is None or (isinstance(v, str) and not v.strip()):
            return [
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
            ]
        
        # 如果是字符串，尝试解析
        if isinstance(v, str):
            # 尝试解析为JSON
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    origins = [str(origin).strip() for origin in parsed if origin]
                    return origins if origins else [
                        "http://localhost:5173",
                        "http://localhost:3000",
                        "http://127.0.0.1:5173",
                        "http://127.0.0.1:3000",
                    ]
            except (json.JSONDecodeError, ValueError):
                # 如果不是JSON，按逗号分隔处理
                origins = [origin.strip() for origin in v.split(",") if origin.strip()]
                return origins if origins else [
                    "http://localhost:5173",
                    "http://localhost:3000",
                    "http://127.0.0.1:5173",
                    "http://127.0.0.1:3000",
                ]
        
        # 其他情况返回默认值
        return [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]
    
    @field_validator("chroma_persist_directory")
    @classmethod
    def ensure_chroma_directory(cls, v):
        """确保ChromaDB目录存在"""
        os.makedirs(v, exist_ok=True)
        return v
    
    @field_validator("log_file")
    @classmethod
    def ensure_log_directory(cls, v):
        """确保日志目录存在"""
        log_dir = os.path.dirname(v)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        return v
    
    @model_validator(mode="after")
    def ensure_cors_origins_type(self):
        """确保 cors_origins 是 List[str] 类型"""
        if not isinstance(self.cors_origins, list):
            self.cors_origins = [
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
            ]
        return self
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.app_env == "development"
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.app_env == "production"


# 创建全局配置实例
# 注意：Pydantic Settings 会自动从环境变量加载必需参数
# 类型检查器无法理解这一点，因此需要忽略此处的类型检查
settings = Settings()  # type: ignore[call-arg]


