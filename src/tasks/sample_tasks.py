"""
Sample task implementations for the task queue system.
"""

import time
import json
from typing import Any, Dict
from src.utils import get_logger

logger = get_logger(__name__)


class TaskExecutor:
    """Base class for task executors."""
    
    @staticmethod
    def execute(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute task.
        
        Args:
            payload: Task payload
        
        Returns:
            Task result as dictionary
        
        Raises:
            Exception: If task execution fails
        """
        raise NotImplementedError


class SleepTask(TaskExecutor):
    """
    Simulates a long-running task by sleeping.
    
    Payload format:
    {
        "duration": 5,  # Seconds to sleep
        "message": "Processing..."  # Optional message
    }
    """
    
    @staticmethod
    def execute(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sleep task."""
        duration = payload.get("duration", 5)
        message = payload.get("message", "Processing...")
        
        logger.info(f"Starting sleep task for {duration} seconds: {message}")
        
        # Simulate work by sleeping
        for i in range(duration):
            time.sleep(1)
            logger.debug(f"Sleep progress: {i+1}/{duration}")
        
        result = {
            "status": "success",
            "message": f"Slept for {duration} seconds",
            "duration": duration,
            "original_message": message
        }
        
        logger.info(f"Sleep task completed: {result}")
        return result


class MathTask(TaskExecutor):
    """
    Performs mathematical computations.
    
    Payload format:
    {
        "operation": "add|subtract|multiply|divide",
        "operands": [10, 5],  # List of numbers
    }
    """
    
    @staticmethod
    def execute(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute math task."""
        operation = payload.get("operation")
        operands = payload.get("operands", [])
        
        if not operation or not operands:
            raise ValueError("Missing 'operation' or 'operands' in payload")
        
        logger.info(f"Executing math task: {operation} on {operands}")
        
        try:
            if operation == "add":
                result = sum(operands)
            elif operation == "subtract":
                result = operands[0]
                for num in operands[1:]:
                    result -= num
            elif operation == "multiply":
                result = 1
                for num in operands:
                    result *= num
            elif operation == "divide":
                result = operands[0]
                for num in operands[1:]:
                    if num == 0:
                        raise ValueError("Division by zero")
                    result /= num
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            return {
                "status": "success",
                "operation": operation,
                "operands": operands,
                "result": result
            }
        except Exception as e:
            logger.error(f"Math task failed: {str(e)}")
            raise


class DataProcessingTask(TaskExecutor):
    """
    Processes and transforms data.
    
    Payload format:
    {
        "data": [1, 2, 3, 4, 5],
        "action": "sum|average|unique"
    }
    """
    
    @staticmethod
    def execute(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data processing task."""
        data = payload.get("data", [])
        action = payload.get("action", "sum")
        
        logger.info(f"Processing data: {action} on {len(data)} items")
        
        try:
            if action == "sum":
                result = sum(data)
            elif action == "average":
                result = sum(data) / len(data) if data else 0
            elif action == "unique":
                result = len(set(data))
            else:
                raise ValueError(f"Unknown action: {action}")
            
            return {
                "status": "success",
                "action": action,
                "data_count": len(data),
                "result": result
            }
        except Exception as e:
            logger.error(f"Data processing task failed: {str(e)}")
            raise


# Task registry mapping task types to executors
TASK_REGISTRY: Dict[str, type] = {
    "sleep_task": SleepTask,
    "math_task": MathTask,
    "data_processing_task": DataProcessingTask,
}


def get_task_executor(task_type: str) -> type:
    """
    Get task executor class for given task type.
    
    Args:
        task_type: Type of task
    
    Returns:
        TaskExecutor subclass
    
    Raises:
        ValueError: If task type is not registered
    """
    if task_type not in TASK_REGISTRY:
        raise ValueError(
            f"Unknown task type: {task_type}. "
            f"Available: {list(TASK_REGISTRY.keys())}"
        )
    
    return TASK_REGISTRY[task_type]


def execute_task(task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a task by its type.
    
    Args:
        task_type: Type of task
        payload: Task payload
    
    Returns:
        Task result
    
    Raises:
        ValueError: If task type is unknown
        Exception: If task execution fails
    """
    executor_class = get_task_executor(task_type)
    logger.info(f"Executing {task_type} task")
    return executor_class.execute(payload)
