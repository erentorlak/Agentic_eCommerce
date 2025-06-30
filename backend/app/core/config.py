"""
Enhanced Configuration Management

Following best practices:
- Environment-based configuration
- Secret management and security
- Validation and type safety
- Logging and monitoring setup
- Development vs production settings
"""

import os
import secrets
from functools import lru_cache
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from pydantic import BaseSettings, Field, validator, AnyHttpUrl, PostgresDsn
from pydantic.env_settings import SettingsSourceCallable


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    
    # Core database settings
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql://user:password@localhost/migration_db",
        env="DATABASE_URL",
        description="PostgreSQL database URL"
    )
    
    # Connection pool settings
    DB_POOL_SIZE: int = Field(
        default=20,
        ge=5,
        le=100,
        env="DB_POOL_SIZE",
        description="Database connection pool size"
    )
    
    DB_MAX_OVERFLOW: int = Field(
        default=10,
        ge=0,
        le=50,
        env="DB_MAX_OVERFLOW",
        description="Maximum connection pool overflow"
    )
    
    DB_POOL_TIMEOUT: int = Field(
        default=30,
        ge=5,
        le=300,
        env="DB_POOL_TIMEOUT",
        description="Connection timeout in seconds"
    )
    
    DB_POOL_RECYCLE: int = Field(
        default=3600,
        ge=300,
        le=86400,
        env="DB_POOL_RECYCLE",
        description="Connection recycle time in seconds"
    )
    
    # Migration settings
    AUTO_MIGRATE: bool = Field(
        default=True,
        env="AUTO_MIGRATE",
        description="Automatically run database migrations on startup"
    )


class RedisSettings(BaseSettings):
    """Redis configuration for caching and sessions"""
    
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL",
        description="Redis connection URL"
    )
    
    REDIS_POOL_SIZE: int = Field(
        default=20,
        ge=5,
        le=100,
        env="REDIS_POOL_SIZE",
        description="Redis connection pool size"
    )
    
    CACHE_TTL: int = Field(
        default=3600,
        ge=60,
        le=86400,
        env="CACHE_TTL",
        description="Default cache TTL in seconds"
    )


class SecuritySettings(BaseSettings):
    """Security and authentication configuration"""
    
    # JWT settings
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        env="SECRET_KEY",
        description="Secret key for JWT signing"
    )
    
    JWT_ALGORITHM: str = Field(
        default="HS256",
        env="JWT_ALGORITHM",
        description="JWT signing algorithm"
    )
    
    JWT_EXPIRE_MINUTES: int = Field(
        default=60 * 24,  # 24 hours
        ge=15,
        le=60 * 24 * 7,  # Max 1 week
        env="JWT_EXPIRE_MINUTES",
        description="JWT token expiration in minutes"
    )
    
    # API Key settings
    API_KEY_HEADER: str = Field(
        default="X-API-Key",
        env="API_KEY_HEADER",
        description="API key header name"
    )
    
    # Password settings
    PASSWORD_MIN_LENGTH: int = Field(
        default=8,
        ge=6,
        le=128,
        env="PASSWORD_MIN_LENGTH",
        description="Minimum password length"
    )
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=100,
        ge=10,
        le=1000,
        env="RATE_LIMIT_PER_MINUTE",
        description="Rate limit per minute per user"
    )
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = Field(
        default=["*"],
        env="ALLOWED_HOSTS",
        description="Allowed hosts for CORS"
    )
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, value):
        if isinstance(value, str):
            return [host.strip() for host in value.split(",") if host.strip()]
        return value


class AISettings(BaseSettings):
    """AI and LangGraph configuration"""
    
    # OpenAI settings
    OPENAI_API_KEY: str = Field(
        ...,  # Required
        env="OPENAI_API_KEY",
        description="OpenAI API key for GPT models"
    )
    
    OPENAI_MODEL: str = Field(
        default="gpt-4",
        env="OPENAI_MODEL",
        description="OpenAI model to use"
    )
    
    OPENAI_TEMPERATURE: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        env="OPENAI_TEMPERATURE",
        description="OpenAI model temperature"
    )
    
    OPENAI_MAX_TOKENS: int = Field(
        default=2000,
        ge=100,
        le=8000,
        env="OPENAI_MAX_TOKENS",
        description="Maximum tokens per OpenAI request"
    )
    
    # LangGraph settings
    LANGGRAPH_TIMEOUT: int = Field(
        default=300,
        ge=30,
        le=3600,
        env="LANGGRAPH_TIMEOUT",
        description="LangGraph workflow timeout in seconds"
    )
    
    LANGGRAPH_MAX_RETRIES: int = Field(
        default=3,
        ge=1,
        le=10,
        env="LANGGRAPH_MAX_RETRIES",
        description="Maximum LangGraph retry attempts"
    )
    
    # Fallback settings
    AI_FALLBACK_ENABLED: bool = Field(
        default=True,
        env="AI_FALLBACK_ENABLED",
        description="Enable fallback when AI services fail"
    )


class MonitoringSettings(BaseSettings):
    """Monitoring and logging configuration"""
    
    # Logging settings
    LOG_LEVEL: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )
    
    LOG_FORMAT: str = Field(
        default="json",
        env="LOG_FORMAT",
        description="Log format (json or text)"
    )
    
    # Metrics settings
    METRICS_ENABLED: bool = Field(
        default=True,
        env="METRICS_ENABLED",
        description="Enable Prometheus metrics"
    )
    
    METRICS_PATH: str = Field(
        default="/metrics",
        env="METRICS_PATH",
        description="Metrics endpoint path"
    )
    
    # Health check settings
    HEALTH_CHECK_ENABLED: bool = Field(
        default=True,
        env="HEALTH_CHECK_ENABLED",
        description="Enable health checks"
    )
    
    HEALTH_CHECK_PATH: str = Field(
        default="/health",
        env="HEALTH_CHECK_PATH",
        description="Health check endpoint path"
    )
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, value):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if value.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return value.upper()


class MigrationSettings(BaseSettings):
    """Migration-specific configuration"""
    
    # Platform settings
    SUPPORTED_SOURCE_PLATFORMS: List[str] = Field(
        default=["shopify", "woocommerce", "magento", "opencart"],
        env="SUPPORTED_SOURCE_PLATFORMS",
        description="Supported source platforms"
    )
    
    SUPPORTED_DESTINATION_PLATFORMS: List[str] = Field(
        default=["ideasoft", "ikas"],
        env="SUPPORTED_DESTINATION_PLATFORMS",
        description="Supported destination platforms"
    )
    
    # Migration limits
    MAX_CONCURRENT_MIGRATIONS: int = Field(
        default=5,
        ge=1,
        le=50,
        env="MAX_CONCURRENT_MIGRATIONS",
        description="Maximum concurrent migrations"
    )
    
    MAX_MIGRATION_DURATION_HOURS: int = Field(
        default=72,
        ge=1,
        le=168,  # 1 week
        env="MAX_MIGRATION_DURATION_HOURS",
        description="Maximum migration duration in hours"
    )
    
    # Data processing settings
    BATCH_SIZE: int = Field(
        default=100,
        ge=10,
        le=1000,
        env="BATCH_SIZE",
        description="Data processing batch size"
    )
    
    MAX_RETRIES: int = Field(
        default=3,
        ge=1,
        le=10,
        env="MAX_RETRIES",
        description="Maximum retry attempts for failed operations"
    )
    
    @validator("SUPPORTED_SOURCE_PLATFORMS", "SUPPORTED_DESTINATION_PLATFORMS", pre=True)
    def parse_platform_list(cls, value):
        if isinstance(value, str):
            return [platform.strip().lower() for platform in value.split(",") if platform.strip()]
        return [platform.lower() for platform in value]


class Settings(BaseSettings):
    """Main application settings"""
    
    # Application settings
    APP_NAME: str = Field(
        default="Intelligent Store Migration Assistant",
        env="APP_NAME",
        description="Application name"
    )
    
    VERSION: str = Field(
        default="1.0.0",
        env="VERSION",
        description="Application version"
    )
    
    ENVIRONMENT: str = Field(
        default="development",
        env="ENVIRONMENT",
        description="Environment (development, staging, production)"
    )
    
    DEBUG: bool = Field(
        default=False,
        env="DEBUG",
        description="Enable debug mode"
    )
    
    # Server settings
    HOST: str = Field(
        default="0.0.0.0",
        env="HOST",
        description="Server host"
    )
    
    PORT: int = Field(
        default=8000,
        ge=1000,
        le=65535,
        env="PORT",
        description="Server port"
    )
    
    # API settings
    API_V1_PREFIX: str = Field(
        default="/api/v1",
        env="API_V1_PREFIX",
        description="API v1 prefix"
    )
    
    DOCS_URL: Optional[str] = Field(
        default="/docs",
        env="DOCS_URL",
        description="API documentation URL"
    )
    
    REDOC_URL: Optional[str] = Field(
        default="/redoc",
        env="REDOC_URL",
        description="ReDoc documentation URL"
    )
    
    # Nested configurations
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    security: SecuritySettings = SecuritySettings()
    ai: AISettings = AISettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    migration: MigrationSettings = MigrationSettings()
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allow nested environment variables
        env_nested_delimiter = "__"
        
        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, value):
        valid_environments = ["development", "staging", "production"]
        if value.lower() not in valid_environments:
            raise ValueError(f"Environment must be one of: {valid_environments}")
        return value.lower()
    
    @validator("DEBUG")
    def set_debug_based_on_environment(cls, value, values):
        environment = values.get("ENVIRONMENT", "development")
        if environment == "production":
            return False
        return value
    
    @validator("DOCS_URL", "REDOC_URL")
    def disable_docs_in_production(cls, value, values):
        environment = values.get("ENVIRONMENT", "development")
        if environment == "production":
            return None
        return value
    
    def get_database_url(self) -> str:
        """Get formatted database URL"""
        return str(self.database.DATABASE_URL)
    
    def get_redis_url(self) -> str:
        """Get formatted Redis URL"""
        return self.redis.REDIS_URL
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT == "production"
    
    def get_allowed_origins(self) -> List[str]:
        """Get CORS allowed origins"""
        if self.is_production():
            return self.security.ALLOWED_HOSTS
        else:
            # Allow all origins in development
            return ["*"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (excluding secrets)"""
        data = self.dict()
        
        # Remove sensitive information
        sensitive_keys = [
            "SECRET_KEY",
            "OPENAI_API_KEY",
            "DATABASE_URL",
            "REDIS_URL"
        ]
        
        def remove_sensitive(obj, keys):
            if isinstance(obj, dict):
                return {
                    k: remove_sensitive(v, keys) if k not in keys else "***HIDDEN***"
                    for k, v in obj.items()
                }
            return obj
        
        return remove_sensitive(data, sensitive_keys)


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()


def setup_logging(settings: Settings):
    """Setup structured logging"""
    import structlog
    import logging
    
    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, settings.monitoring.LOG_LEVEL),
        format="%(message)s",
    )
    
    # Configure structlog
    if settings.monitoring.LOG_FORMAT == "json":
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ]
    else:
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer()
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )


def validate_environment_variables():
    """Validate critical environment variables"""
    try:
        settings = get_settings()
        
        # Validate AI settings
        if not settings.ai.OPENAI_API_KEY or settings.ai.OPENAI_API_KEY == "your-openai-api-key":
            raise ValueError("OPENAI_API_KEY must be set to a valid API key")
        
        # Validate database URL in production
        if settings.is_production():
            if "localhost" in str(settings.database.DATABASE_URL):
                raise ValueError("Production database URL should not use localhost")
        
        # Validate security settings
        if settings.is_production():
            if len(settings.security.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")
            
            if "*" in settings.security.ALLOWED_HOSTS:
                raise ValueError("ALLOWED_HOSTS should not contain '*' in production")
        
        return True
        
    except Exception as exc:
        print(f"Environment validation failed: {exc}")
        return False


# Export commonly used settings
__all__ = [
    "Settings",
    "get_settings",
    "setup_logging",
    "validate_environment_variables"
]