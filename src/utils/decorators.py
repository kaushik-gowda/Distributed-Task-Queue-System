"""
Decorators and utilities for task execution.
"""

import asyncio
import time
from functools import wraps
from typing import Callable, Any, TypeVar, Optional
from .logger import get_logger

logger = get_logger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
) -> Callable[[F], F]:
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Factor to multiply delay by after each retry
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        exceptions: Tuple of exceptions to catch and retry on
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.debug(f"Executing {func.__name__} (attempt {attempt}/{max_attempts})")
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"Failed to execute {func.__name__} after {max_attempts} attempts: {str(e)}"
                        )
                        raise
                    
                    # Calculate delay with cap
                    current_delay = min(delay, max_delay)
                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}, "
                        f"retrying in {current_delay}s: {str(e)}"
                    )
                    time.sleep(current_delay)
                    delay *= backoff_factor
        
        return wrapper
    
    return decorator


def async_retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
) -> Callable[[F], F]:
    """
    Decorator for retrying async functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Factor to multiply delay by after each retry
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        exceptions: Tuple of exceptions to catch and retry on
    
    Returns:
        Decorated async function with retry logic
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.debug(f"Executing {func.__name__} (attempt {attempt}/{max_attempts})")
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"Failed to execute {func.__name__} after {max_attempts} attempts: {str(e)}"
                        )
                        raise
                    
                    # Calculate delay with cap
                    current_delay = min(delay, max_delay)
                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}, "
                        f"retrying in {current_delay}s: {str(e)}"
                    )
                    await asyncio.sleep(current_delay)
                    delay *= backoff_factor
        
        return wrapper
    
    return decorator
