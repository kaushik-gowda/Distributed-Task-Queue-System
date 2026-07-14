#!/usr/bin/env python
"""
Quick testing script for the distributed task queue system.
Run this after starting the API server and worker(s).
"""

import requests
import json
import time
from typing import Optional
import sys

BASE_URL = "http://localhost:8000/api"

class bcolors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print a colored header."""
    print(f"\n{bcolors.HEADER}{bcolors.BOLD}{'='*60}")
    print(f"{text:^60}")
    print(f"{'='*60}{bcolors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{bcolors.OKGREEN}✓ {text}{bcolors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{bcolors.FAIL}✗ {text}{bcolors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{bcolors.OKCYAN}ℹ {text}{bcolors.ENDC}")


def submit_task(task_type: str, payload: dict, priority: int = 0) -> Optional[str]:
    """Submit a task and return task_id."""
    try:
        response = requests.post(
            f"{BASE_URL}/task",
            json={
                "task_type": task_type,
                "payload": payload,
                "priority": priority
            }
        )
        
        if response.status_code == 201:
            task_id = response.json()["task_id"]
            print_success(f"Task submitted: {task_id}")
            return task_id
        else:
            print_error(f"Failed to submit task: {response.json()}")
            return None
    except Exception as e:
        print_error(f"Error submitting task: {str(e)}")
        return None


def get_task_status(task_id: str) -> Optional[dict]:
    """Get task status."""
    try:
        response = requests.get(f"{BASE_URL}/task/{task_id}")
        if response.status_code == 200:
            return response.json()
        else:
            print_error(f"Failed to get task: {response.json()}")
            return None
    except Exception as e:
        print_error(f"Error getting task: {str(e)}")
        return None


def wait_for_task(task_id: str, timeout: int = 60) -> Optional[dict]:
    """Wait for task to complete."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        task = get_task_status(task_id)
        
        if not task:
            return None
        
        status = task["status"]
        
        if status in ["completed", "failed"]:
            return task
        
        print_info(f"Task status: {status}... waiting")
        time.sleep(2)
    
    print_error(f"Task did not complete within {timeout} seconds")
    return None


def print_task_result(task: dict):
    """Print task result nicely."""
    print(f"\n{bcolors.BOLD}Task Details:{bcolors.ENDC}")
    print(f"  Task ID:        {task['task_id']}")
    print(f"  Type:           {task['task_type']}")
    print(f"  Status:         {bcolors.OKGREEN if task['status'] == 'completed' else bcolors.FAIL}{task['status']}{bcolors.ENDC}")
    print(f"  Created:        {task['created_at']}")
    print(f"  Updated:        {task['updated_at']}")
    
    if task['started_at']:
        print(f"  Started:        {task['started_at']}")
    
    if task['completed_at']:
        print(f"  Completed:      {task['completed_at']}")
    
    if task['retry_count'] > 0:
        print(f"  Retries:        {task['retry_count']}")
    
    if task['result']:
        print(f"  Result:         {json.dumps(task['result'], indent=2)}")
    
    if task['error_message']:
        print(f"  Error:          {bcolors.FAIL}{task['error_message']}{bcolors.ENDC}")


def test_health():
    """Test health endpoint."""
    print_header("Testing Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            health = response.json()
            print_success(f"System status: {health['status']}")
            print_info(f"Redis connected: {health['redis_connected']}")
            print_info(f"Database connected: {health['database_connected']}")
            return True
        else:
            print_error("Health check failed")
            return False
    except Exception as e:
        print_error(f"Error checking health: {str(e)}")
        return False


def test_sleep_task():
    """Test sleep task."""
    print_header("Testing Sleep Task")
    
    task_id = submit_task(
        "sleep_task",
        {"duration": 3, "message": "Test sleep"},
        priority=1
    )
    
    if not task_id:
        return False
    
    print_info("Waiting for task to complete...")
    task = wait_for_task(task_id, timeout=15)
    
    if task:
        print_task_result(task)
        return task['status'] == 'completed'
    
    return False


def test_math_task():
    """Test math task."""
    print_header("Testing Math Task (Addition)")
    
    task_id = submit_task(
        "math_task",
        {"operation": "add", "operands": [10, 20, 30]},
        priority=2
    )
    
    if not task_id:
        return False
    
    print_info("Waiting for task to complete...")
    task = wait_for_task(task_id)
    
    if task:
        print_task_result(task)
        if task['status'] == 'completed' and task['result']['result'] == 60:
            print_success("Math result is correct: 10 + 20 + 30 = 60")
            return True
    
    return False


def test_priority():
    """Test task priority."""
    print_header("Testing Task Priority")
    
    # Submit low priority task
    low_priority_id = submit_task(
        "sleep_task",
        {"duration": 2},
        priority=0
    )
    
    time.sleep(0.5)
    
    # Submit high priority task
    high_priority_id = submit_task(
        "math_task",
        {"operation": "multiply", "operands": [5, 10]},
        priority=10
    )
    
    if not (low_priority_id and high_priority_id):
        return False
    
    print_info("Waiting for tasks to complete...")
    
    # High priority task should complete first despite being submitted later
    high_priority_task = wait_for_task(high_priority_id, timeout=10)
    low_priority_task = wait_for_task(low_priority_id, timeout=10)
    
    if high_priority_task and low_priority_task:
        print_success("Both tasks completed")
        return True
    
    return False


def test_queue_stats():
    """Test queue statistics."""
    print_header("Testing Queue Statistics")
    
    try:
        response = requests.get(f"{BASE_URL}/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"\n{bcolors.BOLD}Queue Statistics:{bcolors.ENDC}")
            print(f"  Pending:    {stats['pending_tasks']}")
            print(f"  Running:    {stats['running_tasks']}")
            print(f"  Completed:  {stats['completed_tasks']}")
            print(f"  Failed:     {stats['failed_tasks']}")
            print(f"  Total:      {stats['total_tasks']}")
            print_success("Queue stats retrieved")
            return True
        else:
            print_error("Failed to get queue stats")
            return False
    except Exception as e:
        print_error(f"Error getting queue stats: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n" + bcolors.BOLD + "=" * 60)
    print("Distributed Task Queue System - Test Suite".center(60))
    print("=" * 60 + bcolors.ENDC)
    
    # Test connectivity
    print_header("Checking Connectivity")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print_success("API server is accessible")
    except Exception as e:
        print_error(f"Cannot connect to API server at {BASE_URL}")
        print_error(f"Error: {str(e)}")
        print("\nMake sure to:")
        print("1. Start Redis: redis-server")
        print("2. Start API: python main.py")
        print("3. Start Worker: python worker_main.py")
        sys.exit(1)
    
    results = {}
    
    # Run tests
    results['Health'] = test_health()
    results['Sleep Task'] = test_sleep_task()
    results['Math Task'] = test_math_task()
    results['Priority'] = test_priority()
    results['Queue Stats'] = test_queue_stats()
    
    # Print results summary
    print_header("Test Results Summary")
    
    for test_name, passed in results.items():
        status = f"{bcolors.OKGREEN}PASSED{bcolors.ENDC}" if passed else f"{bcolors.FAIL}FAILED{bcolors.ENDC}"
        print(f"  {test_name:.<40} {status}")
    
    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)
    
    print(f"\n{bcolors.BOLD}Total: {passed_count}/{total_count} tests passed{bcolors.ENDC}")
    
    if passed_count == total_count:
        print_success("All tests passed!")
        return 0
    else:
        print_error("Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
