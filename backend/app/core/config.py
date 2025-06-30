"""
Application configuration management using Pydantic Settings
"""

import os
from typing import List, Optional, Any
from functools import lru_cache

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    ENCRYPTION_KEY: str = Field(..., env="ENCRYPTION_KEY")
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    REDIS_URL: str = Field(..., env="REDIS_URL")
    
    # Security
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    # AI/ML Configuration
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    LANGCHAIN_API_KEY: Optional[str] = Field(None, env="LANGCHAIN_API_KEY")
    LANGCHAIN_TRACING_V2: bool = Field(default=False, env="LANGCHAIN_TRACING_V2")
    LANGCHAIN_PROJECT: str = Field(default="migration_assistant", env="LANGCHAIN_PROJECT")
    
    # Platform API Keys
    SHOPIFY_APP_KEY: Optional[str] = Field(None, env="SHOPIFY_APP_KEY")
    SHOPIFY_APP_SECRET: Optional[str] = Field(None, env="SHOPIFY_APP_SECRET")
    SHOPIFY_SCOPES: str = Field(
        default="read_products,read_customers,read_orders,read_content,read_analytics",
        env="SHOPIFY_SCOPES"
    )
    
    WOOCOMMERCE_CONSUMER_KEY: Optional[str] = Field(None, env="WOOCOMMERCE_CONSUMER_KEY")
    WOOCOMMERCE_CONSUMER_SECRET: Optional[str] = Field(None, env="WOOCOMMERCE_CONSUMER_SECRET")
    
    MAGENTO_ACCESS_TOKEN: Optional[str] = Field(None, env="MAGENTO_ACCESS_TOKEN")
    MAGENTO_BASE_URL: Optional[str] = Field(None, env="MAGENTO_BASE_URL")
    
    IDEASOFT_API_KEY: Optional[str] = Field(None, env="IDEASOFT_API_KEY")
    IDEASOFT_BASE_URL: Optional[str] = Field(None, env="IDEASOFT_BASE_URL")
    
    IKAS_API_KEY: Optional[str] = Field(None, env="IKAS_API_KEY")
    IKAS_BASE_URL: Optional[str] = Field(None, env="IKAS_BASE_URL")
    
    BIGCOMMERCE_ACCESS_TOKEN: Optional[str] = Field(None, env="BIGCOMMERCE_ACCESS_TOKEN")
    BIGCOMMERCE_STORE_HASH: Optional[str] = Field(None, env="BIGCOMMERCE_STORE_HASH")
    
    # Communication Services
    SMTP_SERVER: Optional[str] = Field(None, env="SMTP_SERVER")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(None, env="SMTP_PASSWORD")
    FROM_EMAIL: str = Field(default="noreply@migration-assistant.com", env="FROM_EMAIL")
    
    TWILIO_ACCOUNT_SID: Optional[str] = Field(None, env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = Field(None, env="TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: Optional[str] = Field(None, env="TWILIO_PHONE_NUMBER")
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    SENTRY_DSN: Optional[str] = Field(None, env="SENTRY_DSN")
    
    # Application Limits
    MAX_CONCURRENT_MIGRATIONS: int = Field(default=5, env="MAX_CONCURRENT_MIGRATIONS")
    DEFAULT_MIGRATION_TIMEOUT: int = Field(default=3600, env="DEFAULT_MIGRATION_TIMEOUT")
    
    # Queue Configuration
    CELERY_BROKER_URL: str = Field(..., env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(..., env="CELERY_RESULT_BACKEND")
    CELERY_MAX_WORKERS: int = Field(default=4, env="CELERY_MAX_WORKERS")
    
    # File Storage
    AWS_ACCESS_KEY_ID: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    S3_BUCKET_NAME: Optional[str] = Field(None, env="S3_BUCKET_NAME")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(default=200, env="RATE_LIMIT_BURST")
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        validate_assignment = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()


# Global settings instance
settings = get_settings()