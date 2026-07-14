"""
Database models for the task queue system.
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum
import uuid

Base = declarative_base()


class TaskStatus(str, enum.Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class Task(Base):
    """Task model for storing task metadata."""
    
    __tablename__ = "tasks"
    
    task_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_type = Column(String(100), nullable=False, index=True)
    status = Column(
        SQLEnum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING,
        index=True
    )
    payload = Column(Text, nullable=True)  # JSON string
    result = Column(Text, nullable=True)  # JSON string
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    priority = Column(Integer, nullable=False, default=0)  # Higher = more important
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return (
            f"<Task(id={self.task_id}, type={self.task_type}, "
            f"status={self.status}, created_at={self.created_at})>"
        )
