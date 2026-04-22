# Distributed Task Queue System

A production-grade distributed task queue system built with **Python**, **FastAPI**, **Redis**, and **SQLite**. This system allows you to submit long-running or computationally heavy tasks asynchronously and track their status in real-time.

## Features

- ✅ **FastAPI REST API** for task submission and status tracking
- ✅ **Real-Time Web Dashboard** for visual task management (no CLI needed!)
- ✅ **Redis** as a message broker for task distribution
- ✅ **Async Task Execution** with worker processes
- ✅ **Task Priority Support** for prioritizing important tasks
- ✅ **Automatic Retry Logic** with exponential backoff (max 3 retries by default)
- ✅ **Task Status Tracking** (pending, running, completed, failed, retrying)
- ✅ **SQLite Database** for persistent task metadata storage
- ✅ **PostgreSQL Ready** for production deployments
- ✅ **Sample Tasks** included (sleep_task, math_task, data_processing_task)
- ✅ **Comprehensive Logging** for task execution lifecycle
- ✅ **Docker Support** with docker-compose for easy deployment
- ✅ **Production-Ready Code** with proper error handling and separation of concerns
- ✅ **Health Check Endpoint** to monitor system status

## Project Structure

```
Distributed-Task-Queue-System/
├── src/
│   ├── api/                 # FastAPI handlers and schemas
│   │   ├── handlers.py      # API endpoint handlers
│   │   ├── schemas.py       # Pydantic request/response models
│   │   └── __init__.py
│   ├── db/                  # Database layer
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── connection.py    # Database connection management
│   │   ├── repository.py    # Task repository (DAO pattern)
│   │   └── __init__.py
│   ├── queue/               # Message queue layer
│   │   ├── broker.py        # Redis queue implementation
│   │   └── __init__.py
│   ├── tasks/               # Task implementations
│   │   ├── sample_tasks.py  # Sample task executors
│   │   └── __init__.py
│   ├── worker/              # Worker process
│   │   ├── executor.py      # Task executor logic
│   │   └── __init__.py
│   ├── utils/               # Utilities
│   │   ├── logger.py        # Logging setup
│   │   ├── decorators.py    # Retry decorators
│   │   └── __init__.py
│   ├── config.py            # Configuration management
│   └── __init__.py
├── docker/                  # Docker configuration
│   └── Dockerfile
├── tests/                   # Test suite (placeholder)
├── main.py                  # FastAPI app entry point
├── worker_main.py           # Worker entry point
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # Docker compose configuration
├── .env.example             # Environment variables example
└── README.md                # This file
```

## Prerequisites

- Python 3.11+
- Redis 5+
- pip or conda

## Installation

### 1. Clone and Setup Virtual Environment

```bash
cd "Distributed Task Queue System"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# Default values should work for local development
```

## Running the System

### Option 1: Local Development (Recommended for Testing)

You'll need to run three components in separate terminals:

#### Terminal 1: Start Redis

```bash
# Make sure Redis is installed and running
# On Windows (if using Windows Subsystem for Linux or installed Redis):
redis-server

# On macOS (with Homebrew):
brew services start redis

# Or using Docker:
docker run -d -p 6379:6379 redis:7-alpine
```

#### Terminal 2: Start FastAPI Server

```bash
# Activate virtual environment first
python main.py
```

The API will be available at: `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

#### Terminal 3: Start Worker(s)

```bash
# Activate virtual environment first
python worker_main.py
```

You can start multiple workers in different terminals to increase throughput:
```bash
WORKER_NUM=2 python worker_main.py
```

## Testing the System (Local 3-Terminal Setup)

To verify the system is working flawlessly on Windows, open **3 separate PowerShell terminals** and run the following matching commands. Ensure Redis (or Memurai) is already running in your background.

### Terminal 1: Start the API Server
```powershell
cd "e:\Distributed Task Queue System"
.\.venv\Scripts\activate.ps1
python main.py
```

### Terminal 2: Start the Worker
```powershell
cd "e:\Distributed Task Queue System"
.\.venv\Scripts\activate.ps1
python worker_main.py
```

### Terminal 3: Open the Dashboard
Once Terminals 1 and 2 are running, open your browser and go to:

**[http://localhost:8000](http://localhost:8000)**

You'll see a modern, real-time web dashboard where you can:
- 📊 View live queue statistics (Pending, Running, Completed, Failed tasks)
- ✉️ Submit new tasks with a visual form (no JSON/CLI needed!)
- 📈 Monitor task progress in real-time
- 🎯 Set task priorities (0-100)
- 🔍 Filter and search task history

**For a detailed guide on using the dashboard, see [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md)**

*Note: When updating any code, pause (`Ctrl+C`) and re-run the commands in Terminals 1 and 2 before refreshing Terminal 3 dashboard.*

### Option 2: Docker Compose (Recommended for Production)

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop all services
docker-compose down
```

**Scale workers as needed:**
```bash
docker-compose up -d --scale worker=3
```

## API Endpoints

### Base URL: `http://localhost:8000/api`

### 1. Submit a Task
```
POST /task
```

**Request:**
```json
{
  "task_type": "sleep_task",
  "payload": {
    "duration": 5,
    "message": "Processing..."
  },
  "priority": 0
}
```

**Response:** (201 Created)
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_type": "sleep_task",
  "status": "pending",
  "payload": {"duration": 5, "message": "Processing..."},
  "result": null,
  "error_message": null,
  "retry_count": 0,
  "priority": 0,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00",
  "started_at": null,
  "completed_at": null
}
```

### 2. Get Task Status
```
GET /task/{task_id}
```

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_type": "sleep_task",
  "status": "completed",
  "payload": {"duration": 5, "message": "Processing..."},
  "result": {
    "status": "success",
    "message": "Slept for 5 seconds",
    "duration": 5,
    "original_message": "Processing..."
  },
  "error_message": null,
  "retry_count": 0,
  "priority": 0,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:05",
  "started_at": "2024-01-15T10:30:00",
  "completed_at": "2024-01-15T10:30:05"
}
```

### 3. List Tasks
```
GET /tasks?status=pending&limit=100&offset=0
```

Query Parameters:
- `status` (optional): Filter by status (pending, running, completed, failed, retrying)
- `limit` (optional): Number of tasks to return (default: 100)
- `offset` (optional): Pagination offset (default: 0)

### 4. Get Queue Statistics
```
GET /stats
```

**Response:**
```json
{
  "pending_tasks": 5,
  "running_tasks": 2,
  "completed_tasks": 45,
  "failed_tasks": 3,
  "total_tasks": 55
}
```

### 5. Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:35:00",
  "redis_connected": true,
  "database_connected": true
}
```

## Sample Tasks

### 1. Sleep Task
Simulates a long-running job by sleeping.

```bash
curl -X POST http://localhost:8000/api/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "sleep_task",
    "payload": {
      "duration": 10,
      "message": "Processing data..."
    },
    "priority": 0
  }'
```

### 2. Math Task
Performs mathematical operations.

```bash
curl -X POST http://localhost:8000/api/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "math_task",
    "payload": {
      "operation": "add",
      "operands": [10, 20, 30]
    },
    "priority": 1
  }'
```

Supported operations: `add`, `subtract`, `multiply`, `divide`

### 3. Data Processing Task
Processes and analyzes data.

```bash
curl -X POST http://localhost:8000/api/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "data_processing_task",
    "payload": {
      "data": [1, 2, 3, 4, 5],
      "action": "sum"
    },
    "priority": 0
  }'
```

Supported actions: `sum`, `average`, `unique`

## Configuration

Edit `.env` file to customize:

```env
# API Server
API_HOST=0.0.0.0           # Server host
API_PORT=8000              # Server port
API_WORKERS=1              # Number of API workers

# Redis
REDIS_HOST=localhost       # Redis host
REDIS_PORT=6379            # Redis port
REDIS_DB=0                 # Redis database number
REDIS_PASSWORD=            # Redis password (if required)

# Database
DB_PATH=tasks.db           # SQLite database path
DB_ECHO=False              # SQL query logging

# Worker
WORKER_NUM=2               # Number of worker processes
QUEUE_NAME=task_queue      # Queue name in Redis
TASK_TIMEOUT=300           # Task timeout in seconds
MAX_RETRIES=3              # Maximum retry attempts
BACKOFF_FACTOR=2.0         # Retry backoff multiplier
POLL_INTERVAL=1.0          # Queue polling interval (seconds)

# Logging
LOG_LEVEL=INFO             # Log level (DEBUG, INFO, WARNING, ERROR)
DEBUG=False                # Debug mode
```

## Error Handling & Retry Logic

Tasks failing during execution will automatically retry according to these rules:

1. **Initial Attempt** → Task fails → Move to RETRYING status
2. **Retry 1** → Wait (1s × backoff_factor^0) → Attempt again
3. **Retry 2** → Wait (1s × backoff_factor^1) → Attempt again
4. **Retry 3** → Wait (1s × backoff_factor^2) → Attempt again
5. **Max Retries Exceeded** → Mark as FAILED, store error message

Configuration:
- `MAX_RETRIES=3`: Number of retry attempts
- `BACKOFF_FACTOR=2.0`: Exponential backoff multiplier
- `TASK_TIMEOUT=300`: Timeout per task (added to schema for future use)

## Task Priority

Tasks support priority levels (0-100, higher = more important):

```bash
# High priority task (will be processed first)
curl -X POST http://localhost:8000/api/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "math_task",
    "payload": {"operation": "add", "operands": [1, 2]},
    "priority": 100
  }'

# Low priority task (will be processed later)
curl -X POST http://localhost:8000/api/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "sleep_task",
    "payload": {"duration": 5},
    "priority": 0
  }'
```

## Logging

The system provides comprehensive logging for debugging:

```
2024-01-15 10:30:00 - src.api.handlers - INFO - Task submitted: 550e8400... (type: sleep_task)
2024-01-15 10:30:00 - src.worker.executor - INFO - [worker-1] Processing task: 550e8400...
2024-01-15 10:30:00 - src.worker.executor - INFO - [worker-1] Executing sleep_task task: 550e8400...
2024-01-15 10:30:05 - src.worker.executor - INFO - [worker-1] Task completed successfully: 550e8400...
```

Adjust log level in `.env`:
```env
LOG_LEVEL=DEBUG    # Very verbose
LOG_LEVEL=INFO     # Standard (recommended)
LOG_LEVEL=WARNING  # Only warnings and errors
```

## Testing the System

### Example: Submit Multiple Tasks

```bash
#!/bin/bash

# Submit 5 tasks
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/task \
    -H "Content-Type: application/json" \
    -d "{
      \"task_type\": \"sleep_task\",
      \"payload\": {\"duration\": 3, \"message\": \"Task $i\"},
      \"priority\": $((RANDOM % 10))
    }"
  echo "Submitted task $i"
done

# Check statistics
sleep 2
curl http://localhost:8000/api/stats | jq .

# List all tasks
curl "http://localhost:8000/api/tasks?limit=100" | jq .
```

## Production Deployment

### Using Docker Compose

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Scale workers
docker-compose up -d --scale worker=5

# View logs
docker-compose logs -f worker

# Stop services
docker-compose down

# Cleanup volumes
docker-compose down -v
```

### Using Kubernetes (Future)

The Docker images can be deployed to Kubernetes or other orchestration platforms.

### Performance Considerations

1. **Scale Workers**: Increase `WORKER_NUM` for higher throughput
2. **Redis Memory**: Monitor Redis memory usage for large task queues
3. **Database**: Consider using PostgreSQL for production
4. **Monitoring**: Add Prometheus metrics endpoint for monitoring

## Troubleshooting

### Redis Connection Error
```
Failed to connect to Redis: Connection refused
```
**Solution**: Ensure Redis is running
```bash
redis-cli ping  # Should return PONG
```

### Database Lock Error
```
database is locked
```
**Solution**: Close other connections to the database or use a production database like PostgreSQL

### Tasks Not Processing
1. Check if workers are running: `python worker_main.py`
2. Check Redis queue: `redis-cli`
3. Verify logs: `LOG_LEVEL=DEBUG` in `.env`

### Port Already in Use
```
Address already in use
```
**Solution**: Change port in `.env` or kill the existing process
```bash
# Find process on port 8000
lsof -i :8000
kill -9 <PID>
```

## Architecture

```
┌─────────────┐
│   Client    │ HTTP requests
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  FastAPI Server │ POST /task
│  (main.py)      │ GET /task/{id}
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐  ┌────────┐
│ Redis  │  │SQLite  │
│ Queue  │  │ Store  │
└────┬───┘  └───┬────┘
     │          │
     ▼          │
┌──────────────┐│
│  Worker      ││
│  Process     ││
│  (worker_    │└─ Reads/Writes
│   main.py)   │   Task Status
└──────────────┘
```

## Future Enhancements

- [ ] Task scheduling/cron support
- [ ] WebSocket support for real-time updates
- [ ] Prometheus metrics integration
- [ ] PostgreSQL support for production
- [ ] Task result caching
- [ ] Dead letter queue for permanently failed tasks
- [ ] Task filtering by metadata
- [ ] Batch task submission
- [ ] Task cancellation support
- [ ] Rate limiting and throttling

## License

MIT

## Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guide
- All functions have docstrings
- Error handling is comprehensive
- Logging is included for debugging

## Support

For issues, questions, or suggestions, please open an issue in the repository.
