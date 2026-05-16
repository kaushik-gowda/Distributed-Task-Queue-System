"""
API endpoint handlers for the task queue system.
"""

import json
import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session

from .schemas import (
    TaskSubmitRequest,
    TaskResponse,
    TaskListResponse,
    QueueStatsResponse,
    HealthCheckResponse,
)
from src.db import TaskRepository, TaskStatus, get_session
from src.queue import get_queue
from src.utils import get_logger
from src.tasks import TASK_REGISTRY

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["tasks"])


@router.post("/task", response_model=TaskResponse, status_code=201)
def submit_task(request: TaskSubmitRequest) -> TaskResponse:
    """
    Submit a new task to the queue.
    
    Args:
        request: Task submission request
    
    Returns:
        Created task details
    
    Raises:
        HTTPException: If task type is invalid or task creation fails
    """
    # Validate task type
    if request.task_type not in TASK_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task type: {request.task_type}. "
            f"Available types: {list(TASK_REGISTRY.keys())}"
        )
    
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Create task in database
        session = get_session()
        try:
            task = TaskRepository.create_task(
                session=session,
                task_id=task_id,
                task_type=request.task_type,
                payload=json.dumps(request.payload),
                priority=request.priority,
            )
            
            # Enqueue task to Redis
            queue = get_queue()
            queue.enqueue(task_id, priority=request.priority)
            
            logger.info(f"Task submitted: {task_id} (type: {request.task_type})")
            
            return TaskResponse.model_validate(task)
        finally:
            session.close()
    
    except Exception as e:
        logger.error(f"Failed to submit task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit task: {str(e)}"
        )


@router.get("/task/{task_id}", response_model=TaskResponse)
def get_task(task_id: str) -> TaskResponse:
    """
    Get task status and details.
    
    Args:
        task_id: Task ID to retrieve
    
    Returns:
        Task details
    
    Raises:
        HTTPException: If task not found
    """
    session = get_session()
    try:
        task = TaskRepository.get_task(session, task_id)
        
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Task not found: {task_id}"
            )
        
        return TaskResponse.model_validate(task)
    finally:
        session.close()


@router.get("/tasks", response_model=TaskListResponse)
def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Number of tasks to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> TaskListResponse:
    """
    List tasks with optional filtering and pagination.
    
    Args:
        status: Optional status filter
        limit: Number of tasks to return
        offset: Offset for pagination
    
    Returns:
        List of tasks
    """
    session = get_session()
    try:
        query = session.query(src.db.Task)
        
        if status:
            try:
                status_enum = TaskStatus(status)
                query = query.filter(src.db.Task.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status}"
                )
        
        total = query.count()
        tasks = query.order_by(src.db.Task.created_at.desc()).offset(offset).limit(limit).all()
        
        return TaskListResponse(
            tasks=[TaskResponse.model_validate(task) for task in tasks],
            total=total,
            limit=limit,
        )
    finally:
        session.close()


@router.get("/stats", response_model=QueueStatsResponse)
def get_queue_stats() -> QueueStatsResponse:
    """
    Get queue and task statistics.
    
    Returns:
        Queue statistics
    """
    session = get_session()
    try:
        from src.db import Task
        
        pending = session.query(Task).filter(Task.status == TaskStatus.PENDING).count()
        running = session.query(Task).filter(Task.status == TaskStatus.RUNNING).count()
        completed = session.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
        failed = session.query(Task).filter(Task.status == TaskStatus.FAILED).count()
        total = session.query(Task).count()
        
        return QueueStatsResponse(
            pending_tasks=pending,
            running_tasks=running,
            completed_tasks=completed,
            failed_tasks=failed,
            total_tasks=total,
        )
    finally:
        session.close()


@router.get("/health", response_model=HealthCheckResponse)
def health_check() -> HealthCheckResponse:
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    redis_connected = False
    database_connected = False
    
    # Check Redis
    try:
        queue = get_queue()
        if queue.client:
            queue.client.ping()
            redis_connected = True
    except Exception as e:
        logger.warning(f"Redis health check failed: {str(e)}")
    
    # Check database
    try:
        from sqlalchemy import text
        session = get_session()
        session.execute(text("SELECT 1"))
        session.close()
        database_connected = True
    except Exception as e:
        logger.warning(f"Database health check failed: {str(e)}")
    
    status = "healthy" if (redis_connected and database_connected) else "degraded"
    
    return HealthCheckResponse(
        status=status,
        timestamp=datetime.utcnow(),
        redis_connected=redis_connected,
        database_connected=database_connected,
    )


# Import Task here to avoid circular imports
from src.db import Task
