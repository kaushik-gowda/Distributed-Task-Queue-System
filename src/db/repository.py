"""
Task repository for database operations.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from .models import Task, TaskStatus
from src.utils import get_logger

logger = get_logger(__name__)


class TaskRepository:
    """Repository for task database operations."""
    
    @staticmethod
    def create_task(
        session: Session,
        task_id: str,
        task_type: str,
        payload: str,
        priority: int = 0
    ) -> Task:
        """Create a new task."""
        task = Task(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            payload=payload,
            priority=priority,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(task)
        session.commit()
        logger.info(f"Created task: {task_id} of type {task_type}")
        return task
    
    @staticmethod
    def get_task(session: Session, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return session.query(Task).filter(Task.task_id == task_id).first()
    
    @staticmethod
    def update_task_status(
        session: Session,
        task_id: str,
        status: TaskStatus,
        result: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[Task]:
        """Update task status and result."""
        task = TaskRepository.get_task(session, task_id)
        if not task:
            logger.warning(f"Task not found: {task_id}")
            return None
        
        task.status = status
        task.updated_at = datetime.utcnow()
        
        if status == TaskStatus.RUNNING and not task.started_at:
            task.started_at = datetime.utcnow()
        elif status == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
            if result:
                task.result = result
        elif status == TaskStatus.FAILED:
            task.completed_at = datetime.utcnow()
            if error_message:
                task.error_message = error_message
        elif status == TaskStatus.RETRYING:
            task.retry_count += 1
        
        session.add(task)
        session.commit()
        logger.info(f"Updated task {task_id} status to {status}")
        return task
    
    @staticmethod
    def get_pending_tasks(session: Session, limit: int = 10) -> List[Task]:
        """Get pending tasks ordered by priority."""
        return (
            session.query(Task)
            .filter(Task.status == TaskStatus.PENDING)
            .order_by(Task.priority.desc(), Task.created_at.asc())
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def get_retrying_tasks(session: Session, limit: int = 10) -> List[Task]:
        """Get tasks that are ready to retry."""
        return (
            session.query(Task)
            .filter(Task.status == TaskStatus.RETRYING)
            .order_by(Task.priority.desc(), Task.updated_at.asc())
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def get_tasks_by_status(
        session: Session,
        status: TaskStatus,
        limit: int = 100
    ) -> List[Task]:
        """Get tasks by status."""
        return (
            session.query(Task)
            .filter(Task.status == status)
            .order_by(Task.created_at.desc())
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def mark_task_running(session: Session, task_id: str) -> Optional[Task]:
        """Mark task as running."""
        return TaskRepository.update_task_status(
            session,
            task_id,
            TaskStatus.RUNNING
        )
    
    @staticmethod
    def mark_task_completed(
        session: Session,
        task_id: str,
        result: str
    ) -> Optional[Task]:
        """Mark task as completed with result."""
        return TaskRepository.update_task_status(
            session,
            task_id,
            TaskStatus.COMPLETED,
            result=result
        )
    
    @staticmethod
    def mark_task_failed(
        session: Session,
        task_id: str,
        error_message: str
    ) -> Optional[Task]:
        """Mark task as failed with error message."""
        return TaskRepository.update_task_status(
            session,
            task_id,
            TaskStatus.FAILED,
            error_message=error_message
        )
    
    @staticmethod
    def mark_task_retrying(session: Session, task_id: str) -> Optional[Task]:
        """Mark task as retrying."""
        return TaskRepository.update_task_status(
            session,
            task_id,
            TaskStatus.RETRYING
        )
