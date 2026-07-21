"""
Worker task executor for processing queued tasks.
"""

import json
import time
from typing import Optional
from datetime import datetime

from src.db import TaskRepository, TaskStatus, get_session_context
from src.queue import get_queue
from src.utils import get_logger, async_retry
from src.tasks import execute_task
from src.config import config

logger = get_logger(__name__)


class TaskWorker:
    """Worker for executing tasks from the queue."""
    
    def __init__(self, worker_id: str = "default"):
        """Initialize task worker."""
        self.worker_id = worker_id
        self.queue = get_queue()
        self.running = False
        self.processed_count = 0
    
    def execute_task(self, task_id: str) -> bool:
        """
        Execute a single task.
        
        Args:
            task_id: Task ID to execute
        
        Returns:
            True if task executed successfully, False otherwise
        """
        logger.info(f"[{self.worker_id}] Processing task: {task_id}")
        
        # First, get task details and mark as running
        task_type = None
        payload_str = None
        
        with get_session_context() as session:
            task = TaskRepository.get_task(session, task_id)
            if not task:
                logger.error(f"Task not found: {task_id}")
                return False
            
            # Extract data before session closes
            task_type = task.task_type
            payload_str = task.payload
            
            # Mark as running and commit this update
            TaskRepository.mark_task_running(session, task_id)
            self.queue.set_task_state(task_id, "running")
        
        # Execute task outside of the context manager to avoid rollback on failure
        try:
            # Parse payload (extracted before session closed)
            payload = json.loads(payload_str) if payload_str else {}
            
            # Execute task (outside DB context to avoid rollback on failure)
            logger.info(f"[{self.worker_id}] Executing {task_type} task: {task_id}")
            result = execute_task(task_type, payload)
            
            # Mark as completed in separate transaction
            with get_session_context() as session:
                TaskRepository.mark_task_completed(
                    session,
                    task_id,
                    json.dumps(result)
                )
                self.queue.set_task_state(task_id, "completed", {"result": json.dumps(result)})
            
            logger.info(
                f"[{self.worker_id}] Task completed successfully: {task_id}"
            )
            self.processed_count += 1
            return True
        
        except Exception as e:
            logger.error(f"[{self.worker_id}] Task execution failed: {str(e)}")
            error_msg = str(e)
            
            # Handle failure/retry in separate transaction
            with get_session_context() as session:
                task = TaskRepository.get_task(session, task_id)
                if not task:
                    return False
                
                # Check if we should retry
                if task.retry_count < config.worker.max_retries:
                    logger.info(
                        f"[{self.worker_id}] Retrying task {task_id} "
                        f"({task.retry_count + 1}/{config.worker.max_retries})"
                    )
                    
                    TaskRepository.mark_task_retrying(session, task_id)
                    self.queue.set_task_state(
                        task_id,
                        "retrying",
                        {"retry_count": str(task.retry_count + 1), "error": error_msg}
                    )
                    
                    # Re-enqueue task with same priority
                    self.queue.enqueue(task_id, priority=task.priority)
                else:
                    logger.error(
                        f"[{self.worker_id}] Task failed permanently after "
                        f"{config.worker.max_retries} retries: {task_id}"
                    )
                    
                    TaskRepository.mark_task_failed(session, task_id, error_msg)
                    self.queue.set_task_state(
                        task_id,
                        "failed",
                        {"error": error_msg, "retry_count": str(task.retry_count)}
                    )
            
            return False
    
    def process_pending_tasks(self, batch_size: int = 10) -> int:
        """
        Process pending tasks from queue.
        
        Args:
            batch_size: Number of tasks to process in one batch
        
        Returns:
            Number of tasks processed
        """
        # Dequeue tasks
        task_ids = self.queue.dequeue(count=batch_size)
        
        if not task_ids:
            return 0
        
        logger.info(f"[{self.worker_id}] Processing batch of {len(task_ids)} tasks")
        
        processed = 0
        for task_id in task_ids:
            try:
                if self.execute_task(task_id):
                    processed += 1
            except Exception as e:
                logger.error(f"[{self.worker_id}] Unexpected error processing task: {str(e)}")
        
        return processed
    
    def process_retrying_tasks(self, batch_size: int = 5) -> int:
        """
        Process tasks that are ready to retry.
        
        Args:
            batch_size: Number of tasks to process
        
        Returns:
            Number of tasks processed
        """
        with get_session_context() as session:
            retrying_tasks = TaskRepository.get_retrying_tasks(session, limit=batch_size)
            
            if not retrying_tasks:
                return 0
            
            logger.info(
                f"[{self.worker_id}] Processing {len(retrying_tasks)} retrying tasks"
            )
            
            processed = 0
            for task in retrying_tasks:
                try:
                    # Update status back to pending and re-enqueue
                    TaskRepository.update_task_status(
                        session,
                        task.task_id,
                        TaskStatus.PENDING
                    )
                    self.queue.enqueue(task.task_id, priority=task.priority)
                    processed += 1
                except Exception as e:
                    logger.error(
                        f"[{self.worker_id}] Error processing retry for {task.task_id}: {str(e)}"
                    )
            
            return processed
    
    def run(self, poll_interval: Optional[float] = None):
        """
        Run worker loop that continuously processes tasks.
        
        Args:
            poll_interval: Interval to poll for tasks in seconds
        """
        if poll_interval is None:
            poll_interval = config.worker.poll_interval
        
        logger.info(f"[{self.worker_id}] Worker started")
        self.running = True
        
        try:
            while self.running:
                try:
                    # Process pending tasks
                    processed = self.process_pending_tasks(batch_size=10)
                    
                    # Process retrying tasks
                    retrying = self.process_retrying_tasks(batch_size=5)
                    
                    # Sleep if no tasks were processed
                    if processed == 0 and retrying == 0:
                        logger.debug(f"[{self.worker_id}] Queue empty, sleeping")
                        time.sleep(poll_interval)
                    
                except KeyboardInterrupt:
                    logger.info(f"[{self.worker_id}] Received interrupt signal")
                    break
                except Exception as e:
                    logger.error(f"[{self.worker_id}] Unexpected error in worker loop: {str(e)}")
                    time.sleep(poll_interval)
        finally:
            logger.info(
                f"[{self.worker_id}] Worker stopped. "
                f"Total tasks processed: {self.processed_count}"
            )
            self.running = False
    
    def stop(self):
        """Stop the worker."""
        logger.info(f"[{self.worker_id}] Stopping worker")
        self.running = False
