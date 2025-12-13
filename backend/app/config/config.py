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
    
    # ===== Demo模式配置 =====
    demo_mode: bool = Field(
        default=False,
        alias="DEMO_MODE",
        description="是否启用Demo模式（true=启用，自动创建DemoUser）"
    )
    demo_username: str = Field(
        default="demo",
        alias="DEMO_USERNAME",
        description="Demo用户用户名"
    )
    demo_password: str = Field(
        default="demo123",
        alias="DEMO_PASSWORD",
        description="Demo用户密码"
    )
    demo_email: str = Field(
        default="demo@cozychat.ai",
        alias="DEMO_EMAIL",
        description="Demo用户邮箱"
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
    redis_socket_connect_timeout: float = Field(default=5.0, alias="REDIS_SOCKET_CONNECT_TIMEOUT")
    redis_socket_timeout: float = Field(default=5.0, alias="REDIS_SOCKET_TIMEOUT")
    redis_retry_on_timeout: bool = Field(default=True, alias="REDIS_RETRY_ON_TIMEOUT")
    redis_health_check_interval: int = Field(default=30, alias="REDIS_HEALTH_CHECK_INTERVAL")
    
    # ===== OpenAI配置 =====
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1", 
        alias="OPENAI_BASE_URL"
    )
    openai_realtime_model: str = Field(
        default="gpt-4o-realtime-preview-2024-12-17",
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
    
    # ===== 高德地图API配置 =====
    amap_maps_api_key: Optional[str] = Field(default=None, alias="AMAP_MAPS_API_KEY")
    
    # ===== Tavily搜索API配置 =====
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    
    # ===== 会话标题生成配置（已迁移到session.yaml）=====
    # ⚠️ 已废弃：请使用 ConfigAdapter 从 session.yaml 读取配置
    session_title_trigger_length: int = Field(
        default=10,
        alias="SESSION_TITLE_TRIGGER_LENGTH",
        description="触发标题生成的最小消息数（已废弃，使用session.yaml）"
    )
    session_title_max_messages: int = Field(
        default=20,
        alias="SESSION_TITLE_MAX_MESSAGES",
        description="构造标题时参与的最大消息数（已废弃，使用session.yaml）"
    )
    session_title_model: str = Field(
        default="gpt-4o-mini",
        alias="SESSION_TITLE_MODEL",
        description="标题生成使用的模型（已废弃，使用session.yaml）"
    )
    session_title_temperature: float = Field(
        default=0.3,
        alias="SESSION_TITLE_TEMPERATURE",
        description="标题生成的温度参数（已废弃，使用session.yaml）"
    )
    session_title_max_tokens: int = Field(
        default=100,
        alias="SESSION_TITLE_MAX_TOKENS",
        description="标题生成的最大token数（已废弃，使用session.yaml）"
    )
    
    # ===== 记忆系统配置（已迁移到memory.yaml）=====
    # ⚠️ 已废弃：请使用 ConfigAdapter 从 memory.yaml 读取配置
    memory_storage_mode: str = Field(
        default="hybrid",
        alias="MEMORY_STORAGE_MODE",
        description="记忆存储模式: dual/unified/hybrid（已废弃，使用memory.yaml）"
    )
    memory_async_write: bool = Field(
        default=True,
        alias="MEMORY_ASYNC_WRITE",
        description="是否异步写入记忆（已废弃，使用memory.yaml）"
    )
    memory_batch_size: int = Field(
        default=10,
        alias="MEMORY_BATCH_SIZE",
        description="批量写入的批次大小（已废弃，使用memory.yaml）"
    )
    memory_dedup_enabled: bool = Field(
        default=True,
        alias="MEMORY_DEDUP_ENABLED",
        description="是否启用记忆去重（已废弃，使用memory.yaml）"
    )
    memory_dedup_mode: str = Field(
        default="async",
        alias="MEMORY_DEDUP_MODE",
        description="去重模式: async/off（已废弃，使用memory.yaml）"
    )
    memory_dedup_content_threshold: int = Field(
        default=5,
        alias="MEMORY_DEDUP_CONTENT_THRESHOLD",
        description="同一内容/主题的记忆数量阈值（已废弃，使用memory.yaml）"
    )
    memory_dedup_storage_threshold: float = Field(
        default=0.8,
        alias="MEMORY_DEDUP_STORAGE_THRESHOLD",
        description="存储利用率阈值（0-1）（已废弃，使用memory.yaml）"
    )
    memory_dedup_check_interval: int = Field(
        default=300,
        alias="MEMORY_DEDUP_CHECK_INTERVAL",
        description="去重检查间隔（秒）（已废弃，使用memory.yaml）"
    )
    
    # ===== 智能上下文配置（已迁移到context.yaml）=====
    # ⚠️ 已废弃：请使用 ConfigAdapter 从 context.yaml 读取配置
    context_intelligent_enabled: bool = Field(
        default=True,
        alias="CONTEXT_INTELLIGENT_ENABLED",
        description="是否启用智能上下文管理（已废弃，使用context.yaml）"
    )
    context_recent_message_count: int = Field(
        default=6,
        alias="CONTEXT_RECENT_MESSAGE_COUNT",
        description="保留的最近消息数量（已废弃，使用context.yaml）"
    )
    context_max_tokens: int = Field(
        default=8000,
        alias="CONTEXT_MAX_TOKENS",
        description="上下文最大token数（已废弃，使用context.yaml）"
    )
    context_summary_weight: float = Field(
        default=0.3,
        alias="CONTEXT_SUMMARY_WEIGHT",
        description="历史摘要权重（已废弃，使用context.yaml）"
    )
    context_memory_weight: float = Field(
        default=0.2,
        alias="CONTEXT_MEMORY_WEIGHT",
        description="记忆权重（已废弃，使用context.yaml）"
    )
    context_summary_trigger_count: int = Field(
        default=50,
        alias="CONTEXT_SUMMARY_TRIGGER_COUNT",
        description="触发摘要生成的消息数阈值（已废弃，使用context.yaml）"
    )
    context_summary_window_size: int = Field(
        default=20,
        alias="CONTEXT_SUMMARY_WINDOW_SIZE",
        description="每次摘要的消息窗口大小（已废弃，使用context.yaml）"
    )
    context_summary_model: str = Field(
        default="gpt-4o-mini",
        alias="CONTEXT_SUMMARY_MODEL",
        description="摘要生成使用的模型（已废弃，使用context.yaml）"
    )
    context_summary_temperature: float = Field(
        default=0.3,
        alias="CONTEXT_SUMMARY_TEMPERATURE",
        description="摘要生成的温度参数（已废弃，使用context.yaml）"
    )
    
    # ===== 性能监控配置（已迁移到performance.yaml）=====
    # ⚠️ 已废弃：请使用 ConfigAdapter 从 performance.yaml 读取配置
    performance_slow_request_threshold: float = Field(
        default=0.2,
        alias="PERFORMANCE_SLOW_REQUEST_THRESHOLD",
        description="慢请求阈值（秒），超过此时间的请求会记录为警告（已废弃，使用performance.yaml）"
    )
    performance_slow_delete_threshold: float = Field(
        default=0.5,
        alias="PERFORMANCE_SLOW_DELETE_THRESHOLD",
        description="DELETE操作的慢请求阈值（秒），通常需要更长时间（已废弃，使用performance.yaml）"
    )
    
    # ===== Sentry监控配置 =====
    sentry_dsn: Optional[str] = Field(
        default=None,
        alias="SENTRY_DSN",
        description="Sentry DSN (Data Source Name)，用于错误追踪和性能监控"
    )
    sentry_environment: str = Field(
        default="development",
        alias="SENTRY_ENVIRONMENT",
        description="Sentry环境标识（development/staging/production）"
    )
    sentry_traces_sample_rate: float = Field(
        default=0.1,
        alias="SENTRY_TRACES_SAMPLE_RATE",
        description="Sentry性能追踪采样率（0.0-1.0），生产环境建议0.1-0.2"
    )
    sentry_profiles_sample_rate: float = Field(
        default=0.1,
        alias="SENTRY_PROFILES_SAMPLE_RATE",
        description="Sentry性能分析采样率（0.0-1.0）"
    )
    sentry_send_default_pii: bool = Field(
        default=False,
        alias="SENTRY_SEND_DEFAULT_PII",
        description="是否发送个人身份信息（PII）到Sentry，生产环境建议False"
    )
    sentry_attach_stacktrace: bool = Field(
        default=True,
        alias="SENTRY_ATTACH_STACKTRACE",
        description="是否附加完整堆栈跟踪"
    )
    sentry_enable: bool = Field(
        default=False,
        alias="SENTRY_ENABLE",
        description="是否启用Sentry监控（只有配置了DSN且此项为True才会生效）"
    )
    sentry_max_breadcrumbs: int = Field(
        default=100,
        alias="SENTRY_MAX_BREADCRUMBS",
        description="最大面包屑数量（用于追踪事件发生前的操作序列）"
    )
    sentry_debug: bool = Field(
        default=False,
        alias="SENTRY_DEBUG",
        description="Sentry调试模式（开启后会输出详细日志）"
    )
    
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
# 这是Pydantic Settings的设计特性，无法通过类型注解解决
settings: Settings = Settings()  # type: ignore[call-arg]


