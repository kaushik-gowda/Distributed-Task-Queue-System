"""
Worker process entry point for the distributed task queue system.
Runs multiple worker thread/process instances to process queued tasks.
"""

import signal
import sys
from multiprocessing import Process
from threading import Thread

from src.config import config
from src.utils import setup_logging
from src.db import init_db
from src.worker import TaskWorker

# Setup logging
logger = setup_logging(__name__, level=config.log_level)

# Global worker instances
workers = []


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down workers")
    stop_all_workers()
    sys.exit(0)


def stop_all_workers():
    """Stop all running workers."""
    for worker in workers:
        if isinstance(worker, Process):
            if worker.is_alive():
                worker.terminate()
                worker.join(timeout=5)
                if worker.is_alive():
                    worker.kill()
        elif isinstance(worker, Thread):
            if worker.is_alive():
                # Threads don't have terminate, we rely on daemon=True
                pass


def run_worker_thread(worker_id: str):
    """
    Run a worker in a thread.
    
    Args:
        worker_id: Worker identifier
    """
    logger.info(f"Starting worker thread: {worker_id}")
    worker = TaskWorker(worker_id=worker_id)
    
    try:
        worker.run()
    except Exception as e:
        logger.error(f"Worker {worker_id} failed: {str(e)}")


def start_workers(num_workers: int = 1, use_threads: bool = True):
    """
    Start multiple worker instances.
    
    Args:
        num_workers: Number of workers to start
        use_threads: Use threads instead of processes (default: True for simplicity)
    """
    logger.info(f"Starting {num_workers} worker(s)")
    
    for i in range(num_workers):
        worker_id = f"worker-{i+1}"
        
        if use_threads:
            # Use threading for simplicity (single machine)
            worker_thread = Thread(
                target=run_worker_thread,
                args=(worker_id,),
                daemon=False
            )
            worker_thread.start()
            workers.append(worker_thread)
        else:
            # Use multiprocessing for true parallelism
            worker_process = Process(
                target=run_worker_thread,
                args=(worker_id,)
            )
            worker_process.start()
            workers.append(worker_process)
    
    logger.info(f"Started {num_workers} worker(s)")


def main():
    """Main worker entry point."""
    logger.info("=" * 60)
    logger.info("Distributed Task Queue Worker")
    logger.info("=" * 60)
    
    # Initialize database
    init_db()
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Determine if we should use threads or processes
    # For development and single machines, threads are simpler
    # For production with multiple machines, processes are better
    use_threads = True
    
    # Start worker instances
    num_workers = config.worker.num_workers
    start_workers(num_workers=num_workers, use_threads=use_threads)
    
    # Wait for all workers to complete
    try:
        for worker in workers:
            if isinstance(worker, Thread):
                worker.join()
            else:
                worker.join()
    except KeyboardInterrupt:
        logger.info("Interrupted, stopping workers")
        stop_all_workers()


if __name__ == "__main__":
    main()
