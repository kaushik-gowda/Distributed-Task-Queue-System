"""
Redis queue broker for task distribution.
"""

import json
import redis
from typing import Optional, List, Dict, Any
from src.config import config
from src.utils import get_logger

logger = get_logger(__name__)


class RedisQueue:
    """Redis-based task queue broker."""
    
    def __init__(self, queue_name: str = "task_queue"):
        """Initialize Redis queue."""
        self.queue_name = queue_name
        self.client: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis."""
        try:
            self.client = redis.from_url(
                config.redis.url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {config.redis.host}:{config.redis.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    def enqueue(self, task_id: str, priority: int = 0) -> bool:
        """
        Enqueue a task to the queue.
        
        Args:
            task_id: Task ID to queue
            priority: Priority level (higher = more important)
        
        Returns:
            True if successfully enqueued
        """
        try:
            # Store task ID with priority as score for sorted set
            # This allows us to prioritize tasks
            queue_key = f"{self.queue_name}:pending"
            self.client.zadd(queue_key, {task_id: priority})
            logger.debug(f"Enqueued task {task_id} with priority {priority}")
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue task {task_id}: {str(e)}")
            return False
    
    def dequeue(self, count: int = 1) -> List[str]:
        """
        Dequeue tasks from the queue.
        Tasks are retrieved in priority order (highest first).
        
        Args:
            count: Number of tasks to dequeue
        
        Returns:
            List of task IDs
        """
        try:
            queue_key = f"{self.queue_name}:pending"
            # Get highest priority tasks (using zrevrange - reverse order)
            task_ids = self.client.zrevrange(queue_key, 0, count - 1)
            
            if task_ids:
                # Remove from pending queue
                self.client.zremrangebyrank(queue_key, -count, -1)
                logger.debug(f"Dequeued {len(task_ids)} tasks")
            
            return list(task_ids)
        except Exception as e:
            logger.error(f"Failed to dequeue tasks: {str(e)}")
            return []
    
    def get_queue_size(self) -> int:
        """Get the number of pending tasks in queue."""
        try:
            queue_key = f"{self.queue_name}:pending"
            size = self.client.zcard(queue_key)
            return size
        except Exception as e:
            logger.error(f"Failed to get queue size: {str(e)}")
            return 0
    
    def set_task_state(
        self,
        task_id: str,
        state: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Set task state in Redis (for tracking execution).
        
        Args:
            task_id: Task ID
            state: Task state (queued, processing, completed, failed)
            data: Optional metadata about the task
        
        Returns:
            True if successful
        """
        try:
            key = f"{self.queue_name}:task:{task_id}"
            state_data = {"state": str(state)}
            
            if data:
                # Ensure all values in mapping are strings
                for k, v in data.items():
                    try:
                        if isinstance(v, str):
                            state_data[k] = v
                        elif isinstance(v, (dict, list)):
                            state_data[k] = json.dumps(v)
                        elif v is None:
                            state_data[k] = ""
                        else:
                            state_data[k] = str(v)
                    except Exception as convert_err:
                        logger.warning(f"Could not convert {k}={v}: {convert_err}, skipping")
                        continue
            
            # Simple approach: use individual HSET calls instead of mapping
            # This is more compatible with different redis-py versions
            for field, value in state_data.items():
                self.client.hset(key, field, value)
            
            # Set expiration to 7 days
            self.client.expire(key, 7 * 24 * 60 * 60)
            logger.debug(f"Set state for task {task_id}: {state}")
            return True
        except Exception as e:
            logger.error(f"Failed to set task state: {str(e)}")
            return False
    
    def get_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task state from Redis."""
        try:
            key = f"{self.queue_name}:task:{task_id}"
            data = self.client.hgetall(key)
            return data if data else None
        except Exception as e:
            logger.error(f"Failed to get task state: {str(e)}")
            return None
    
    def delete_task_state(self, task_id: str) -> bool:
        """Delete task state from Redis."""
        try:
            key = f"{self.queue_name}:task:{task_id}"
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete task state: {str(e)}")
            return False
    
    def flush_queue(self) -> bool:
        """Flush all tasks from queue (use with caution)."""
        try:
            queue_key = f"{self.queue_name}:pending"
            self.client.delete(queue_key)
            logger.warning("Flushed task queue")
            return True
        except Exception as e:
            logger.error(f"Failed to flush queue: {str(e)}")
            return False
    
    def close(self):
        """Close Redis connection."""
        if self.client:
            self.client.close()
            logger.info("Closed Redis connection")


# Global queue instance
_queue_instance: Optional[RedisQueue] = None


def get_queue(queue_name: str = config.worker.queue_name) -> RedisQueue:
    """Get or create global queue instance."""
    global _queue_instance
    
    if _queue_instance is None:
        _queue_instance = RedisQueue(queue_name)
    
    return _queue_instance


def close_queue():
    """Close global queue instance."""
    global _queue_instance
    if _queue_instance:
        _queue_instance.close()
        _queue_instance = None
