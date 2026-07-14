"""
Configuration management for the distributed task queue system.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RedisConfig:
    """Redis configuration."""
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    db: int = int(os.getenv("REDIS_DB", "0"))
    password: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    
    @property
    def url(self) -> str:
        """Generate Redis URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    sqlite_path: str = os.getenv("DB_PATH", "tasks.db")
    echo: bool = os.getenv("DB_ECHO", "False").lower() == "true"


@dataclass
class ApiConfig:
    """API configuration."""
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    workers: int = int(os.getenv("API_WORKERS", "1"))


@dataclass
class WorkerConfig:
    """Worker configuration."""
    enabled: bool = os.getenv("WORKER_ENABLED", "True").lower() == "true"
    num_workers: int = int(os.getenv("WORKER_NUM", "1"))
    queue_name: str = os.getenv("QUEUE_NAME", "task_queue")
    task_timeout: int = int(os.getenv("TASK_TIMEOUT", "300"))  # 5 minutes
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    backoff_factor: float = float(os.getenv("BACKOFF_FACTOR", "2.0"))
    poll_interval: float = float(os.getenv("POLL_INTERVAL", "1.0"))


@dataclass
class Config:
    """Main configuration."""
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    redis: RedisConfig = field(default_factory=RedisConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: ApiConfig = field(default_factory=ApiConfig)
    worker: WorkerConfig = field(default_factory=WorkerConfig)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


# Global config instance
config = Config()
