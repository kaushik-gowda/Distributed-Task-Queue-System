"""
Pydantic schemas for API requests and responses.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Any, Dict, Optional, Union
from datetime import datetime
import json

class TaskSubmitRequest(BaseModel):
    """Schema for submitting a new task."""
    
    task_type: str = Field(
        ...,
        description="Type of task (e.g., sleep_task, math_task)",
        example="sleep_task"
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Task-specific payload",
        example={"duration": 5, "message": "Processing"}
    )
    priority: int = Field(
        default=0,
        description="Task priority (higher = more important)",
        ge=0,
        le=100
    )


class TaskResponse(BaseModel):
    """Schema for task response."""
    
    task_id: str
    task_type: str
    status: Any  # Allowing Any temporarily because it's an Enum from DB
    payload: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int
    priority: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @model_validator(mode='before')
    @classmethod
    def parse_json_fields(cls, data: Any) -> Any:
        # data might be a SQLAlchemy model or a dict
        if hasattr(data, '__dict__'):
            # Convert SQLAlchemy objects to dict
            payload = getattr(data, 'payload', None)
            if isinstance(payload, str):
                try:
                    data.payload = json.loads(payload)
                except json.JSONDecodeError:
                    pass
            
            result = getattr(data, 'result', None)
            if isinstance(result, str):
                try:
                    data.result = json.loads(result)
                except json.JSONDecodeError:
                    pass
                    
            # Convert Enum status to string
            status = getattr(data, 'status', None)
            if hasattr(status, 'value'):
                data.status = status.value
            elif hasattr(status, 'name'):
                data.status = status.name
                
        elif isinstance(data, dict):
            # Normal dict mode
            if isinstance(data.get('payload'), str):
                try:
                    data['payload'] = json.loads(data['payload'])
                except json.JSONDecodeError:
                    pass
            if isinstance(data.get('result'), str):
                try:
                    data['result'] = json.loads(data['result'])
                except json.JSONDecodeError:
                    pass
            
            status = data.get('status')
            if hasattr(status, 'value'):
                data['status'] = status.value
            elif hasattr(status, 'name'):
                data['status'] = status.name

        return data
        
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for listing tasks."""
    
    tasks: list[TaskResponse]
    total: int
    limit: int


class QueueStatsResponse(BaseModel):
    """Schema for queue statistics."""
    
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_tasks: int


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""
    
    status: str
    timestamp: datetime
    redis_connected: bool
    database_connected: bool
