"""
Production-Ready Configuration with Security Enhancements
"""

import os
from dataclasses import dataclass
from typing import Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Security configuration for production."""
    
    # HTTPS/SSL
    use_https: bool = os.getenv("USE_HTTPS", "True").lower() == "true"
    ssl_cert_path: Optional[str] = os.getenv("SSL_CERT_PATH", None)
    ssl_key_path: Optional[str] = os.getenv("SSL_KEY_PATH", None)
    
    # API Authentication
    enable_api_key_auth: bool = os.getenv("ENABLE_API_KEY_AUTH", "False").lower() == "true"
    api_key_secret: Optional[str] = os.getenv("API_KEY_SECRET", None)
    
    # CORS
    allowed_origins: list = None
    
    # Rate Limiting
    enable_rate_limiting: bool = os.getenv("ENABLE_RATE_LIMITING", "True").lower() == "true"
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "1000"))
    rate_limit_period: int = int(os.getenv("RATE_LIMIT_PERIOD", "3600"))
    
    # Request size limits
    max_body_size: int = int(os.getenv("MAX_BODY_SIZE", "1048576"))  # 1MB
    
    def __post_init__(self):
        """Parse CORS origins from environment."""
        origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
        self.allowed_origins = [
            origin.strip() for origin in origins_str.split(",")
        ]
    
    def validate(self):
        """Validate security configuration."""
        if self.use_https:
            if not self.ssl_cert_path or not self.ssl_key_path:
                logger.warning(
                    "HTTPS enabled but SSL certificates not configured. "
                    "Set SSL_CERT_PATH and SSL_KEY_PATH environment variables."
                )
        
        if self.enable_api_key_auth and not self.api_key_secret:
            raise ValueError(
                "API key authentication enabled but API_KEY_SECRET not set"
            )


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    
    enable_metrics: bool = os.getenv("ENABLE_METRICS", "True").lower() == "true"
    metrics_port: int = int(os.getenv("METRICS_PORT", "9090"))
    
    sentry_dsn: Optional[str] = os.getenv("SENTRY_DSN", None)
    
    health_check_interval: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    
    enable_profiling: bool = os.getenv("ENABLE_PROFILING", "False").lower() == "true"


@dataclass
class PerformanceConfig:
    """Performance tuning configuration."""
    
    # Connection pooling
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "20"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "40"))
    redis_pool_size: int = int(os.getenv("REDIS_POOL_SIZE", "50"))
    
    # Caching
    enable_caching: bool = os.getenv("ENABLE_CACHING", "True").lower() == "true"
    cache_ttl: int = int(os.getenv("CACHE_TTL", "300"))
    
    # Request timeout
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "60"))


@dataclass
class DeploymentConfig:
    """Deployment environment configuration."""
    
    environment: str = os.getenv("ENVIRONMENT", "development")
    deployment_region: str = os.getenv("DEPLOYMENT_REGION", "us-east-1")
    service_name: str = os.getenv("SERVICE_NAME", "task-queue-api")
    version: str = "1.0.0"
    
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() in ["production", "prod"]
    
    def is_staging(self) -> bool:
        """Check if running in staging."""
        return self.environment.lower() == "staging"
    
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment.lower() in ["development", "dev", "local"]


class ProductionConfig:
    """Combined production configuration."""
    
    def __init__(self):
        """Initialize production configuration."""
        from src.config import config as base_config
        
        self.base = base_config
        self.security = SecurityConfig()
        self.monitoring = MonitoringConfig()
        self.performance = PerformanceConfig()
        self.deployment = DeploymentConfig()
        
        # Validate configuration
        self.security.validate()
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "api": {
                "host": self.base.api.host,
                "port": self.base.api.port,
                "workers": self.base.api.workers,
            },
            "redis": {
                "host": self.base.redis.host,
                "port": self.base.redis.port,
                "pool_size": self.performance.redis_pool_size,
            },
            "database": {
                "path": self.base.database.sqlite_path,
                "pool_size": self.performance.db_pool_size,
                "echo": self.base.database.echo,
            },
            "worker": {
                "num_workers": self.base.worker.num_workers,
                "max_retries": self.base.worker.max_retries,
                "poll_interval": self.base.worker.poll_interval,
            },
            "security": {
                "https": self.security.use_https,
                "rate_limiting": self.security.enable_rate_limiting,
                "api_key_auth": self.security.enable_api_key_auth,
            },
            "monitoring": {
                "metrics_enabled": self.monitoring.enable_metrics,
                "profiling_enabled": self.monitoring.enable_profiling,
                "sentry_enabled": bool(self.monitoring.sentry_dsn),
            },
            "deployment": {
                "environment": self.deployment.environment,
                "region": self.deployment.deployment_region,
                "service_name": self.deployment.service_name,
            },
        }


@lru_cache(maxsize=1)
def get_production_config() -> ProductionConfig:
    """Get production configuration (cached)."""
    return ProductionConfig()
